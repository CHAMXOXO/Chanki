// index.js - Core Legacy + Premium Support
const { AnkiClient } = require("./anki-client");
const joplin = require("./joplin-client");
const batchImporter = require("./anki-importer");
const { log, levelApplication, levelVerbose, levelDebug } = require("./log");
const { JoplinExporter, exporter, typeItem, registerPremiumDeckHandler, registerDynamicMapper } = require('./joplin-exporter');

let TwoWaySyncEngine = null;

function registerTwoWaySyncEngine(engine) {
  TwoWaySyncEngine = engine;
  log(levelVerbose, '💎 Two-way sync engine registered by premium plugin.');
}

/**
 * LEGACY ONE-WAY SYNC ORCHESTRATOR
 * - Joplin → Anki only
 * - Default deck assignment
 * - Basic Enhanced model only
 * - No state management
 * - Simple create/update logic
 */
const runLegacyOneWaySync = async (jClient, aClient, logLevels) => {
  log(levelApplication, "✅ Using legacy one-way exporter.");
  log(levelApplication, "📋 Fetching notes from Joplin...");
  
  const itemsToCreate = [];
  const itemsToUpdate = [];
  
  // Get all existing JTA notes from Anki for comparison
  const existingAnkiNotesMap = await aClient.getAllJtaNotesInfo();
  log(levelApplication, `📊 Found ${existingAnkiNotesMap.size} existing cards in Anki`);
  
  // Use the legacy exporter generator
  let itemCount = 0;
  for await (const result of exporter(jClient, null, log)) {
    if (result.type === typeItem) {
      const item = result.data;
      itemCount++;
      
      // LEGACY RULE: Always use "Default" deck
      item.deckName = "Default";
      
      // LEGACY RULE: Force Basic Enhanced model only
      if (item.additionalFields) {
        item.additionalFields.ankiModelName = "Joplin to Anki Basic Enhanced";
      }
      
      // Check if this item already exists in Anki
      const existingAnkiNote = existingAnkiNotesMap.get(item.jtaID);
      
      if (existingAnkiNote) {
        // Item exists - add to update queue
        // NOTE: In Legacy, we ignore content hash checks to ensure resources are always fixed.
        // This causes the "Update" count to equal total cards found.
        item.ankiNoteId = existingAnkiNote.ankiNoteId;
        itemsToUpdate.push(item);
        log(levelVerbose, `🔄 Queued for update: ${item.jtaID} - "${item.title}"`);
      } else {
        // Item doesn't exist - add to create queue
        itemsToCreate.push(item);
        log(levelVerbose, `➕ Queued for creation: ${item.jtaID} - "${item.title}"`);
      }
    }
  }
  
  log(levelApplication, `📦 Processed ${itemCount} JTA blocks from Joplin`);
  log(levelApplication, `   → ${itemsToCreate.length} new cards to create`);
  log(levelApplication, `   → ${itemsToUpdate.length} existing cards to update`);
  
  // Batch import to Anki
  if (itemsToCreate.length > 0 || itemsToUpdate.length > 0) {
    log(levelApplication, "🚀 Starting batch import to Anki...");
    
    const summary = await batchImporter(
      aClient,
      { create: itemsToCreate, update: itemsToUpdate },
      10, // batch size
      log,
      jClient,
      {} // no media conversion map in legacy mode
    );
    
    // Final summary - Perfectly Aligned using padEnd
    const p = (label, value) => {
        return `║  ${label.padEnd(13)} ${String(value).padEnd(6)} cards                    ║`;
    };
    const pRes = (label, value) => {
        return `║  ${label.padEnd(13)} ${String(value).padEnd(6)} uploaded                 ║`;
    };

    log(levelApplication, `
╔════════════════════════════════════════════════════════════╗
║                   LEGACY SYNC COMPLETED                    ║
╠════════════════════════════════════════════════════════════╣
${p('📝 Created:', ssummary.created)}
${p('🔄 Updated:', summary.updated)}
${p('⏭️  Skipped:', ssummary.skipped)}
${p('❌ Failed:', summary.failed)}
${pRes('📎 Resources:', summary.resourcesUploaded)}
╚════════════════════════════════════════════════════════════╝
    `);
    
    if (summary.failed > 0) {
      log(levelApplication, "⚠️  Some cards failed to sync. Check logs above for details.");
    }
  } else {
    log(levelApplication, "✅ No changes detected. All cards are up to date!");
  }
};

/**
 * MAIN RUN FUNCTION
 * Routes to either Premium Two-Way or Legacy One-Way sync
 */
const run = async (joplinURL, joplinToken, exportFromDate, ankiURL, logLevels) => {
  log(levelApplication, "🚀 Initializing Joplin to Anki Sync");
  
  const jClient = joplin.newClient(joplinURL, joplinToken, log);
  const aClient = new AnkiClient(ankiURL, log);
  
  try {
    // Health checks
    await Promise.all([jClient.health(), aClient.health()]);
    await aClient.setup();
    
    if (TwoWaySyncEngine) {
      // ═══════════════════════════════════════════════════════
      // PREMIUM MODE: Two-Way Bidirectional Sync
      // ═══════════════════════════════════════════════════════
      log(levelApplication, "💎 Running with Premium Two-Way Sync Engine...");
      const exporterInstance = new JoplinExporter(jClient, log);
      const engine = new TwoWaySyncEngine(
        jClient, 
        aClient, 
        log, 
        batchImporter, 
        exporterInstance, 
        logLevels
      );
      await engine.run();
    } else {
      // ═══════════════════════════════════════════════════════
      // LEGACY MODE: One-Way Sync (Joplin → Anki)
      // ═══════════════════════════════════════════════════════
      log(levelApplication, "⚠️ Running in legacy mode.");
      await runLegacyOneWaySync(jClient, aClient, logLevels);
    }
    
  } catch (error) {
    throw new Error(`Sync engine failed: ${error.message}`);
  }
};

module.exports = {
  run,
  registerTwoWaySyncEngine,
  registerPremiumDeckHandler,
  registerDynamicMapper,
};

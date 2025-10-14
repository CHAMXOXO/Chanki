// Joplin to Anki - Main Orchestrator - FINAL DEBUG VERSION
const marked = require("marked");
const { exporter, typeItem, typeResource, typeError } = require("./joplin-exporter");
const batchImporter = require("./anki-importer");
const joplin = require("./joplin-client");
const anki = require("./anki-client");
const { log, setLevel, levelApplication, levelVerbose } = require("./log");

// ============================================================================
// PREMIUM ENGINE REGISTRATION
// ============================================================================
let TwoWaySyncEngine = null;

function registerTwoWaySyncEngine(engine) {
  TwoWaySyncEngine = engine;
  console.log('💎 Premium Two-Way Sync Engine registered and active.');
}
// ============================================================================

function stripDetails(html) {
  if (!html) return html;
  return html.replace(/<details[^>]*>/gi, "").replace(/<\/details>/gi, "").replace(/<summary[^>]*>.*?<\/summary>/gi, "");
}

/**
 * The main run function, which now acts as a dispatcher.
 */
const run = async (logLevel, joplinURL, joplinToken, exportFromDate, ankiURL, options = {}) => {
  setLevel(logLevel);

  // --- START OF PROOF-OF-LIFE LOG ---
  console.log("--- Executing LATEST version of joplin-to-anki.js ---");
  // --- END OF PROOF-OF-LIFE LOG ---

  log(levelApplication, "🚀 Initializing Joplin to Anki Sync");

  const jClient = joplin.newClient(joplinURL, joplinToken, log);
  const aClient = new anki(ankiURL, log);

  try {
    await Promise.all([jClient.health(), aClient.health()]);
    await aClient.setup();
  } catch (error) {
    throw new Error(`Health checks or setup failed: ${error.message}`);
  }

  // --- DISPATCHER LOGIC ---
  if (TwoWaySyncEngine) {
    // PREMIUM PATH: Use the new two-way sync engine
    log(levelApplication, "Running with Premium Two-Way Sync Engine...");

    // --- START OF DEBUG LOG ---
    console.log(`[DEBUG] Type of batchImporter is: ${typeof batchImporter}`);
    if (typeof batchImporter !== 'function') {
        console.error("[FATAL DEBUG] batchImporter is NOT a function! The require statement failed.");
    console.log(`[DEBUG] Type of batchImporter is: ${typeof batchImporter}`);
    
    // --- ADD THIS NEW DIAGNOSTIC LINE ---
    console.log('[DEBUG] Inspecting batchImporter object:', JSON.stringify(batchImporter, null, 2));
    
    if (typeof batchImporter !== 'function') {
        console.error("[FATAL DEBUG] batchImporter is NOT a function! The require statement failed.");
    }
    }
    // --- END OF DEBUG LOG ---

    const engine = new TwoWaySyncEngine(jClient, aClient, log, batchImporter);
    await engine.run();

  } else {
    // FREE / LEGACY PATH: Run the original one-way sync logic
    log(levelApplication, "Running with Free One-Way Sync Logic...");
    await runLegacyOneWaySync(jClient, aClient, exportFromDate, options);
  }

  log(levelApplication, "✨ SYNC COMPLETED");
};


/**
 * The original one-way sync logic, now encapsulated in its own function.
 */
async function runLegacyOneWaySync(jClient, aClient, exportFromDate, options) {
    // ... (This function does not need any changes)
    const { batchSize = 10, markdownProcessing = true } = options;
    const sync = {
        startTime: new Date(),
        summary: { created: 0, updated: 0, skipped: 0, failed: 0, errors: [] },
    };
    try {
        log(levelApplication, "📚 Starting export from Joplin...");
        const gen = exporter(jClient, exportFromDate, log);
        const allItems = [];
        for await (const value of gen) {
            if (value.type === typeItem) {
                allItems.push(value.data);
            }
        }
        log(levelApplication, `📊 Collected ${allItems.length} items for batch processing`);
        if (allItems.length > 0) {
            const processedItems = allItems.map(item => {
                if (item.additionalFields && item.additionalFields.customNoteType) {
                    return { ...item, additionalFields: { ...item.additionalFields, deckName: item.deckName } };
                } else {
                    return {
                        ...item,
                        question: stripDetails(markdownProcessing ? marked(item.question || '') : item.question),
                        answer: stripDetails(markdownProcessing ? marked(item.answer || '') : item.answer),
                        additionalFields: { ...item.additionalFields, deckName: item.deckName }
                    };
                }
            });
            const results = await batchImporter(aClient, processedItems, batchSize, log);
            sync.summary.created += results.created;
            sync.summary.updated += results.updated;
            sync.summary.skipped += results.skipped;
            sync.summary.failed += results.failed;
        }
        const duration = (new Date() - sync.startTime) / 1000;
        log(levelApplication, `
🎉 One-Way Sync Completed Successfully!
   • Duration: ${duration.toFixed(1)}s
   • Created: ${sync.summary.created}, Updated: ${sync.summary.updated}, Skipped: ${sync.summary.skipped}, Failed: ${sync.summary.failed}
        `);
    } catch (error) {
        log(levelApplication, `❌ One-Way Sync failed: ${error.message}`);
        throw error;
    }
}


module.exports = {
  run,
  registerTwoWaySyncEngine,
};

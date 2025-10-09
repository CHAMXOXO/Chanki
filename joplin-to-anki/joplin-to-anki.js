const marked = require("marked");
const {
  exporter,
  typeItem,
  typeResource,
  typeError,
} = require("./joplin-exporter");
const {
  validatedImporter,
  batchImporter,
  cleanupDuplicates
} = require("./anki-importer");
const joplin = require("./joplin-client");
const anki = require("./anki-client");
const {
  log, // <--- CHANGED: Import 'log' directly
  setLevel, // <--- CHANGED: Import 'setLevel'
  levelApplication,
  levelVerbose,
  levelDebug,
} = require("./log");

// --- Helper: Strip <details> wrappers (leave inner content only) ---
function stripDetails(html) {
  if (!html) return html;
  return html
    .replace(/<details[^>]*>/gi, "")
    .replace(/<\/details>/gi, "")
    .replace(/<summary[^>]*>.*?<\/summary>/gi, ""); // remove summary text
}

const run = async (
  logLevel,
  joplinURL,
  joplinToken,
  exportFromDate,
  ankiURL,
  options = {}
) => {
  // <--- REMOVED: const log = newLogger(logLevel);
  // <--- ADDED: Call setLevel on the imported log module to configure it globally
  setLevel(logLevel); // <--- CHANGED: Set the global log level using setLevel

  const {
    batchSize = 10,
    cleanupDuplicates: shouldCleanup = false,
    retryAttempts = 3,
    markdownProcessing = true,
    validateData = true,
    useBatchProcessing = true
  } = options;

  // The 'log' function is now directly available and configured via setLevel
  // Just use 'log(level, msg)' directly.
  log(levelApplication, "🚀 Starting Enhanced Joplin to Anki Sync"); // <--- Example usage
  log(levelVerbose, `Configuration:
    - Batch size: ${batchSize}
    - Cleanup duplicates: ${shouldCleanup}
    - Retry attempts: ${retryAttempts}
    - Markdown processing: ${markdownProcessing}
    - Data validation: ${validateData}
    - Batch processing: ${useBatchProcessing}`);

  const jClient = joplin.newClient(joplinURL, joplinToken, log);
  const aClient = new anki(ankiURL, log);

  // Health checks (retrying)
  let healthCheckAttempts = 0;
  const maxHealthCheckAttempts = 3;
  while (healthCheckAttempts < maxHealthCheckAttempts) {
    try {
      log(levelVerbose, "🔍 Performing health checks...");
      await Promise.all([jClient.health(), aClient.health()]);
      log(levelVerbose, "✅ Health checks passed");
      break;
    } catch (error) {
      healthCheckAttempts++;
      if (healthCheckAttempts >= maxHealthCheckAttempts) {
        throw new Error(`Health checks failed: ${error.message}`);
      }
      log(levelVerbose, `⚠️ Health check attempt ${healthCheckAttempts} failed, retrying...`);
      await new Promise(resolve => setTimeout(resolve, 2000 * healthCheckAttempts));
    }
  }

  try {
    log(levelVerbose, "🔧 Setting up Anki models and decks...");
    await aClient.setup();
    log(levelVerbose, "✅ Anki setup completed");
  } catch (error) {
    const errorMsg = `Problem with Anki setup: ${error.message}`;
    log(levelApplication, `❌ ${errorMsg}`);
    throw new Error(errorMsg);
  }

  if (shouldCleanup) {
    try {
      log(levelVerbose, "🧹 Running duplicate cleanup...");
      const cleanedCount = await cleanupDuplicates(aClient, log);
      log(levelApplication, `🧹 Cleaned up ${cleanedCount} duplicate notes`);
    } catch (error) {
      log(levelApplication, `⚠️ Duplicate cleanup failed: ${error.message}`);
    }
  }

  const sync = {
    startTime: new Date(),
    summary: {
      items: 0,
      itemsSuccess: 0,
      itemsUpdated: 0,
      itemsCreated: 0,
      resources: 0,
      resourcesSuccess: 0,
      errorCount: 0,
      decksCreated: new Set(),
    },
    errors: [],
    processedItems: [],
    processedResources: []
  };

  try {
    log(levelApplication, "📚 Starting export from Joplin...");
    // Pass the 'log' function directly to the exporter
    const gen = exporter(jClient, exportFromDate, log); // <--- CHANGED: Pass 'log' directly

    if (useBatchProcessing) {
      const allItems = [];
      const allResources = [];

      for await (const value of gen) {
        switch (value.type) {
          case typeItem:
            sync.summary.items++;
            allItems.push(value.data);
            break;
          case typeResource:
            sync.summary.resources++;
            allResources.push(value.data);
            break;
          case typeError:
            sync.summary.errorCount++;
            sync.errors.push(value.data);
            log(levelApplication, `❌ Export error: ${value.data}`);
            break;
        }
      }

      log(levelApplication, `📊 Collected ${allItems.length} items and ${allResources.length} resources for batch processing`);

      if (allResources.length > 0) {
        await processResourcesBatch(aClient, allResources, sync, log, batchSize);
      }

      if (allItems.length > 0) {
        await processItemsBatch(
          aClient,
          allItems,
          sync,
          log,
          batchSize,
          { markdownProcessing, validateData }
        );
      }

    } else {
      for await (const value of gen) {
        await processExportValue(value, aClient, sync, log, { markdownProcessing, validateData });
      }
    }

    const duration = (new Date() - sync.startTime) / 1000;
    log(levelApplication, `
🎉 Enhanced Sync Completed Successfully!

📊 Summary:
   • Duration: ${duration.toFixed(1)}s
   • Notes processed: ${sync.summary.items}
   • Cards created: ${sync.summary.itemsCreated}
   • Cards updated: ${sync.summary.itemsUpdated}
   • Total successful: ${sync.summary.itemsSuccess}
   • Failed: ${sync.summary.items - sync.summary.itemsSuccess}
   • Resources processed: ${sync.summary.resources}
   • Resources successful: ${sync.summary.resourcesSuccess}
   • Resource failures: ${sync.summary.resources - sync.summary.resourcesSuccess}
   • Decks involved: ${sync.summary.decksCreated.size}
   • Total errors: ${sync.summary.errorCount}
    `);

  } catch (error) {
    const duration = (new Date() - sync.startTime) / 1000;
    log(levelApplication, `❌ Sync failed after ${duration.toFixed(1)}s: ${error.message}`);
    throw error;
  }

  log(levelApplication, "✨ SYNC COMPLETED");
  return sync.summary;
};

// --- Updated processing functions to strip <details> before Anki ---
const processExportValue = async (value, aClient, sync, log, options = {}) => {
  const { markdownProcessing = true, validateData = true } = options;
  switch (value.type) {
    case typeItem:
      sync.summary.items++;
      try {
        let question = markdownProcessing ? marked(value.data.question) : value.data.question;
        let answer = markdownProcessing ? marked(value.data.answer) : value.data.answer;

        // Strip dropdowns for Anki
        question = stripDetails(question);
        answer = stripDetails(answer);

        const importerFunction = validateData ? validatedImporter : batchImporter;
        const result = await importerFunction(
          aClient,
          question,
          answer,
          value.data.jtaID,
          value.data.title,
          value.data.notebook,
          value.data.tags,
          value.data.folders,
          value.data.additionalFields,
          log
        );

        sync.summary.itemsSuccess++;
        if (result.action === "created") sync.summary.itemsCreated++;
        else if (result.action === "updated") sync.summary.itemsUpdated++;
        sync.summary.decksCreated.add(result.deck);
        sync.processedItems.push(result);

      } catch (error) {
        sync.summary.errorCount++;
        sync.errors.push(`Item import failed: ${error.message}`);
        log(levelApplication, `❌ Problem importing note: ${error.message}`);
      }
      break;

    case typeResource:
      sync.summary.resources++;
      try {
        await aClient.storeMedia(value.data.fileName, value.data.data);
        sync.summary.resourcesSuccess++;
        sync.processedResources.push(value.data.fileName);
      } catch (error) {
        sync.summary.errorCount++;
        sync.errors.push(`Resource import failed: ${error.message}`);
        log(levelApplication, `❌ Resource failed: ${error.message}`);
      }
      break;

    case typeError:
      sync.summary.errorCount++;
      sync.errors.push(value.data);
      log(levelApplication, `❌ Export error: ${value.data}`);
      break;
  }
};

const processItemsBatch = async (aClient, items, sync, log, batchSize, options = {}) => {
  const { markdownProcessing = true } = options;
  const processedItems = items.map(item => ({
    ...item,
    question: stripDetails(markdownProcessing ? marked(item.question) : item.question),
    answer: stripDetails(markdownProcessing ? marked(item.answer) : item.answer),
  }));

  try {
    const results = await batchImporter(aClient, processedItems, batchSize, log);
    sync.summary.itemsSuccess += results.created + results.updated;
    sync.summary.itemsCreated += results.created;
    sync.summary.itemsUpdated += results.updated;
    sync.summary.errorCount += results.failed;
  } catch (error) {
    log(levelApplication, `❌ Batch processing failed: ${error.message}`);
    sync.summary.errorCount += items.length;
  }
};

const processResourcesBatch = async (aClient, resources, sync, log, batchSize) => {
  for (let i = 0; i < resources.length; i += batchSize) {
    const batch = resources.slice(i, i + batchSize);
    const batchPromises = batch.map(async (resource, index) => {
      try {
        // Adding a small delay to avoid overwhelming AnkiConnect, especially for many resources
        await new Promise(resolve => setTimeout(resolve, index * 100)); // Delay per resource in batch
        await aClient.storeMedia(resource.fileName, resource.data);
        sync.summary.resourcesSuccess++;
        sync.processedResources.push(resource.fileName);
      } catch (error) {
        sync.summary.errorCount++;
        sync.errors.push(`Resource ${resource.fileName}: ${error.message}`);
      }
    });
    await Promise.allSettled(batchPromises);
    // Add a larger delay between batches if there are more batches to process
    if (i + batchSize < resources.length) {
      await new Promise(resolve => setTimeout(resolve, 500)); // Delay between batches
    }
  }
};

module.exports = { run };

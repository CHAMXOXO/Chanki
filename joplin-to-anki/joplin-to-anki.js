// joplin-to-anki.js (FINAL INTELLIGENT UPDATE VERSION)
const marked = require("marked");
const { exporter, typeItem, typeResource, typeError } = require("./joplin-exporter");
const { validatedImporter, batchImporter, cleanupDuplicates } = require("./anki-importer");
const joplin = require("./joplin-client");
const anki = require("./anki-client");
const { log, setLevel, levelApplication, levelVerbose } = require("./log");

function stripDetails(html) {
  if (!html) return html;
  return html
    .replace(/<details[^>]*>/gi, "")
    .replace(/<\/details>/gi, "")
    .replace(/<summary[^>]*>.*?<\/summary>/gi, "");
}

const run = async (
  logLevel,
  joplinURL,
  joplinToken,
  exportFromDate,
  ankiURL,
  options = {}
) => {
  setLevel(logLevel);

  const {
    batchSize = 10,
    cleanupDuplicates: shouldCleanup = false,
    markdownProcessing = true,
    validateData = true,
    useBatchProcessing = true
  } = options;

  log(levelApplication, "🚀 Starting Enhanced Joplin to Anki Sync");

  const jClient = joplin.newClient(joplinURL, joplinToken, log);
  const aClient = new anki(ankiURL, log);

  try {
    await Promise.all([jClient.health(), aClient.health()]);
    await aClient.setup();
  } catch (error) {
    throw new Error(`Health checks or setup failed: ${error.message}`);
  }

  if (shouldCleanup) {
    try {
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
      itemsUpdated: 0,
      itemsCreated: 0,
      itemsSkipped: 0, // ADDED
      resources: 0,
      resourcesSuccess: 0,
      errorCount: 0,
      decksCreated: new Set(),
    },
    errors: [],
  };

  try {
    log(levelApplication, "📚 Starting export from Joplin...");
    const gen = exporter(jClient, exportFromDate, log);

    if (useBatchProcessing) {
      const allItems = [];
      for await (const value of gen) {
        switch (value.type) {
          case typeItem:
            sync.summary.items++;
            allItems.push(value.data);
            break;
          case typeResource:
            sync.summary.resources++;
            try {
                await aClient.storeMedia(value.data.fileName, value.data.data);
                sync.summary.resourcesSuccess++;
            } catch(e) { /* handle resource error */ }
            break;
          case typeError:
            sync.summary.errorCount++;
            sync.errors.push(value.data);
            break;
        }
      }

      log(levelApplication, `📊 Collected ${allItems.length} items for batch processing`);

      if (allItems.length > 0) {
        const processedItems = allItems.map(item => ({
            ...item,
            question: stripDetails(markdownProcessing ? marked(item.question) : item.question),
            answer: stripDetails(markdownProcessing ? marked(item.answer) : item.answer),
        }));

        const results = await batchImporter(aClient, processedItems, batchSize, log);
        sync.summary.itemsCreated += results.created;
        sync.summary.itemsUpdated += results.updated;
        sync.summary.itemsSkipped += results.skipped;
        sync.summary.errorCount += results.failed;
      }
    } else {
        // Sequential processing logic can be added here if needed, but batch is superior.
    }

    const duration = (new Date() - sync.startTime) / 1000;
    log(levelApplication, `
🎉 Enhanced Sync Completed Successfully!

📊 Summary:
   • Duration: ${duration.toFixed(1)}s
   • Notes processed: ${sync.summary.items}
   • Cards created: ${sync.summary.itemsCreated}
   • Cards updated: ${sync.summary.itemsUpdated}
   • Skipped (unchanged): ${sync.summary.itemsSkipped}
   • Total successful: ${sync.summary.itemsCreated + sync.summary.itemsUpdated}
   • Failed: ${sync.summary.items - (sync.summary.itemsCreated + sync.summary.itemsUpdated + sync.summary.itemsSkipped)}
   • Resources processed: ${sync.summary.resources}
   • Resources successful: ${sync.summary.resourcesSuccess}
   • Resource failures: ${sync.summary.resources - sync.summary.resourcesSuccess}
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

module.exports = { run };

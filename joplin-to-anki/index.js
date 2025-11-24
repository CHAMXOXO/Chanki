// index.js

const { AnkiClient } = require("./anki-client");
const joplin = require("./joplin-client");
const batchImporter = require("./anki-importer");
const { log, levelApplication, levelVerbose, levelDebug } = require("./log");
const { JoplinExporter, registerPremiumDeckHandler, registerDynamicMapper } = require('./joplin-exporter');

let TwoWaySyncEngine = null;
function registerTwoWaySyncEngine(engine) {
  TwoWaySyncEngine = engine;
  log(levelVerbose, '   → Two-way sync engine registered by premium plugin.');
}

const run = async (joplinURL, joplinToken, exportFromDate, ankiURL, logLevels) => {
  log(levelApplication, "🚀 Initializing Joplin to Anki Sync");

  const jClient = joplin.newClient(joplinURL, joplinToken, log);
  const aClient = new AnkiClient(ankiURL, log);

  try {
    await Promise.all([jClient.health(), aClient.health()]);
    await aClient.setup();

    if (TwoWaySyncEngine) {
      log(levelApplication, "Running with Premium Two-Way Sync Engine...");
      const exporter = new JoplinExporter(jClient, log);
      const engine = new TwoWaySyncEngine(jClient, aClient, log, batchImporter, exporter, logLevels);
      await engine.run();
    } else {
      log(levelApplication, "⚠️ Running in legacy mode.");
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

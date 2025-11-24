const Configstore = require("configstore");
const packageJson = require("./package.json");

const defaultConfigs = {
  joplinURL: "http://localhost:41184",
  ankiURL: "http://localhost:8765",
  exportFromDate: null, 
  joplinToken: null,
};

const config = new Configstore(packageJson.name);

/**
 * Loads and validates the application configuration.
 * Priority Order:
 * 1. Environment Variables (e.g., JTA_JOPLIN_TOKEN)
 * 2. Stored values in the config file (e.g., from `chanki config set`)
 * 3. Default values defined above.
 */
function loadConfig() {
  const storedConfig = config.all;

  let finalConfig = { ...defaultConfigs, ...storedConfig };

  if (process.env.JTA_JOPLIN_URL) {
    finalConfig.joplinURL = process.env.JTA_JOPLIN_URL;
  }
  if (process.env.JTA_JOPLIN_TOKEN) {
    finalConfig.joplinToken = process.env.JTA_JOPLIN_TOKEN;
  }
  if (process.env.JTA_ANKI_URL) {
    finalConfig.ankiURL = process.env.JTA_ANKI_URL;
  }

  // Handle dynamic default for exportFromDate if it's not set
  if (!finalConfig.exportFromDate) {
    const defaultDate = new Date();
    defaultDate.setDate(defaultDate.getDate() - 1);
    finalConfig.exportFromDate = defaultDate.toISOString();
  }
  
  if (!finalConfig.joplinToken) {
  }

  return finalConfig;
}

const validatedConfig = loadConfig();

module.exports = {
  config: validatedConfig,
  
  path: config.path,
  set: (key, value) => {
    config.set(key, value);
  },
  reset: () => {
    config.clear();
  }
};

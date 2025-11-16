// config.js - ENHANCED & CENTRALIZED VERSION
const Configstore = require("configstore");
const packageJson = require("./package.json");

// 1. Define default values in one place.
const defaultConfigs = {
  joplinURL: "http://localhost:41184",
  ankiURL: "http://localhost:8765",
  exportFromDate: null, // We will set this dynamically if needed
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

  // Start with defaults and merge stored values
  let finalConfig = { ...defaultConfigs, ...storedConfig };

  // Allow environment variables to override everything
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
  
  // 2. Perform critical validation.
  // The 'run' command will need the token.
  if (!finalConfig.joplinToken) {
    // We don't throw an error here, as commands like 'status' or 'config' should still work.
    // The 'run' command itself should perform the final check.
    // This allows the app to function partially without a full setup.
  }

  return finalConfig;
}

// 3. Export a single, ready-to-use config object for the application.
const validatedConfig = loadConfig();

module.exports = {
  // The main export is the validated config object
  config: validatedConfig,
  
  // Expose these methods for the `chanki config` commands
  path: config.path,
  set: (key, value) => {
    config.set(key, value);
  },
  reset: () => {
    config.clear();
  }
};

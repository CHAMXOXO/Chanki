#!/usr/bin/env node
const { program } = require("commander");
const jta = require("./index");
// --- UPDATED: Import the new config module's exports ---
const { config, path: configPath, set: configSet, reset: configReset } = require("./config");
const { log, setLevel, levelApplication, levelVerbose, levelDebug } = require("./log");
const fs = require("fs");
const path = require("path");
const os = require("os");

const CHANKI_VERSION = "2.0.2"; // Bumped version for new features
const CHANKI_BANNER = `
╔════════════════════════════════════════════════════════════╗
║                       CHANKI v2.0.2                        ║
║         Advanced Joplin ↔ Anki Synchronization             ║
║                                                            ║
║          Based on joplin-to-anki by Bart (MIT)             ║
║           Enhanced & Extended by Cindy © 2025              ║
╚════════════════════════════════════════════════════════════╝
`;

function detectPremiumLicense() {
  const licenseFile = path.join(os.homedir(), '.jta-premium-license');
  const envKey = process.env.JTA_PREMIUM_KEY;
  if (envKey) return { active: true, key: envKey, source: 'environment variable' };
  if (fs.existsSync(licenseFile)) {
    try {
      const key = fs.readFileSync(licenseFile, 'utf8').trim();
      return { active: true, key: key, source: 'license file' };
    } catch (e) { return { active: false, error: 'Could not read license file' }; }
  }
  return { active: false };
}

async function loadPremiumPlugin() {
  const license = detectPremiumLicense();
  if (!license.active) return { loaded: false, license: false };
  try {
    // --- NOTE: Hardcoded path retained as requested for local development ---
    const localPath = '/home/cindy/Chanki-Premium/joplin-to-anki-premium';
    const premiumModule = fs.existsSync(localPath) ? require(localPath) : require('chanki-premium');

    if (premiumModule && premiumModule.initialize) {
      const logLevels = { levelApplication, levelVerbose, levelDebug };
      const success = premiumModule.initialize(jta, log, logLevels);
      return { loaded: success, license: true };
    }
    throw new Error("Premium module is invalid.");
  } catch (error) {
    log(levelApplication, `❌ Failed to load premium plugin`);
    log(levelApplication, `   Error: ${error.message}`);
    return { loaded: false, license: true, error: error };
  }
}

program.name('chanki').version(CHANKI_VERSION).description('...');
program.option("-t, --joplintoken <token>", "Override the stored Joplin token").option("-d, --date <ISO Time String>", "Override the last sync date").option("-j, --joplinurl <URL>", "Override the stored Joplin URL").option("-a, --ankiurl <URL>", "Override the stored Anki URL").option('-v, --verbose', "Enable verbose logging").option('-vv, --debug', "Enable debug logging").option("--no-banner", "Hide the startup banner");
program.hook('preAction', (thisCommand) => {
  const opts = thisCommand.opts();
  if (opts.debug) setLevel(levelDebug);
  else if (opts.verbose) setLevel(levelVerbose);
  else setLevel(levelApplication);
});

program.command("status").description("Show current configuration and license status").action(async () => {
    if (!program.opts().noBanner) {
        console.log(CHANKI_BANNER);
    }
    const premium = await loadPremiumPlugin();
    
    // --- UPDATED: Use the imported 'config' object directly ---
    // No need for getAll() or fallback checks like `|| '(not set)'` for most values
    console.log('📊 System Status\n');
    console.log(`Version: ${CHANKI_VERSION}`);
    console.log(`Edition: ${premium.loaded ? '💎 Premium' : '📦 Legacy'}`);
    if (premium.license && !premium.loaded && premium.error) console.log(`Load Error: ${String(premium.error.message)}`);
    
    console.log('\n⚙️  Configuration\n');
    console.log(`Joplin URL: ${config.joplinURL}`);
    console.log(`Joplin Token: ${config.joplinToken ? '***' + config.joplinToken.slice(-4) : '(not set)'}`);
    console.log(`Anki URL: ${config.ankiURL}`);
    console.log(`Last Sync: ${config.exportFromDate || '(never)'}`);
    
    console.log('\n📂 Paths\n');
    console.log(`Config File: ${configPath}`);
    console.log(`License File: ${path.join(os.homedir(), '.jta-premium-license')}`);
    console.log(`Installation: ${__dirname}`);
});

program.command("run")
    .description("Run the synchronization process")
    .action(async () => {
        if (!program.opts().noBanner) {
            console.log(CHANKI_BANNER);
        }
        const options = program.opts();

        const finalConfig = { ...config }; 
        if (options.joplintoken) finalConfig.joplinToken = options.joplintoken;
        if (options.joplinurl) finalConfig.joplinURL = options.joplinurl;
        if (options.ankiurl) finalConfig.ankiURL = options.ankiurl;
        if (options.date) finalConfig.exportFromDate = options.date;

        if (!finalConfig.joplinToken) {
            log(levelApplication, '❌ Joplin token is not set. Please run "chanki config set joplinToken YOUR_TOKEN"');
            process.exit(1);
        }

        try {
            await loadPremiumPlugin();
            
            const logLevels = { levelApplication, levelVerbose, levelDebug };
            
            await jta.run(
                finalConfig.joplinURL,
                finalConfig.joplinToken,
                finalConfig.exportFromDate,
                finalConfig.ankiURL,
                logLevels
            );
            
            process.exit(0);
            
        } catch (error) {
            log(levelApplication, `❌ A critical error occurred during the sync process:`);
            log(levelApplication, error.message);
            process.exit(1); // This is correct
        }
    });

// --- NEW: Fully implemented `config` command ---
const configCommand = program.command("config").description("Get or set configuration values");

configCommand.command("set <key> <value>").description("Set a configuration key").action((key, value) => {
    configSet(key, value);
    log(levelApplication, `✅ Configuration updated: "${key}" has been set.`);
});

configCommand.command("get <key>").description("Get a configuration key's value").action((key) => {
    // The imported 'config' object already has all values
    const value = config[key];
    if (value !== undefined) {
        console.log(value);
    } else {
        log(levelApplication, `⚠️ Key "${key}" not found in configuration.`);
    }
});

configCommand.command("reset").description("Reset all stored configurations to default").action(() => {
    configReset();
    log(levelApplication, '✅ Configuration has been reset.');
});

// --- NEW: Fully implemented `license` command ---
program.command("license").description("Display premium license details").action(() => {
    log(levelApplication, "Checking for premium license...");
    const license = detectPremiumLicense();
    if (license.active) {
        log(levelApplication, `💎 License Found!`);
        console.log(`   Key: ***${license.key.slice(-8)}`);
        console.log(`   Source: ${license.source}`);
    } else {
        log(levelApplication, `No active premium license found.`);
        if(license.error) log(levelApplication, `   Error: ${license.error}`);
    }
});

module.exports = (args) => {
  program.parse(args);
};

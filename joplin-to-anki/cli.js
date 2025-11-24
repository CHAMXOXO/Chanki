#!/usr/bin/env node
const { program } = require("commander");
const jta = require("./index");
const { config, path: configPath, set: configSet, reset: configReset } = require("./config");
const { log, setLevel, levelApplication, levelVerbose, levelDebug } = require("./log");
const fs = require("fs");
const path = require("path");
const os = require("os");

const CHANKI_VERSION = "2.0.2";
const CHANKI_BANNER = `
╔════════════════════════════════════════════════════════════╗
║                       CHANKI v2.0.2                        ║
║         Advanced Joplin ↔ Anki Synchronization             ║
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
    } catch (e) { 
        return { active: false, error: 'Could not read license file' }; 
    }
  }
  return { active: false };
}

async function loadPremiumPlugin() {
  const license = detectPremiumLicense();
  
  // If no license exists, stop trying to load (Prevents "Module not found" error in Legacy mode)
  if (!license.active) return { loaded: false, license: false };
  
  try {
    // 1. Check your specific Developer Path
    const devPath = '/home/cindy/Chanki-Premium/joplin-to-anki-premium';
    
    // 2. Check Sibling Directory (Standard Dev structure)
    const siblingPath = path.join(__dirname, '../joplin-to-anki-premium');

    let premiumModule = null;

    if (fs.existsSync(devPath)) {
        premiumModule = require(devPath);
    } else if (fs.existsSync(siblingPath)) {
        premiumModule = require(siblingPath);
    } else {
        // 3. Fallback to Production (NPM package)
        try {
            premiumModule = require('chanki-premium');
        } catch (e) {
            // If strictly legacy, this is expected, but we only error if a license WAS found
            throw new Error("Premium license detected, but premium module files are missing.");
        }
    }

    if (premiumModule && premiumModule.initialize) {
      const logLevels = { levelApplication, levelVerbose, levelDebug };
      const success = await premiumModule.initialize(jta, log, logLevels);
      return { loaded: success, license: true };
    }
    
    return { loaded: false, license: true };

  } catch (error) {
    return { loaded: false, license: true, error: error };
  }
}

program.name('chanki').version(CHANKI_VERSION).description('Advanced Joplin to Anki Sync Tool');

program.option("-t, --joplintoken <token>", "Override the stored Joplin token")
       .option("-d, --date <ISO Time String>", "Override the last sync date")
       .option("-j, --joplinurl <URL>", "Override the stored Joplin URL")
       .option("-a, --ankiurl <URL>", "Override the stored Anki URL")
       .option('-v, --verbose', "Enable verbose logging")
       .option('-vv, --debug', "Enable debug logging")
       .option("--no-banner", "Hide the startup banner");

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
    
    console.log('📊 System Status\n');
    console.log(`Version: ${CHANKI_VERSION}`);
    
    if (premium.loaded) {
        console.log(`Edition: 💎 Premium (Active)`);
    } else {
        console.log(`Edition: 📦 Legacy (Free)`);
    }

    if (premium.license && !premium.loaded && premium.error) {
        console.log(`⚠️ Warning: License found but module failed to load:`);
        console.log(`   ${String(premium.error.message)}`);
    }
    
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
            const premiumStatus = await loadPremiumPlugin();
            if(premiumStatus.license && !premiumStatus.loaded) {
                 log(levelApplication, `⚠️ Running in Legacy Mode (Premium module not found)`);
            }
            
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
            process.exit(1); 
        }
    });

const configCommand = program.command("config").description("Get or set configuration values");

configCommand.command("set <key> <value>").description("Set a configuration key").action((key, value) => {
    configSet(key, value);
    log(levelApplication, `✅ Configuration updated: "${key}" has been set.`);
});

configCommand.command("get <key>").description("Get a configuration key's value").action((key) => {
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

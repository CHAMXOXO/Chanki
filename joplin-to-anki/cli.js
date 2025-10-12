const { program } = require("commander");
const jta = require("./joplin-to-anki");
const configStore = require("./config");
const { levelApplication, levelVerbose, levelDebug } = require("./log");

program.version("0.0.0");

program
  .option(
    "-t, --joplintoken <token>",
    "token for Joplin Web Clipper API",
    configStore.get("joplinToken")
  )
  .option(
    "-d, --date <ISO Time String>",
    "joplin notes updated after this date will be exported. Defaults to configured value or now - 1 day",
    configStore.getWithFallback("exportFromDate")
  )
  .option(
    "-j, --joplinurl <URL>",
    "URL for Joplin Web Clipper API",
    configStore.getWithFallback("joplinURL")
  )
  .option(
    "-a, --ankiurl <URL>",
    "URL for Anki Connect API",
    configStore.getWithFallback("ankiURL")
  )
  .option(
    `-l, --loglevel <one of ${levelApplication}, ${levelVerbose}, ${levelDebug}>`,
    "Enable verbose logs",
    levelApplication
  );
  
  
  // ============================================================================
  // PREMIUM PLUGIN LOADER
  // ============================================================================
  async function loadPremiumPlugin() {
    try {
      // Try multiple locations for the premium plugin
      let premium;
      try {
        // Try local path first
        premium = require('/home/cindy/Chanki-Premium/joplin-to-anki-premium');
      } catch (e) {
        // Fall back to module name
        premium = require('joplin-to-anki-premium');
      }
      
      if (premium) {
        console.log('🔍 Found premium plugin');
        return true;
      }
      return false;
    } catch (error) {
      console.log('📚 Premium plugin not found:', error.message);
      return false;
    }
  }
  
  program
    .command("run")
    .description("export from Joplin to Anki")
    .requiredOption(
      "-t, --joplintoken <token>",
      "token for Joplin Web Clipper API",
      configStore.get("joplinToken")
    )
    
    .action(async () => {
      // Try to load premium plugin
      const premiumLoaded = await loadPremiumPlugin();
      
      // Show tier info (only if verbose)
      if (program.loglevel >= levelVerbose) {
        if (premiumLoaded) {
          console.log('💎 Premium features active\n');
        } else {
          console.log('📚 Free version - Basic features only');
          console.log('💎 Want premium? Visit: https://yoursite.com/premium\n');
        }
      }
      
      // Run the sync
      const now = new Date().toISOString();
      await jta.run(
        program.loglevel,
        program.joplinurl,
        program.joplintoken,
        program.date,
        program.ankiurl
      );
      configStore.set("exportFromDate", now);
    });

const config = program.command("config").description("Get/set configs for JTA");

config
  .command("set")
  .description(
    "Set options in config; these options will be used as default by JTA"
  )
  .action(() => {
    configStore.set("joplinURL", program.joplinurl);
    configStore.set("ankiURL", program.ankiurl);
    configStore.set("joplinToken", program.joplintoken);
    configStore.set("exportFromDate", program.date);
    console.log(configStore.getAll());
  });

config
  .command("get")
  .description("Get options in config")
  .action(() => {
    console.log(configStore.getAll());
  });

function cli(args) {
  program.parse(args);
}
module.exports = cli;

// anki-importer.js - CORRECTED with Media Upload Logic & RESOURCE COUNTING

const { levelApplication, levelVerbose, levelDebug } = require("./log");

// Helper to decode HTML entities (Unchanged)
const decodeHtmlEntities = (text) => {
  if (!text || typeof text !== 'string') return text;
  const entityMap = {
    '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'",
    '&#x27;': "'", '&#x39;': "'", '&#xA0;': ' ', '&nbsp;': ' '
  };
  let decoded = text;
  for (const [entity, char] of Object.entries(entityMap)) {
    decoded = decoded.replace(new RegExp(entity, 'g'), char);
  }
  decoded = decoded.replace(/&#(\d+);/g, (match, dec) => String.fromCharCode(parseInt(dec, 10)));
  decoded = decoded.replace(/&#x([0-9a-fA-F]+);/g, (match, hex) => String.fromCharCode(parseInt(hex, 16)));
  return decoded;
};

const batchImporter = async (aClient, items, batchSize = 10, log, jClient) => {
  // ============================================================================
  // THE FIX: Added resource counters to the summary object
  // ============================================================================
  const summary = { 
    created: 0, updated: 0, skipped: 0, failed: 0, 
    resourcesUploaded: 0, resourcesFailed: 0 
  };
  
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    log(levelApplication, `Processing batch ${Math.floor(i / batchSize) + 1} of ${Math.ceil(items.length / batchSize)}...`);
    
    const promises = batch.map(async (item) => {
      try {
        // Media Upload Pipeline
        if (item.resourcesToUpload && item.resourcesToUpload.length > 0) {
            log(levelDebug, `[MEDIA] JTA ID ${item.jtaID} has ${item.resourcesToUpload.length} resources to process.`);
            for (const resource of item.resourcesToUpload) {
                try {
                    log(levelApplication, `[MEDIA] Downloading resource ${resource.fileName} from Joplin...`);
                    const fileData = await jClient.request(
                        jClient.urlGen("resources", resource.id, "file"), 
                        "GET", undefined, undefined, false, "binary"
                    );
                    
                    log(levelApplication, `[MEDIA] Uploading resource ${resource.fileName} to Anki...`);
                    await aClient.storeMedia(resource.fileName, fileData);
                    
                    // ========================================================
                    // THE FIX: Increment success counter
                    // ========================================================
                    summary.resourcesUploaded++;

                } catch (e) {
                    log(levelApplication, `❌ Failed to upload resource ${resource.fileName} for JTA ID ${item.jtaID}: ${e.message}`);
                    // ========================================================
                    // THE FIX: Increment failure counter
                    // ========================================================
                    summary.resourcesFailed++;
                }
            }
        }

        // Note processing logic (unchanged)
        await aClient.ensureDeckExists(item.deckName);
        const existingNotes = await aClient.findNote(item.jtaID, item.deckName);
        
        if (item.additionalFields && item.additionalFields.customNoteType) {
          // ... (Dynamic note logic is unchanged)
          const modelName = item.additionalFields.customNoteType;
          const fields = Object.fromEntries(Object.entries(item.additionalFields.customFields).map(([k,v]) => [k, decodeHtmlEntities(v)]));
          if (existingNotes && existingNotes.length > 0) {
            await aClient.updateCustomNote(existingNotes[0], fields);
            await aClient.updateNoteTags(existingNotes[0], item.title, item.notebook, item.tags);
            summary.updated++;
          } else {
            await aClient.createCustomNote(modelName, fields, item.deckName, item.tags, item.title, item.notebook);
            summary.created++;
          }
        } else {
          // ... (Standard note logic is unchanged)
          const decodedAdditionalFields = Object.fromEntries(Object.entries(item.additionalFields || {}).map(([k,v]) => [k, decodeHtmlEntities(v)]));
          if (existingNotes && existingNotes.length > 0) {
            await aClient.updateNote(existingNotes[0], decodedAdditionalFields);
            await aClient.updateNoteTags(existingNotes[0], item.title, item.notebook, item.tags);
            summary.updated++;
          } else {
            await aClient.createNote(
              item.question, item.answer, item.jtaID, item.title,
              item.notebook, item.tags, item.folders, decodedAdditionalFields, item.deckName
            );
            summary.created++;
          }
        }
      } catch (e) {
        log(levelApplication, `❌ Failed to process JTA ID ${item.jtaID}: ${e.message}`);
        summary.failed++;
      }
    });
    
    await Promise.all(promises);
  }
  
  return summary;
};

module.exports = batchImporter;

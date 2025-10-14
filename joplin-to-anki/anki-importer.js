// anki-importer.js - FIXED with Enhanced Debugging

const { levelApplication, levelVerbose, levelDebug } = require("./log");

// Helper to decode HTML entities
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
  const summary = { 
    created: 0, 
    updated: 0, 
    skipped: 0, 
    failed: 0, 
    resourcesUploaded: 0, 
    resourcesFailed: 0,
    createdItems: [] 
  };
  
  log(levelApplication, `📦 Starting batch import of ${items.length} items...`);
  
  // CRITICAL DEBUG: Check what we received
  let totalResourcesInItems = 0;
  items.forEach(item => {
    const resourceCount = item.resourcesToUpload?.length || 0;
    totalResourcesInItems += resourceCount;
    if (resourceCount > 0) {
      log(levelApplication, `[DEBUG] Item ${item.jtaID} has ${resourceCount} resources to upload`);
    }
  });
  log(levelApplication, `[DEBUG] Total resources across all items: ${totalResourcesInItems}`);
  
  if (!jClient) {
    log(levelApplication, `⚠️ WARNING: jClient not provided - cannot download resources!`);
  }
  
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    log(levelApplication, `Processing batch ${Math.floor(i / batchSize) + 1} of ${Math.ceil(items.length / batchSize)}...`);
    
    const promises = batch.map(async (item) => {
      try {
        // ====================================================================
        // PHASE 1: MEDIA UPLOAD PIPELINE (BEFORE NOTE PROCESSING)
        // ====================================================================
        if (item.resourcesToUpload && item.resourcesToUpload.length > 0) {
            log(levelApplication, `[MEDIA] 🎬 Starting upload of ${item.resourcesToUpload.length} resources for JTA ID ${item.jtaID}...`);
            
            for (const resource of item.resourcesToUpload) {
                try {
                    // Validate we have jClient
                    if (!jClient) {
                        throw new Error('Joplin client not provided to batchImporter - cannot download resources');
                    }

                    log(levelApplication, `[MEDIA] ⬇️ Downloading ${resource.fileName} (ID: ${resource.id}) from Joplin...`);
                    
                    // Download from Joplin
                    const fileData = await jClient.request(
                        jClient.urlGen("resources", resource.id, "file"), 
                        "GET", 
                        undefined, 
                        undefined, 
                        false, 
                        "binary"
                    );
                    
                    if (!fileData) {
                        throw new Error(`No data returned for resource ${resource.id}`);
                    }
                    
                    log(levelApplication, `[MEDIA] ⬆️ Uploading ${resource.fileName} to Anki (${fileData.length} bytes)...`);
                    
                    // Upload to Anki
                    await aClient.storeMedia(resource.fileName, fileData);
                    
                    summary.resourcesUploaded++;
                    log(levelApplication, `✅ [MEDIA] Successfully uploaded ${resource.fileName}`);

                } catch (e) {
                    summary.resourcesFailed++;
                    log(levelApplication, `❌ [MEDIA] Failed to upload ${resource.fileName}: ${e.message}`);
                    log(levelDebug, `[MEDIA] Error stack: ${e.stack}`);
                }
            }
        } else {
            log(levelDebug, `[MEDIA] No resources to upload for JTA ID ${item.jtaID}`);
        }

        // ====================================================================
        // PHASE 2: NOTE PROCESSING (CREATE OR UPDATE)
        // ====================================================================
        await aClient.ensureDeckExists(item.deckName);
        const existingNotes = await aClient.findNote(item.jtaID, item.deckName);
        
        // Check if this is a custom/dynamic note type
        if (item.additionalFields && item.additionalFields.customNoteType) {
          // --- CUSTOM NOTE TYPE HANDLING ---
          const modelName = item.additionalFields.customNoteType;
          const fields = Object.fromEntries(
            Object.entries(item.additionalFields.customFields).map(([k, v]) => [k, decodeHtmlEntities(v)])
          );
          
          if (existingNotes && existingNotes.length > 0) {
            log(levelVerbose, `Updating custom note ${item.jtaID} in deck "${item.deckName}"`);
            await aClient.updateCustomNote(existingNotes[0], fields);
            await aClient.updateNoteTags(existingNotes[0], item.title, item.notebook, item.tags);
            summary.updated++;
            log(levelApplication, `✅ Updated custom card: "${item.title}" (Model: ${modelName})`);
          } else {
            log(levelVerbose, `Creating custom note ${item.jtaID} in deck "${item.deckName}"`);
            await aClient.createCustomNote(modelName, fields, item.deckName, item.tags, item.title, item.notebook);
            summary.created++;
            log(levelApplication, `✅ Created custom card: "${item.title}" (Model: ${modelName})`);
          }
        } else {
          // --- STANDARD NOTE TYPE HANDLING ---
          const decodedAdditionalFields = Object.fromEntries(
            Object.entries(item.additionalFields || {}).map(([k, v]) => [k, decodeHtmlEntities(v)])
          );
          
          if (existingNotes && existingNotes.length > 0) {
            log(levelVerbose, `Updating standard note ${item.jtaID} in deck "${item.deckName}"`);
            
            // Build fields object for update
            const cardType = aClient.detectCardType(item.question, item.answer, decodedAdditionalFields);
            const fieldsToUpdate = {};
            
            // Only update non-empty fields
            if (item.question) fieldsToUpdate.Question = decodeHtmlEntities(item.question);
            if (item.answer) fieldsToUpdate.Answer = decodeHtmlEntities(item.answer);
            
            // Add additional fields
            Object.assign(fieldsToUpdate, decodedAdditionalFields);
            
            await aClient.updateNote(existingNotes[0], fieldsToUpdate);
            await aClient.updateNoteTags(existingNotes[0], item.title, item.notebook, item.tags);
            summary.updated++;
            log(levelApplication, `✅ Updated ${cardType} card: "${item.title}"`);
          } else {
            log(levelVerbose, `Creating standard note ${item.jtaID} in deck "${item.deckName}"`);
                        await aClient.createNote(
                          item.question, 
                          item.answer, 
                          item.jtaID, 
                          item.title,
                          item.notebook, 
                          item.tags, 
                          item.folders, 
                          decodedAdditionalFields, 
                          item.deckName
                        );
                        summary.created++;
                        
                        // --- CAPTURE THE CREATED ITEM'S COORDINATES ---
                        summary.createdItems.push({ jtaID: item.jtaID, joplinNoteId: item.joplinNoteId, index: item.index }); // <-- ADD THIS
                        
                        const cardType = aClient.detectCardType(item.question, item.answer, decodedAdditionalFields);
                        log(levelApplication, `✅ Created ${cardType} card: "${item.title}"`);
                      }
                    }
                  } catch (e) {
                    log(levelApplication, `❌ Failed to process JTA ID ${item.jtaID}: ${e.message}`);
                    log(levelDebug, `Error stack: ${e.stack}`);
                    summary.failed++;
                  }
                });
    
    await Promise.all(promises);
  }
  
  // Final summary
  log(levelApplication, `
📊 Batch Import Summary:
   • Created: ${summary.created}
   • Updated: ${summary.updated}
   • Failed: ${summary.failed}
   • Resources Uploaded: ${summary.resourcesUploaded}
   • Resource Failures: ${summary.resourcesFailed}
  `);
  
  return summary;
};

module.exports = batchImporter;

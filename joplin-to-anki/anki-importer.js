// anki-importer.js - FIXED with proper field deletion support

const { levelApplication, levelVerbose, levelDebug } = require("./log");

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
  
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    log(levelApplication, `Processing batch ${Math.floor(i / batchSize) + 1} of ${Math.ceil(items.length / batchSize)}...`);
    
    const promises = batch.map(async (item) => {
      try {
        // PHASE 1: UPLOAD RESOURCES
        if (item.resourcesToUpload && item.resourcesToUpload.length > 0 && jClient) {
          log(levelApplication, `[MEDIA] 🎬 Uploading ${item.resourcesToUpload.length} resources for ${item.jtaID}...`);
          
          for (const resource of item.resourcesToUpload) {
            try {
              const fileData = await jClient.request(
                jClient.urlGen("resources", resource.id, "file"), 
                "GET", undefined, undefined, false, "binary"
              );
              
              if (!fileData) throw new Error(`No data for resource ${resource.id}`);
              
              await aClient.storeMedia(resource.fileName, fileData);
              summary.resourcesUploaded++;
              log(levelApplication, `✅ [MEDIA] Uploaded ${resource.fileName}`);
            } catch (e) {
              summary.resourcesFailed++;
              log(levelApplication, `❌ [MEDIA] Failed: ${resource.fileName}: ${e.message}`);
            }
          }
        }
        
        await aClient.ensureDeckExists(item.deckName);
        const existingNotes = await aClient.findNote(item.jtaID, item.deckName);
        
        const isCustomNote = item.additionalFields && item.additionalFields.customNoteType;
        
        if (isCustomNote) {
          // CUSTOM NOTE TYPE HANDLING
          const modelName = item.additionalFields.customNoteType;
          const fields = Object.fromEntries(
            Object.entries(item.additionalFields.customFields).map(([k, v]) => [k, decodeHtmlEntities(v)])
          );
          
          if (existingNotes && existingNotes.length > 0) {
            await aClient.updateCustomNote(existingNotes[0], fields);
            await aClient.updateNoteTags(existingNotes[0], item.title, item.notebook, item.tags);
            summary.updated++;
            log(levelApplication, `✅ Updated custom "${modelName}" card: "${item.title}"`);
          } else {
            await aClient.createCustomNote(modelName, fields, item.deckName, item.tags, item.title, item.notebook);
            summary.created++;
            summary.createdItems.push({ 
              jtaID: item.jtaID, 
              joplinNoteId: item.joplinNoteId, 
              index: item.index 
            });
            log(levelApplication, `✅ Created custom "${modelName}" card: "${item.title}"`);
          }
        } else {
          // STANDARD NOTE TYPE HANDLING
          const decodedAdditionalFields = Object.fromEntries(
            Object.entries(item.additionalFields || {}).map(([k, v]) => [k, decodeHtmlEntities(v || '')])
          );
          
          const cardType = aClient.detectCardType(item.question, item.answer, decodedAdditionalFields);
          
          if (existingNotes && existingNotes.length > 0) {
            // === FIX: UPDATE WITH PROPER FIELD CLEARING ===
            const fieldsToUpdate = {};
            
            // Always include Question and Answer (use empty string if not present)
            fieldsToUpdate.Question = decodeHtmlEntities(item.question || '');
            fieldsToUpdate.Answer = decodeHtmlEntities(item.answer || '');
            
            // === FIX: Include ALL possible fields, even if empty ===
            // This ensures deleted fields get cleared in Anki
            // IMPORTANT: %%FieldName%% is treated as VALID content, not a placeholder
            const allPossibleFields = [
              'Header', 'Footer', 'Sources', 'Explanation', 'Clinical Correlation',
              'Extra', 'Comments', 'Origin', 'Insertion', 'Innervation', 'Action',
              'OptionA', 'OptionB', 'OptionC', 'OptionD', 'CorrectAnswer',
              'QuestionImagePath', 'AnswerImagePath', 'AltText'
            ];
            
            for (const fieldName of allPossibleFields) {
              const camelCase = fieldName.charAt(0).toLowerCase() + fieldName.slice(1);
              let fieldValue = '';
              
              if (decodedAdditionalFields.hasOwnProperty(camelCase)) {
                fieldValue = decodedAdditionalFields[camelCase];
              } else if (decodedAdditionalFields.hasOwnProperty(fieldName)) {
                fieldValue = decodedAdditionalFields[fieldName];
              }
              
              // Only send to Anki if field exists in the model
              // Empty string is valid and will clear the field
              fieldsToUpdate[fieldName] = fieldValue || '';
            }
            
            await aClient.updateNote(existingNotes[0], fieldsToUpdate);
            await aClient.updateNoteTags(existingNotes[0], item.title, item.notebook, item.tags);
            summary.updated++;
            log(levelApplication, `✅ Updated standard "${cardType}" card: "${item.title}" (${Object.keys(fieldsToUpdate).length} fields)`);
          } else {
            // CREATE NEW
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
            summary.createdItems.push({ 
              jtaID: item.jtaID, 
              joplinNoteId: item.joplinNoteId, 
              index: item.index 
            });
            log(levelApplication, `✅ Created standard "${cardType}" card: "${item.title}"`);
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

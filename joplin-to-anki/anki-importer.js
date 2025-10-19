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

/**
 * Converts Joplin resource links back to Anki media filenames
 * @param {string} html - HTML content with potential Joplin resource links
 * @param {object} mediaConversionMap - Bidirectional mapping of resources
 * @param {function} log - Logging function
 * @returns {string} - HTML with Anki filenames restored
 */
const convertJoplinResourcesToAnkiMedia = (html, mediaConversionMap, log) => {
  if (!html || typeof html !== 'string') return html;
  if (!mediaConversionMap || Object.keys(mediaConversionMap).length === 0) return html;
  
  const cheerio = require('cheerio');
  const $ = cheerio.load(html, { decodeEntities: false });
  const images = $('img');
  let converted = 0;
  
  images.each((i, imgElement) => {
    const img = $(imgElement);
    const src = img.attr('src');
    
    // Check if it's a Joplin resource link (format: ":/{resource-id}")
    if (src && src.startsWith(':/')) {
      const resourceId = src.replace(':/', '');
      
      // Look up the original Anki filename using reverse mapping
      if (mediaConversionMap[resourceId]) {
        const originalAnkiFilename = mediaConversionMap[resourceId];
        img.attr('src', originalAnkiFilename);
        converted++;
        log(levelDebug, `[MEDIA-REVERSE] ✅ :/${resourceId} → ${originalAnkiFilename}`);
      } else {
        log(levelVerbose, `[MEDIA-REVERSE] ⚠️ No mapping found for :/${resourceId} (might be a managed resource)`);
      }
    }
  });
  
  if (converted > 0) {
    log(levelApplication, `[MEDIA-REVERSE] 📊 Converted ${converted} Joplin resource(s) back to Anki media`);
  }
  
  return $.html();
};

const batchImporter = async (aClient, items, batchSize = 10, log, jClient, mediaConversionMap = {}) => {
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
      log(levelDebug, `[IMPORTER-DEBUG] Processing item ${item.jtaID}. Full item object received: ${JSON.stringify(item, null, 2)}`);
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

        log(levelDebug, `[IMPORTER-DEBUG] Item ${item.jtaID}: Is this a custom note? -> ${isCustomNote}`);
        
        if (isCustomNote) {
          // CUSTOM NOTE TYPE HANDLING
          const modelName = item.additionalFields.customNoteType;
          log(levelDebug, `[IMPORTER-DEBUG] Taking the CUSTOM note path for ${item.jtaID}.`);
          log(levelDebug, `[IMPORTER-DEBUG] Custom ModelName: "${modelName}". Fields to be sent to Anki: ${JSON.stringify(item.additionalFields.customFields, null, 2)}`);
          const fields = Object.fromEntries(
            Object.entries(item.additionalFields.customFields).map(([k, v]) => [k, decodeHtmlEntities(v)])
          );
            
            // ✅ CONVERT JOPLIN RESOURCES TO ANKI MEDIA IN CUSTOM FIELDS
            const fields = {};
            for (const [fieldName, fieldValue] of Object.entries(item.additionalFields.customFields)) {
              let convertedValue = decodeHtmlEntities(fieldValue);
              
              // Check if this field contains HTML with potential Joplin resource links
              if (convertedValue && typeof convertedValue === 'string' && convertedValue.includes(':/')) {
                log(levelDebug, `[CUSTOM-MEDIA] Checking field "${fieldName}" for Joplin resources`);
                convertedValue = convertJoplinResourcesToAnkiMedia(convertedValue, mediaConversionMap, log);
              }
              
              fields[fieldName] = convertedValue;
            }
            
            log(levelDebug, `[CUSTOM-NOTE] Processed ${Object.keys(fields).length} fields for custom note type "${modelName}"`);
            
            if (existingNotes && existingNotes.length > 0) {
              await aClient.updateCustomNote(existingNotes[0], fields);
              await aClient.updateNoteTags(existingNotes[0], item.title, item.notebook, item.tags);
              summary.updated++;
              log(levelApplication, `✅ Updated custom "${modelName}" card: "${item.title}" (${Object.keys(fields).length} fields)`);
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
          }
        } else {
          // STANDARD NOTE TYPE HANDLING
          const decodedAdditionalFields = Object.fromEntries(
            Object.entries(item.additionalFields || {}).map(([k, v]) => [k, decodeHtmlEntities(v || '')])
          );

          log(levelDebug, `[IMPORTER-DEBUG] Taking the STANDARD note path for ${item.jtaID}.`);
          
          const cardType = aClient.detectCardType(item.question, item.answer, decodedAdditionalFields);
          
          if (existingNotes && existingNotes.length > 0) {
            // === FIX: UPDATE WITH PROPER FIELD CLEARING ===
            const fieldsToUpdate = {};
            
            // ✅ CONVERT JOPLIN RESOURCES BACK TO ANKI FILENAMES FIRST
            const convertedQuestion = convertJoplinResourcesToAnkiMedia(
              item.question || '', 
              mediaConversionMap, 
              log
            );
            const convertedAnswer = convertJoplinResourcesToAnkiMedia(
              item.answer || '', 
              mediaConversionMap, 
              log
            );
            
            // Always include Question and Answer (use empty string if not present)
            fieldsToUpdate.Question = decodeHtmlEntities(convertedQuestion);
            fieldsToUpdate.Answer = decodeHtmlEntities(convertedAnswer);
            
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
              
              // ✅ CONVERT RESOURCES IN THIS FIELD TOO (if it contains HTML)
              if (fieldValue && typeof fieldValue === 'string' && fieldValue.includes(':/')) {
                fieldValue = convertJoplinResourcesToAnkiMedia(fieldValue, mediaConversionMap, log);
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
            // ✅ CONVERT RESOURCES BEFORE CREATING
            const convertedQuestion = convertJoplinResourcesToAnkiMedia(
              item.question, 
              mediaConversionMap, 
              log
            );
            const convertedAnswer = convertJoplinResourcesToAnkiMedia(
              item.answer, 
              mediaConversionMap, 
              log
            );
            
            // Also convert resources in additional fields
            const convertedAdditionalFields = {};
            for (const [key, value] of Object.entries(decodedAdditionalFields)) {
              if (value && typeof value === 'string' && value.includes(':/')) {
                convertedAdditionalFields[key] = convertJoplinResourcesToAnkiMedia(value, mediaConversionMap, log);
              } else {
                convertedAdditionalFields[key] = value;
              }
            }
            
            await aClient.createNote(
              convertedQuestion, 
              convertedAnswer, 
              item.jtaID, 
              item.title,
              item.notebook, 
              item.tags, 
              item.folders, 
              convertedAdditionalFields, 
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

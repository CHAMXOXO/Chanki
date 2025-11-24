// anki-importer.js

const { levelApplication, levelVerbose, levelDebug } = require("./log");
const { buildAnkiFieldsObject } = require('./anki-client');

const decodeHtmlEntities = (text) => {
  // Ensure we always work with a string
  if (typeof text !== 'string') return '';
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

const convertJoplinResourcesToAnkiMedia = (html, mediaConversionMap, log) => {
  if (!html || typeof html !== 'string') return html;
  if (!mediaConversionMap || Object.keys(mediaConversionMap).length === 0) return html;
  
  const cheerio = require('cheerio');
  const $ = cheerio.load(html, { decodeEntities: false });
  const images = $('img');
  
  images.each((i, imgElement) => {
    const img = $(imgElement);
    const src = img.attr('src');
    
    if (src && src.startsWith(':/')) {
      const resourceId = src.replace(':/', '');
      if (mediaConversionMap[resourceId]) {
        img.attr('src', mediaConversionMap[resourceId]);
      }
    }
  });
  return $.html();
};

const batchImporter = async (aClient, items, batchSize = 10, log, jClient, mediaConversionMap = {}) => {
  const itemsToCreate = items.create || [];
  const itemsToUpdate = items.update || [];
  const totalItems = itemsToCreate.length + itemsToUpdate.length;

  const summary = { 
    created: 0, 
    updated: 0, 
    skipped: 0, 
    failed: 0, 
    resourcesUploaded: 0, 
    resourcesFailed: 0,
    createdItems: [] 
  };
  
  log(levelApplication, `📦 Starting batch import of ${totalItems} items...`);
  
  const allItems = [...itemsToCreate, ...itemsToUpdate];
  
   for (let i = 0; i < allItems.length; i += batchSize) {
     const batch = allItems.slice(i, i + batchSize);
     log(levelApplication, `Processing batch ${Math.floor(i / batchSize) + 1} of ${Math.ceil(allItems.length / batchSize)}...`);
     
     const promises = batch.map(async (item) => {
       try {
         if (item.resourcesToUpload && item.resourcesToUpload.length > 0 && jClient) {
           log(levelVerbose, `[MEDIA] 🎬 Uploading ${item.resourcesToUpload.length} resources for ${item.jtaID}...`);
           for (const resource of item.resourcesToUpload) {
             try {
               const fileData = await jClient.request(
                 jClient.urlGen("resources", resource.id, "file"), "GET", undefined, undefined, false, "binary"
               );
               if (!fileData) throw new Error(`No data for resource ${resource.id}`);
               await aClient.storeMedia(resource.fileName, fileData);
               summary.resourcesUploaded++;
               log(levelVerbose, `✅ [MEDIA] Uploaded ${resource.fileName}`);
             } catch (e) {
               summary.resourcesFailed++;
               log(levelApplication, `❌ [MEDIA] Failed: ${resource.fileName}: ${e.message}`);
             }
           }
         }
         
         await aClient.ensureDeckExists(item.deckName);
         
         const isCustomNote = item.additionalFields && item.additionalFields.customNoteType;
         
         if (isCustomNote) {
             const modelName = item.additionalFields.customNoteType;
             const fields = {};
             // --- FIX: Ensure every field value is a string to prevent "bad argument type" API errors. ---
             for (const [fieldName, fieldValue] of Object.entries(item.additionalFields.customFields)) {
               fields[fieldName] = decodeHtmlEntities(fieldValue); // Removed (|| '') as decode handles it
             }
             // --- END FIX ---
     
             if (item.ankiNoteId) {
                await aClient.updateCustomNote(item.ankiNoteId, fields);
                await aClient.updateNoteTags(item.ankiNoteId, item.title, item.notebook, item.tags);
                summary.updated++;
                log(levelApplication, `✅ Updated custom "${modelName}" card: "${item.title}"`);
             } else {
               await aClient.createCustomNote(modelName, fields, item.deckName, item.tags, item.title, item.notebook);
               summary.created++;
               summary.createdItems.push({ jtaID: item.jtaID, joplinNoteId: item.joplinNoteId, index: item.index });
               log(levelApplication, `✅ Created custom "${modelName}" card: "${item.title}"`);
             }
         } else {
           const modelName = item.additionalFields.ankiModelName || aClient.detectCardType(item.question, item.answer, item.additionalFields);
               const cardType = aClient.detectCardType(item.question, item.answer, item.additionalFields); // Still useful for buildAnkiFieldsObject
       
               const decodedAdditionalFields = Object.fromEntries(
                 Object.entries(item.additionalFields || {}).map(([k, v]) => [k, decodeHtmlEntities(v)])
               );
       
               // 2. Build the fields object using this reliable information.
               const fields = buildAnkiFieldsObject(decodeHtmlEntities(item.question), decodeHtmlEntities(item.answer), item.jtaID, cardType, decodedAdditionalFields);
       
               if (item.ankiNoteId) {
                  // 3. Perform the UPDATE using the correctly built fields.
                  await aClient.updateNote(item.ankiNoteId, fields);
                  await aClient.updateNoteTags(item.ankiNoteId, item.title, item.notebook, item.tags);
                  summary.updated++;
                  log(levelApplication, `✅ Updated standard "${modelName}" card: "${item.title}"`);
               } else {
                 // 4. Perform the CREATE. createNote internally figures out the model name.
                 await aClient.createNote(
                   item.question, item.answer, item.jtaID, item.title, item.notebook, 
                   item.tags, item.folders, decodedAdditionalFields, item.deckName
                 );
                 summary.created++;
                 summary.createdItems.push({ jtaID: item.jtaID, joplinNoteId: item.joplinNoteId, index: item.index });
               }
           }
       } catch (e) {
         const isDuplicateError = e.message && e.message.includes('cannot create note because it is a duplicate');
         if (isDuplicateError) {
           log(levelVerbose, `⏭️ Skipped duplicate creation attempt for ${item.jtaID}. Treating as implicitly synced/skipped.`);
           summary.skipped++;
           return; 
         }
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
    • Skipped: ${summary.skipped}
    • Failed: ${summary.failed}
    • Resources Uploaded: ${summary.resourcesUploaded}
    • Resource Failures: ${summary.resourcesFailed}
   `);
   
   return summary;
 };

module.exports = batchImporter;

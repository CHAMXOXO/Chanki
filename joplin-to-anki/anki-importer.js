// anki-importer.js - FIXED Logging and Custom Note Type Routing

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
        await aClient.ensureDeckExists(item.deckName);
        const existingNotes = await aClient.findNote(item.jtaID, item.deckName);
        
        // FIXED: Explicit type checking with detailed logging
        const isCustomNote = item.additionalFields && 
                             item.additionalFields.customNoteType &&
                             typeof item.additionalFields.customNoteType === 'string' &&
                             item.additionalFields.customNoteType.trim().length > 0;
        
        log(levelDebug, `[TYPE CHECK] Item ${item.jtaID}: isCustomNote=${isCustomNote}, customNoteType=${item.additionalFields?.customNoteType}`);
        
        if (isCustomNote) {
          // ========================================================================
          // CUSTOM NOTE TYPE HANDLING
          // ========================================================================
          const modelName = item.additionalFields.customNoteType;
          const fields = Object.fromEntries(
            Object.entries(item.additionalFields.customFields || {}).map(([k, v]) => [k, decodeHtmlEntities(v)])
          );
          
          log(levelApplication, `📥 Processing custom note with model: "${modelName}"`);
          log(levelDebug, `   Fields: ${JSON.stringify(Object.keys(fields))}`);
          
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
          // ========================================================================
          // STANDARD NOTE TYPE HANDLING
          // ========================================================================
          const decodedAdditionalFields = Object.fromEntries(
            Object.entries(item.additionalFields || {}).map(([k, v]) => [k, decodeHtmlEntities(v)])
          );
          
          const cardType = aClient.detectCardType(item.question, item.answer, decodedAdditionalFields);
          
          log(levelDebug, `[TYPE CHECK] Standard note detected as type: ${cardType}`);
          
          if (existingNotes && existingNotes.length > 0) {
            // UPDATE EXISTING STANDARD NOTE
            const fieldsToUpdate = {};
            
            if (item.question) fieldsToUpdate.Question = decodeHtmlEntities(item.question);
            if (item.answer) fieldsToUpdate.Answer = decodeHtmlEntities(item.answer);
            
            Object.assign(fieldsToUpdate, decodedAdditionalFields);
            
            await aClient.updateNote(existingNotes[0], fieldsToUpdate);
            await aClient.updateNoteTags(existingNotes[0], item.title, item.notebook, item.tags);
            summary.updated++;
            log(levelApplication, `✅ Updated standard "${cardType}" card: "${item.title}"`);
          } else {
            // CREATE NEW STANDARD NOTE
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

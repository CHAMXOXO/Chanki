// anki-importer.js - WITH DEBUG LOGGING & HTML ENTITY DECODING

const { levelApplication, levelVerbose, levelDebug } = require("./log");

// Helper to decode HTML entities
const decodeHtmlEntities = (text) => {
  if (!text || typeof text !== 'string') return text;
  const entityMap = {
    '&amp;': '&',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&apos;': "'",
    '&#x27;': "'",
    '&#39;': "'",
    '&#xA0;': ' ',
    '&nbsp;': ' '
  };
  let decoded = text;
  for (const [entity, char] of Object.entries(entityMap)) {
    decoded = decoded.replace(new RegExp(entity, 'g'), char);
  }
  // Also handle numeric entities like &#123;
  decoded = decoded.replace(/&#(\d+);/g, (match, dec) => {
    return String.fromCharCode(parseInt(dec, 10));
  });
  // Handle hex entities like &#x1A;
  decoded = decoded.replace(/&#x([0-9a-fA-F]+);/g, (match, hex) => {
    return String.fromCharCode(parseInt(hex, 16));
  });
  return decoded;
};

const batchImporter = async (aClient, items, batchSize = 10, log) => {
  const summary = { created: 0, updated: 0, skipped: 0, failed: 0 };
  
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    log(levelApplication, `Processing batch ${Math.floor(i / batchSize) + 1} of ${Math.ceil(items.length / batchSize)}...`);
    
    const promises = batch.map(async (item) => {
      try {
        // Ensure the deck exists before trying to find or create a note in it
        await aClient.ensureDeckExists(item.deckName);
        const existingNotes = await aClient.findNote(item.jtaID, item.deckName);
        
        // --- DYNAMIC/CUSTOM NOTE PATH ---
        if (item.additionalFields && item.additionalFields.customNoteType) {
          const modelName = item.additionalFields.customNoteType;
          const rawFields = item.additionalFields.customFields;
          
          // DECODE HTML ENTITIES IN ALL FIELDS
          const fields = {};
          for (const [key, value] of Object.entries(rawFields)) {
            fields[key] = decodeHtmlEntities(value);
          }
          
          // DEBUG: Log the fields structure with decoded values
          log(levelApplication, `🔍 DEBUG for JTA ID ${item.jtaID}:`);
          log(levelApplication, `   Source Joplin Note ID: ${item.joplinNoteId}`);
          log(levelApplication, `   Joplin Note Title: ${item.title}`);
          log(levelApplication, `   Model: ${modelName}`);
          log(levelApplication, `   Fields type: ${typeof fields}`);
          log(levelApplication, `   Fields keys: ${Object.keys(fields).join(', ')}`);
          
          // Log each field's type and value snippet (decoded)
          for (const [key, value] of Object.entries(fields)) {
            const valueType = typeof value;
            const valuePreview = value !== null && value !== undefined 
              ? String(value).substring(0, 50) 
              : value;
            log(levelApplication, `   - ${key}: (${valueType}) "${valuePreview}"`);
          }
          
          if (existingNotes && existingNotes.length > 0) {
            const noteId = existingNotes[0];
            log(levelApplication, `   Updating existing note ${noteId}...`);
            await aClient.updateCustomNote(noteId, fields);
            await aClient.updateNoteTags(noteId, item.title, item.notebook, item.tags);
            log(levelVerbose, `Updated custom card in Anki for JTA ID: ${item.jtaID}`);
            summary.updated++;
          } else {
            log(levelApplication, `   Creating new note in deck "${item.deckName}"...`);
            await aClient.createCustomNote(modelName, fields, item.deckName, item.tags, item.title, item.notebook);
            log(levelVerbose, `Created new custom card in Anki for JTA ID: ${item.jtaID}`);
            summary.created++;
          }
        }
        // --- STANDARD NOTE PATH ---
        else {
          // DECODE HTML ENTITIES IN ADDITIONAL FIELDS
          const decodedAdditionalFields = {};
          for (const [key, value] of Object.entries(item.additionalFields || {})) {
            decodedAdditionalFields[key] = decodeHtmlEntities(value);
          }
          
          // Log source info for tracking phantom notes
          log(levelDebug, `📌 Processing standard note: ${item.jtaID}`);
          log(levelDebug, `   Source Joplin Note ID: ${item.joplinNoteId}`);
          log(levelDebug, `   Joplin Note Title: ${item.title}`);
          log(levelDebug, `   Target Deck: ${item.deckName}`);
          
          if (existingNotes && existingNotes.length > 0) {
            const noteId = existingNotes[0];
            await aClient.updateNote(noteId, decodedAdditionalFields);
            await aClient.updateNoteTags(noteId, item.title, item.notebook, item.tags);
            log(levelVerbose, `Updated card in Anki for JTA ID: ${item.jtaID}`);
            summary.updated++;
          } else {
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
            log(levelVerbose, `Created new card in Anki for JTA ID: ${item.jtaID}`);
            summary.created++;
          }
        }
      } catch (e) {
        log(levelApplication, `❌ Failed to process JTA ID ${item.jtaID}: ${e.message}`);
        log(levelDebug, `   Source Joplin Note ID: ${item.joplinNoteId}`);
        log(levelDebug, `   Stack trace: ${e.stack}`);
        summary.failed++;
      }
    });
    
    await Promise.all(promises);
  }
  
  return summary;
};

module.exports = batchImporter;

// anki-importer.js (DEFINITIVE CRASH-PROOF VERSION)
const { levelApplication, levelVerbose, levelDebug } = require("./log");

const normalizeTags = (tags = []) => (Array.isArray(tags) ? tags.map(t => (t || "").toString().trim()) : []);

const buildEnhancedFields = (additionalFields = {}) => {
  return {
    header: additionalFields.header || "", footer: additionalFields.footer || "", sources: additionalFields.sources || "",
    explanation: additionalFields.explanation || "", clinicalCorrelation: additionalFields.clinicalCorrelation || "",
    extra: additionalFields.extra || "", origin: additionalFields.origin || "", insertion: additionalFields.insertion || "",
    innervation: additionalFields.innervation || "", action: additionalFields.action || "", comments: additionalFields.comments || "",
    optionA: additionalFields.optionA || "", optionB: additionalFields.optionB || "", optionC: additionalFields.optionC || "",
    optionD: additionalFields.optionD || "", correctAnswer: additionalFields.correctAnswer || "",
    questionImagePath: additionalFields.questionImagePath || "", answerImagePath: additionalFields.answerImagePath || "",
    altText: additionalFields.altText || "",
  };
};

// This function is now defined in anki-client.js to be shared
// We just need a placeholder here for structure
const buildAnkiFieldsObject = () => ({});

const validateImportData = (question, answer, jtaID, title, additionalFields = {}, inferredType) => {
  const errors = [];
  if (!question || question.toString().trim().length === 0) errors.push("Question is empty or missing");
  if (inferredType !== 'cloze' && inferredType !== 'imageOcclusion' && (!answer || answer.toString().trim().length === 0)) {
    errors.push("Answer is empty or missing");
  }
  if (!jtaID || jtaID.toString().trim().length === 0) errors.push("JTA ID is empty or missing");
  if (!title || title.toString().trim().length === 0) errors.push("Title is empty or missing");
  return errors;
};

const importer = async (client, question, answer, jtaID, title, notebook, tags, folders = [], additionalFields = {}, log) => {
  try {
    const normalizedTags = normalizeTags(tags);
    const enhancedFields = buildEnhancedFields(additionalFields);
    
    // Use the client's definitive detector
    const inferredType = client.detectCardType(question, answer, enhancedFields);

    const validationErrors = validateImportData(question, answer, jtaID, title, enhancedFields, inferredType);
    if (validationErrors.length > 0) {
      throw new Error(`Validation failed: ${validationErrors.join("; ")}`);
    }

    const deckName = "default"; // Simplified
    await client.ensureDeckExists(deckName);

    const foundNoteIds = await client.findNote(jtaID, deckName);

    if (foundNoteIds && foundNoteIds.length > 0) {
      const existingNoteId = foundNoteIds[0];
      log(levelVerbose, `Found existing note ${existingNoteId}. Updating.`);
      await client.updateNote(existingNoteId, question, answer, additionalFields);
      await client.updateNoteTags(existingNoteId, title, notebook, normalizedTags);
      return { action: "updated", noteId: existingNoteId };
    } else {
      log(levelVerbose, `Creating new note for JTA ID ${jtaID}.`);
      const createdNoteId = await client.createNote(question, answer, jtaID, title, notebook, normalizedTags, folders, additionalFields);
      return { action: "created", noteId: createdNoteId };
    }
  } catch (error) {
    throw new Error(`Importer failed for JTA ID ${jtaID}: ${error.message}`);
  }
};

const batchImporter = async (client, items, batchSize = 10, log) => {
  const results = { created: 0, updated: 0, skipped: 0, failed: 0, errors: [] };
  log(levelApplication, `Starting batch import of ${items.length} items...`);
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    const promises = batch.map(async (item) => {
      try {
        const res = await importer(client, item.question, item.answer, item.jtaID, item.title, item.notebook, item.tags, item.folders, item.additionalFields || {}, log);
        if (res.action === "created") results.created++;
        else if (res.action === "updated") results.updated++;
        else if (res.action === "skipped") results.skipped++;
      } catch (err) {
        results.failed++;
        results.errors.push({ item: item.jtaID, error: err.message });
        log(levelApplication, `Batch item failed: ${item.jtaID} - ${err.message}`);
      }
    });
    await Promise.allSettled(promises);
  }
  log(levelApplication, `Batch import completed - Created: ${results.created}, Updated: ${results.updated}, Skipped: ${results.skipped}, Failed: ${results.failed}`);
  return results;
};

module.exports = { importer, batchImporter };

// anki-importer.js (FINAL, CLEAN, SINGLE-FUNCTION VERSION)
const { levelApplication, levelVerbose, levelDebug } = require("./log");

const MCQ_MIN_OPTIONS = 2;

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

const buildAnkiFieldsObject = (question, answer, jtaID, inferredType, enhancedFields) => {
  let fields = { "Joplin to Anki ID": jtaID };
  switch (inferredType) {
      case 'basic':
          fields["Header"] = enhancedFields.header; fields["Question"] = question; fields["Answer"] = answer;
          fields["Explanation"] = enhancedFields.explanation; fields["Clinical Correlation"] = enhancedFields.clinicalCorrelation;
          fields["Footer"] = enhancedFields.footer; fields["Sources"] = enhancedFields.sources;
          break;
      case 'cloze':
          fields["Header"] = enhancedFields.header; fields["Text"] = question; fields["Extra"] = enhancedFields.extra;
          fields["Explanation"] = enhancedFields.explanation; fields["Clinical Correlation"] = enhancedFields.clinicalCorrelation;
          fields["Footer"] = enhancedFields.footer; fields["Sources"] = enhancedFields.sources;
          break;
      case 'mcq':
          fields["Header"] = enhancedFields.header; fields["Question"] = question; fields["OptionA"] = enhancedFields.optionA;
          fields["OptionB"] = enhancedFields.optionB; fields["OptionC"] = enhancedFields.optionC; fields["OptionD"] = enhancedFields.optionD;
          fields["CorrectAnswer"] = enhancedFields.correctAnswer; fields["Explanation"] = enhancedFields.explanation;
          fields["Clinical Correlation"] = enhancedFields.clinicalCorrelation;
          fields["Footer"] = enhancedFields.footer; fields["Sources"] = enhancedFields.sources;
          break;
      case 'imageOcclusion':
          fields["Header"] = enhancedFields.header; fields["QuestionImagePath"] = enhancedFields.questionImagePath;
          fields["AnswerImagePath"] = enhancedFields.answerImagePath; fields["AltText"] = enhancedFields.altText;
          fields["Question"] = question; fields["Answer"] = answer; fields["Origin"] = enhancedFields.origin;
          fields["Insertion"] = enhancedFields.insertion; fields["Innervation"] = enhancedFields.innervation;
          fields["Action"] = enhancedFields.action; fields["Comments"] = enhancedFields.comments;
          fields["Clinical Correlation"] = enhancedFields.clinicalCorrelation; fields["Footer"] = enhancedFields.footer;
          fields["Sources"] = enhancedFields.sources;
          break;
  }
  return fields;
};

const validateImportData = (question, answer, jtaID, title, inferredType) => {
  const errors = [];
  if (inferredType !== 'cloze' && (!question || question.toString().trim().length === 0)) {
      errors.push("Question is empty or missing");
  }
  if (inferredType !== 'cloze' && inferredType !== 'imageOcclusion' && (!answer || answer.toString().trim().length === 0)) {
      errors.push("Answer is empty or missing for this card type");
  }
  if (!jtaID || jtaID.toString().trim().length === 0) errors.push("JTA ID is empty or missing");
  if (!title || title.toString().trim().length === 0) errors.push("Title is empty or missing");
  return errors;
};

const inferCardType = (question, answer, enhancedFields = {}) => {
  if (/\{\{c\d+::[^}]+\}\}/g.test(question || "")) return "cloze";
  if ((enhancedFields.questionImagePath||'').trim() || (enhancedFields.answerImagePath||'').trim()) return "imageOcclusion";
  const hasCorrectAnswer = (enhancedFields.correctAnswer || '').trim().length > 0;
  const options = [enhancedFields.optionA, enhancedFields.optionB, enhancedFields.optionC, enhancedFields.optionD];
  const hasMinOptions = options.filter(opt => (opt || '').trim().length > 0).length >= 2;
  if (hasCorrectAnswer && hasMinOptions) return "mcq";
  return "basic";
};

// anki-importer.js -> replace the importer function

const importer = async (client, question, answer, jtaID, title, notebook, tags, folders = [], additionalFields = {}, log) => {
  try {
    const normalizedTags = normalizeTags(tags);
    const enhancedFields = buildEnhancedFields(additionalFields);
    const inferredType = inferCardType(question, answer, enhancedFields);

    const validationErrors = validateImportData(question, answer, jtaID, title, inferredType);
    if (validationErrors.length > 0) throw new Error(`Validation failed: ${validationErrors.join("; ")}`);

    const deckName = "default";
    // --- THIS IS THE LINE WITH THE FIX ---
    await client.ensureDeckExists(deckName); // Corrected from 'deckname' to 'deckName'
    // --- END OF FIX ---
    
    const joplinFields = buildAnkiFieldsObject(question, answer, jtaID, inferredType, enhancedFields);
    const foundNoteIds = await client.findNote(jtaID, deckName);

    if (foundNoteIds && foundNoteIds.length > 0) {
      const existingNoteId = foundNoteIds[0];
      const noteInfo = await client.getNoteInfo([existingNoteId]);
      const ankiNote = noteInfo && noteInfo[0];
      if (!ankiNote) throw new Error(`Could not retrieve info for note ${existingNoteId}`);

      let isIdentical = true;
      for (const key in joplinFields) {
        if (joplinFields[key] !== (ankiNote.fields[key] ? ankiNote.fields[key].value : '')) {
          isIdentical = false;
          break;
        }
      }

      if (isIdentical) {
        log(levelVerbose, `Note ${existingNoteId} is unchanged. Skipping.`);
        return { action: "skipped", noteId: existingNoteId };
      }

      log(levelVerbose, `Note ${existingNoteId} has changed. Updating.`);
      await client.updateNote(existingNoteId, joplinFields); 
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

// anki-importer.js

// ... (keep the rest of the file the same)

const batchImporter = async (client, items, batchSize = 10, log) => {
  const results = { created: 0, updated: 0, skipped: 0, failed: 0, errors: [] };
  log(levelApplication, `Starting batch import of ${items.length} items...`);

  // Process items one by one to avoid overwhelming AnkiConnect
  for (const item of items) {
    try {
      const res = await importer(client, item.question, item.answer, item.jtaID, item.title, item.notebook, item.tags, item.folders, item.additionalFields || {}, log);
      if (res.action === "created") {
        results.created++;
      } else if (res.action === "updated") {
        results.updated++;
      } else if (res.action === "skipped") {
        results.skipped++;
      }
    } catch (err) {
      results.failed++;
      results.errors.push({ item: item.jtaID, error: err.message });
      log(levelApplication, `Batch item failed: ${item.jtaID} - ${err.message}`);
    }
  }

  log(levelApplication, `Batch import completed - Created: ${results.created}, Updated: ${results.updated}, Skipped: ${results.skipped}, Failed: ${results.failed}`);
  if (results.failed > 0) {
    log(levelApplication, `Errors occurred for the following items:`, results.errors);
  }
  return results;
};

module.exports = { importer, batchImporter };;

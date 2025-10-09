// anki-importer.js (FINAL INTELLIGENT UPDATE VERSION)
const { levelApplication, levelVerbose, levelDebug } = require("./log");

const MCQ_MIN_OPTIONS = 2;

/**
 * Helper: normalize tags array -> lower-case trimmed strings
 */
const normalizeTags = (tags = []) => (Array.isArray(tags) ? tags.map(t => (t || "").toString().trim()) : []);

/**
 * Build enhancedFields object mapping all template-specific fields
 */
const buildEnhancedFields = (additionalFields = {}) => {
  return {
    header: additionalFields.header || additionalFields.Header || "",
    footer: additionalFields.footer || additionalFields.Footer || "",
    sources: additionalFields.sources || additionalFields.Sources || "",
    explanation: additionalFields.explanation || additionalFields.Explanation || "",
    clinicalCorrelation: additionalFields.clinicalCorrelation || additionalFields["Clinical Correlation"] || additionalFields.clinical || "",
    extra: additionalFields.extra || additionalFields.Extra || "",
    origin: additionalFields.origin || additionalFields.Origin || "",
    insertion: additionalFields.insertion || additionalFields.Insertion || "",
    innervation: additionalFields.innervation || additionalFields.Innervation || "",
    action: additionalFields.action || additionalFields.Action || "",
    comments: additionalFields.comments || additionalFields.Comments || "",
    optionA: additionalFields.optionA || additionalFields.OptionA || "",
    optionB: additionalFields.optionB || additionalFields.OptionB || "",
    optionC: additionalFields.optionC || additionalFields.OptionC || "",
    optionD: additionalFields.optionD || additionalFields.OptionD || "",
    correctAnswer: additionalFields.correctAnswer || additionalFields.CorrectAnswer || additionalFields.Correct || "",
    questionImagePath: additionalFields.questionImagePath || additionalFields.QuestionImagePath || "",
    answerImagePath: additionalFields.answerImagePath || additionalFields.AnswerImagePath || "",
    altText: additionalFields.altText || additionalFields.AltText || additionalFields.alt || "",
    text: additionalFields.text || additionalFields.Text || "",
    _rawAdditionalFields: additionalFields,
  };
};

// --- NEW HELPER FUNCTION TO BUILD ANKI FIELDS OBJECT ---
const buildAnkiFieldsObject = (question, answer, jtaID, inferredType, enhancedFields) => {
  let fields = { "Joplin to Anki ID": jtaID };

  switch (inferredType) {
    case 'basic':
      fields["Header"] = enhancedFields.header;
      fields["Question"] = question;
      fields["Answer"] = answer;
      fields["Explanation"] = enhancedFields.explanation;
      fields["Clinical Correlation"] = enhancedFields.clinicalCorrelation;
      fields["Footer"] = enhancedFields.footer;
      fields["Sources"] = enhancedFields.sources;
      break;
    case 'cloze':
      fields["Header"] = enhancedFields.header;
      fields["Text"] = question; // In cloze, the question content goes into the "Text" field
      fields["Extra"] = enhancedFields.extra;
      fields["Explanation"] = enhancedFields.explanation;
      fields["Clinical Correlation"] = enhancedFields.clinicalCorrelation;
      fields["Footer"] = enhancedFields.footer;
      fields["Sources"] = enhancedFields.sources;
      break;
    case 'mcq':
      fields["Header"] = enhancedFields.header;
      fields["Question"] = question;
      fields["OptionA"] = enhancedFields.optionA;
      fields["OptionB"] = enhancedFields.optionB;
      fields["OptionC"] = enhancedFields.optionC;
      fields["OptionD"] = enhancedFields.optionD;
      fields["CorrectAnswer"] = enhancedFields.correctAnswer;
      fields["Explanation"] = enhancedFields.explanation;
      fields["Clinical Correlation"] = enhancedFields.clinicalCorrelation;
      fields["Footer"] = enhancedFields.footer;
      fields["Sources"] = enhancedFields.sources;
      break;
    case 'imageOcclusion':
      fields["Header"] = enhancedFields.header;
      fields["QuestionImagePath"] = enhancedFields.questionImagePath;
      fields["AnswerImagePath"] = enhancedFields.answerImagePath;
      fields["AltText"] = enhancedFields.altText;
      fields["Question"] = question;
      fields["Answer"] = answer;
      fields["Origin"] = enhancedFields.origin;
      fields["Insertion"] = enhancedFields.insertion;
      fields["Innervation"] = enhancedFields.innervation;
      fields["Action"] = enhancedFields.action;
      fields["Comments"] = enhancedFields.comments;
      fields["Clinical Correlation"] = enhancedFields.clinicalCorrelation;
      fields["Footer"] = enhancedFields.footer;
      fields["Sources"] = enhancedFields.sources;
      break;
  }
  return fields;
};


/**
 * Validate import data with RELAXED rules for medical/educational content
 */
const validateImportData = (question, answer, jtaID, title, additionalFields = {}, inferredType) => {
  const errors = [];

  if (!question || question.toString().trim().length === 0) {
    errors.push("Question is empty or missing");
  }

  if (inferredType === 'imageOcclusion') {
    const hasImages = (additionalFields.questionImagePath && additionalFields.questionImagePath.trim()) ||
                      (additionalFields.answerImagePath && additionalFields.answerImagePath.trim());
    if (!hasImages && (!answer || answer.toString().trim().length === 0)) {
      errors.push("Image Occlusion card requires either Answer text or image paths");
    }
  } else if (inferredType === 'cloze') {
    // Cloze cards do not require a separate answer field, so we do nothing.
  } else {
    // For all other card types (e.g., Basic, MCQ), the Answer is required.
    if (!answer || answer.toString().trim().length === 0) {
      errors.push("Answer is empty or missing");
    }
  }

  if (!jtaID || jtaID.toString().trim().length === 0) errors.push("JTA ID is empty or missing");
  if (!title || title.toString().trim().length === 0) errors.push("Title is empty or missing");
  if (question && question.length > 15000) errors.push("Question is too long (>15000 characters)");
  if (answer && answer.length > 25000) errors.push("Answer is too long (>25000 characters)");

  switch (inferredType) {
    case 'mcq':
      const { optionA, optionB, optionC, optionD, correctAnswer } = additionalFields;
      const options = [optionA, optionB, optionC, optionD].map(opt => (opt || "").toString().trim()).filter(Boolean);
      if (options.length < MCQ_MIN_OPTIONS) errors.push(`MCQ requires at least ${MCQ_MIN_OPTIONS} non-empty options`);
      if (!correctAnswer || correctAnswer.toString().trim().length === 0) errors.push("MCQ requires a CorrectAnswer field");
      break;
    case 'imageOcclusion':
      const { questionImagePath, answerImagePath } = additionalFields;
      if (!questionImagePath && !answerImagePath) errors.push("Image Occlusion card requires at least a QuestionImagePath or an AnswerImagePath");
      break;
  }
  return errors;
};

/**
 * Determine the "card type" heuristic
 */
const inferCardType = (question, answer, enhancedFields = {}) => {
  const clozePattern = /\{\{c\d+::[^}]+\}\}/g;
  if (clozePattern.test((question || "") + (answer || ""))) return "cloze";

  if ((enhancedFields.questionImagePath && enhancedFields.questionImagePath.trim().length > 0) ||
      (enhancedFields.answerImagePath && enhancedFields.answerImagePath.trim().length > 0)) {
      return "imageOcclusion";
  }

  const mcqFieldsPresent = [enhancedFields.optionA, enhancedFields.optionB, enhancedFields.optionC, enhancedFields.optionD]
    .some(v => v && v.toString().trim().length > 0) || (enhancedFields.correctAnswer && enhancedFields.correctAnswer.toString().trim().length > 0);

  if (mcqFieldsPresent) return "mcq";

  return "basic";
};

/**
 * Main single-item importer with intelligent update logic
 */
const importer = async (
  client,
  question,
  answer,
  jtaID,
  title,
  notebook,
  tags,
  folders = [],
  additionalFields = {},
  log
) => {
  try {
    const normalizedTags = normalizeTags(tags);
    const enhancedFields = buildEnhancedFields(additionalFields);
    const inferredType = inferCardType(question, answer, enhancedFields);

    const validationErrors = validateImportData(question, answer, jtaID, title, enhancedFields, inferredType);
    if (validationErrors.length > 0) {
      throw new Error(`Validation failed for ${jtaID} (${inferredType}): ${validationErrors.join("; ")}`);
    }

    const deckName = client.determineDeckName(normalizedTags, folders, notebook?.id);
    await client.ensureDeckExists(deckName);
    
    // Build the complete fields object from Joplin data
    const joplinFields = buildAnkiFieldsObject(question, answer, jtaID, inferredType, enhancedFields);

    const foundNoteIds = await client.findNote(jtaID, deckName);

    if (foundNoteIds && foundNoteIds.length > 0) {
      // --- START OF INTELLIGENT UPDATE LOGIC ---
      const existingNoteId = foundNoteIds[0];
      log(levelVerbose, `Found existing note ${existingNoteId}. Checking for changes...`);

      const noteInfo = await client.getNoteInfo([existingNoteId]);
      const ankiNote = noteInfo && noteInfo[0];
      if (!ankiNote) {
        throw new Error(`Could not retrieve info for existing note ${existingNoteId}`);
      }
      
      let isIdentical = true;
      for (const key in joplinFields) {
        if (joplinFields[key] !== (ankiNote.fields[key] ? ankiNote.fields[key].value : '')) {
          isIdentical = false;
          log(levelDebug, `Detected change in field "${key}"`);
          break;
        }
      }

      if (isIdentical) {
        log(levelVerbose, `Note ${existingNoteId} is unchanged. Skipping.`);
        return { action: "skipped", noteId: existingNoteId, deck: deckName };
      }

      log(levelVerbose, `Note ${existingNoteId} has changed. Updating.`);
      await client.updateNote(existingNoteId, question, answer, additionalFields);
      await client.updateNoteTags(existingNoteId, title, notebook, normalizedTags);
      
      return { action: "updated", noteId: existingNoteId, deck: deckName };
      // --- END OF INTELLIGENT UPDATE LOGIC ---

    } else {
      // Create new note
      log(levelVerbose, `Creating new note for JTA ID ${jtaID} in deck "${deckName}"`);
      const createdNoteId = await client.createNote(question, answer, jtaID, title, notebook, normalizedTags, folders, additionalFields);
      return { action: "created", noteId: createdNoteId, deck: deckName };
    }

  } catch (error) {
    const msg = `Importer failed for JTA ID ${jtaID} (title: "${title}"): ${error.message}`;
    log(levelApplication, msg);
    throw new Error(msg);
  }
};

/**
 * Batch importer with enhanced reporting
 */
const batchImporter = async (client, items, batchSize = 10, log) => {
  const results = {
    created: 0,
    updated: 0,
    skipped: 0,
    failed: 0,
    errors: []
  };

  log(levelApplication, `Starting batch import of ${items.length} items (batch size: ${batchSize})`);

  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    log(levelVerbose, `Processing batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(items.length / batchSize)}`);

    const promises = batch.map(async (item) => {
      try {
        const res = await importer(
          client, item.question, item.answer, item.jtaID, item.title,
          item.notebook, item.tags, item.folders, item.additionalFields || {}, log
        );

        if (res.action === "created") results.created++;
        else if (res.action === "updated") results.updated++;
        else if (res.action === "skipped") results.skipped++;

        return res;
      } catch (err) {
        results.failed++;
        const errObj = { item: item.jtaID || "(unknown)", error: err.message };
        results.errors.push(errObj);
        log(levelApplication, `Batch item failed: ${errObj.item} - ${errObj.error}`);
        return { action: "failed", error: err.message };
      }
    });
    await Promise.allSettled(promises);
  }

  log(levelApplication, `Batch import completed - Created: ${results.created}, Updated: ${results.updated}, Skipped: ${results.skipped}, Failed: ${results.failed}`);
  return results;
};

/**
 * validatedImporter: wrapper which validates data before import
 */
const validatedImporter = async (client, question, answer, jtaID, title, notebook, tags, folders = [], additionalFields = {}, log) => {
  const enhancedFields = buildEnhancedFields(additionalFields);
  const inferredType = inferCardType(question, answer, enhancedFields);
  const errors = validateImportData(question, answer, jtaID, title, enhancedFields, inferredType);
  if (errors.length > 0) {
    const msg = `Validation failed for ${jtaID}: ${errors.join("; ")}`;
    log(levelApplication, msg);
    throw new Error(msg);
  }
  return importer(client, question, answer, jtaID, title, notebook, tags, folders, additionalFields, log);
};

/**
 * Duplicate cleanup routine
 */
const cleanupDuplicates = async (client, log) => {
  log(levelVerbose, "Starting duplicate cleanup process...");
  try {
    const decks = await client.getDecks();
    const deckNames = Object.keys(decks || {});
    let totalCleaned = 0;
    for (const deckName of deckNames) {
      if (!deckName.includes("Joplin")) continue;
      const noteQuery = `deck:'${deckName}' "Joplin to Anki ID:*"`;
      const noteIds = await client.doRequest({ action: "findNotes", version: 6, params: { query: noteQuery } });
      if (!noteIds || noteIds.length === 0) continue;
      const notesInfo = await client.doRequest({ action: "notesInfo", version: 6, params: { notes: noteIds } });
      const jtaGroups = {};
      notesInfo.forEach(note => {
        const jtaField = note.fields && note.fields["Joplin to Anki ID"];
        if (jtaField && jtaField.value) {
          const jtaId = jtaField.value;
          if (!jtaGroups[jtaId]) jtaGroups[jtaId] = [];
          jtaGroups[jtaId].push(note);
        }
      });
      for (const [jtaId, notes] of Object.entries(jtaGroups)) {
        if (notes.length > 1) {
          notes.sort((a, b) => b.noteId - a.noteId);
          const toDelete = notes.slice(1).map(n => n.noteId);
          if (toDelete.length > 0) {
            await client.deleteNotes(toDelete);
            totalCleaned += toDelete.length;
          }
        }
      }
    }
    log(levelApplication, `Cleanup completed. Removed ${totalCleaned} duplicate notes.`);
    return totalCleaned;
  } catch (error) {
    log(levelApplication, `Duplicate cleanup failed: ${error.message}`);
    throw error;
  }
};

module.exports = {
  importer,
  batchImporter,
  validatedImporter,
  validateImportData,
  cleanupDuplicates,
  buildAnkiFieldsObject // Export the new helper function
};

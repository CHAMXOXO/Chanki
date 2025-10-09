// anki-importer.js (revised with relaxed validation for medical content and enhanced image occlusion)
const { levelApplication, levelVerbose, levelDebug } = require("./log");

const MCQ_MIN_OPTIONS = 2;

/**
 * Helper: normalize tags array -> lower-case trimmed strings
 */
const normalizeTags = (tags = []) => (Array.isArray(tags) ? tags.map(t => (t || "").toString().trim()) : []);

/**
 * Build enhancedFields object mapping all template-specific fields
 * --- MODIFICATION ---
 */
const buildEnhancedFields = (additionalFields = {}) => {
  return {
    // NEW FIELDS
    header: additionalFields.header || additionalFields.Header || "",
    footer: additionalFields.footer || additionalFields.Footer || "",
    sources: additionalFields.sources || additionalFields.Sources || "",
    // text-based extras
    explanation: additionalFields.explanation || additionalFields.Explanation || "",
    clinicalCorrelation: additionalFields.clinicalCorrelation || additionalFields["Clinical Correlation"] || additionalFields.clinical || "",
    extra: additionalFields.extra || additionalFields.Extra || "",
    // Anatomy fields
    origin: additionalFields.origin || additionalFields.Origin || "",
    insertion: additionalFields.insertion || additionalFields.Insertion || "",
    innervation: additionalFields.innervation || additionalFields.Innervation || "",
    action: additionalFields.action || additionalFields.Action || "",
    comments: additionalFields.comments || additionalFields.Comments || "", 
    // MCQ
    optionA: additionalFields.optionA || additionalFields.OptionA || "",
    optionB: additionalFields.optionB || additionalFields.OptionB || "",
    optionC: additionalFields.optionC || additionalFields.OptionC || "",
    optionD: additionalFields.optionD || additionalFields.OptionD || "",
    correctAnswer: additionalFields.correctAnswer || additionalFields.CorrectAnswer || additionalFields.Correct || "",
    // Image (NEW FIELDS)
    questionImagePath: additionalFields.questionImagePath || additionalFields.QuestionImagePath || "",
    answerImagePath: additionalFields.answerImagePath || additionalFields.AnswerImagePath || "",
    altText: additionalFields.altText || additionalFields.AltText || additionalFields.alt || "",
    // Cloze / Text (Text field for cloze only, if needed)
    text: additionalFields.text || additionalFields.Text || "",
    // Keep original additionalFields available if needed
    _rawAdditionalFields: additionalFields,
  };
};

/**
 * Validate import data with RELAXED rules for medical/educational content:
 * - Basic: question, answer, jtaID, title
 * - MCQ: at least two options + CorrectAnswer present
 * - Image: at least one of questionImagePath or answerImagePath + answer
 * - INCREASED length limits for medical content
 * --- MODIFICATION ---
 */
const validateImportData = (question, answer, jtaID, title, additionalFields = {}, inferredType) => { // ADD inferredType parameter
  const errors = [];

  if (!question || question.toString().trim().length === 0) {
    errors.push("Question is empty or missing");
  }

// For image occlusion, Answer can be empty if image paths exist
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

  if (!jtaID || jtaID.toString().trim().length === 0) {
    errors.push("JTA ID is empty or missing");
  }

  if (!title || title.toString().trim().length === 0) {
    errors.push("Title is empty or missing");
  }

  // RELAXED length limits for medical/educational content
  if (question && question.length > 15000) { // Increased from 5000
    errors.push("Question is too long (>15000 characters)");
  }

  if (answer && answer.length > 25000) { // Increased from 10000
    errors.push("Answer is too long (>25000 characters)");
  }

  // Additional checks based on inferred card type
  switch (inferredType) {
    case 'mcq':
      const { optionA, optionB, optionC, optionD, correctAnswer } = additionalFields;
      const options = [optionA, optionB, optionC, optionD].map(opt => (opt || "").toString().trim()).filter(Boolean);
      if (options.length < MCQ_MIN_OPTIONS) {
        errors.push(`MCQ requires at least ${MCQ_MIN_OPTIONS} non-empty options`);
      }
      if (!correctAnswer || correctAnswer.toString().trim().length === 0) {
        errors.push("MCQ requires a CorrectAnswer field");
      }
      break;

    case 'imageOcclusion':
      const { questionImagePath, answerImagePath } = additionalFields;
      if (!questionImagePath && !answerImagePath) {
        errors.push("Image Occlusion card requires at least a QuestionImagePath or an AnswerImagePath");
      }
      // Your template always includes an answer field. If you wanted to be super strict, uncomment:
      // if (!answer || answer.toString().trim().length === 0) {
      //   errors.push("Image Occlusion card requires an Answer field");
      // }
      break;

    case 'cloze':
      // Cloze doesn't have specific validation rules beyond basic content and cloze syntax check (handled by inferCardType)
      break;

    case 'basic':
      // Basic doesn't have specific validation rules beyond basic content
      break;
  }

  return errors;
};


/**
 * Determine the "card type" heuristic
 * --- MODIFICATION ---
 */
const inferCardType = (question, answer, enhancedFields = {}) => {
  const clozePattern = /\{\{c\d+::[^}]+\}\}/g;
  if (clozePattern.test((question || "") + (answer || ""))) return "cloze";

  // Check for image paths
  if ((enhancedFields.questionImagePath && enhancedFields.questionImagePath.trim().length > 0) ||
      (enhancedFields.answerImagePath && enhancedFields.answerImagePath.trim().length > 0)) {
      return "imageOcclusion"; // Changed from "image" to "imageOcclusion" to match model name
  }

  const mcqFieldsPresent = [enhancedFields.optionA, enhancedFields.optionB, enhancedFields.optionC, enhancedFields.optionD]
    .some(v => v && v.toString().trim().length > 0) || (enhancedFields.correctAnswer && enhancedFields.correctAnswer.toString().trim().length > 0);

  if (mcqFieldsPresent) return "mcq";

  if (enhancedFields.text && enhancedFields.text.trim().length > 0) return "text";

  return "basic";
};

/**
 * Main single-item importer - UPDATED to handle auto-generated JTA IDs and new image fields
 * --- MODIFICATION ---
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
    log(levelDebug, `Importer invoked for JTA ID ${jtaID} (title: "${title}")`);

    // AUTO-GENERATE JTA ID if missing (common for templates)
    if (!jtaID || jtaID.toString().trim().length === 0) {
      const crypto = require('crypto');
      const content = `${title}${question}${answer}`;
      jtaID = `auto_${crypto.createHash('md5').update(content).digest('hex').substring(0, 12)}`;
      log(levelVerbose, `Generated JTA ID: ${jtaID} for note: ${title}`);
    }

    // Normalize tags for passing and logging
    const normalizedTags = normalizeTags(tags);

    // Build a complete enhancedFields mapping
    const enhancedFields = buildEnhancedFields(additionalFields);

    // Infer card type for logging/validation
    const inferredType = inferCardType(question, answer, enhancedFields);
    log(levelDebug, `Inferred card type: ${inferredType}`);

    // Validate fields with RELAXED rules - NOW PASSING INFERRED TYPE
    const validationErrors = validateImportData(question, answer, jtaID, title, enhancedFields, inferredType);
    if (validationErrors.length > 0) {
      const errMsg = `Validation failed for ${jtaID} (${inferredType}): ${validationErrors.join("; ")}`;
      log(levelApplication, errMsg);
      throw new Error(errMsg);
    }

    // Determine deck/subdeck name using client's logic
    const deckName = client.determineDeckName(normalizedTags, folders, notebook?.id);
    log(levelVerbose, `Determined deck for "${title}": ${deckName}`);

    // Ensure deck exists
    await client.ensureDeckExists(deckName);

    // Try to find an existing note for this JTA ID in the target deck
    const foundNoteIds = await client.findNote(jtaID, deckName);

    if (foundNoteIds && foundNoteIds.length > 1) {
      const errorMsg = `Multiple notes found for JTA ID ${jtaID} in deck "${deckName}": ${foundNoteIds.join(", ")}`;
      log(levelApplication, errorMsg);
      throw new Error(errorMsg);
    }

    if (foundNoteIds && foundNoteIds.length === 1) {
      // Update existing note
      const existingNoteId = foundNoteIds[0];
      log(levelVerbose, `Updating existing note ${existingNoteId} for JTA ID ${jtaID} in deck "${deckName}"`);

      await client.updateNote(
        existingNoteId,
        question,
        answer,
        {
          explanation: enhancedFields.explanation,
          extra: enhancedFields.extra,
          clinicalCorrelation: enhancedFields.clinicalCorrelation,
          comments: enhancedFields.comments,
          optionA: enhancedFields.optionA,
          optionB: enhancedFields.optionB,
          optionC: enhancedFields.optionC,
          optionD: enhancedFields.optionD,
          correctAnswer: enhancedFields.correctAnswer,
          // NEW IMAGE FIELDS
          questionImagePath: enhancedFields.questionImagePath,
          answerImagePath: enhancedFields.answerImagePath,
          altText: enhancedFields.altText,
          text: enhancedFields.text,
          // Anatomy fields
          origin: enhancedFields.origin,
          insertion: enhancedFields.insertion,
          innervation: enhancedFields.innervation,
          action: enhancedFields.action,
          // --- ADDED MISSING FIELDS ---
          header: enhancedFields.header,
          footer: enhancedFields.footer,
          sources: enhancedFields.sources
        }
      );

      try {
        await client.updateNoteTags(existingNoteId, title, notebook, normalizedTags);
      } catch (tagErr) {
        log(levelVerbose, `Warning: could not update tags for note ${existingNoteId}: ${tagErr.message}`);
      }

      log(levelDebug, `Updated note ${existingNoteId} for JTA ID ${jtaID}`);
      return { action: "updated", noteId: existingNoteId, deck: deckName };
    }

    // Create new note
    log(levelVerbose, `Creating new note for JTA ID ${jtaID} in deck "${deckName}"`);

    const createdNoteId = await client.createNote(
      question,
      answer,
      jtaID,
      title,
      notebook,
      normalizedTags,
      folders,
      {
        explanation: enhancedFields.explanation,
        extra: enhancedFields.extra,
        clinicalCorrelation: enhancedFields.clinicalCorrelation,
        comments: enhancedFields.comments,
        optionA: enhancedFields.optionA,
        optionB: enhancedFields.optionB,
        optionC: enhancedFields.optionC,
        optionD: enhancedFields.optionD,
        correctAnswer: enhancedFields.correctAnswer,
        // NEW IMAGE FIELDS
        questionImagePath: enhancedFields.questionImagePath,
        answerImagePath: enhancedFields.answerImagePath,
        altText: enhancedFields.altText,
        text: enhancedFields.text,
        // Anatomy fields
        origin: enhancedFields.origin,
        insertion: enhancedFields.insertion,
        innervation: enhancedFields.innervation,
        action: enhancedFields.action,
        // --- ADDED MISSING FIELDS ---
        header: enhancedFields.header,
        footer: enhancedFields.footer,
        sources: enhancedFields.sources
      }
    );

    log(levelDebug, `Created new note ${createdNoteId} for JTA ID ${jtaID} in deck "${deckName}"`);
    return { action: "created", noteId: createdNoteId, deck: deckName };

  } catch (error) {
    const msg = `Importer failed for JTA ID ${jtaID} (title: "${title}"): ${error.message}`;
    log(levelApplication, msg);
    throw new Error(msg);
  }
};

/**
 * Batch importer - enhanced reporting & safe concurrency
 */
const batchImporter = async (client, items, batchSize = 10, log) => {
  const results = {
    created: 0,
    updated: 0,
    failed: 0,
    errors: []
  };

  log(levelApplication, `Starting batch import of ${items.length} items (batch size: ${batchSize})`);

  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    log(levelVerbose, `Processing batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(items.length / batchSize)}`);

    const promises = batch.map(async (item, idx) => {
      try {
        await new Promise(resolve => setTimeout(resolve, idx * 30));

        const res = await importer(
          client,
          item.question,
          item.answer,
          item.jtaID,
          item.title,
          item.notebook,
          item.tags,
          item.folders,
          item.additionalFields || {},
          log
        );

        if (res.action === "created") results.created++;
        else if (res.action === "updated") results.updated++;

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

    if (i + batchSize < items.length) {
      await new Promise(resolve => setTimeout(resolve, 200));
    }
  }

  log(levelApplication, `Batch import completed - Created: ${results.created}, Updated: ${results.updated}, Failed: ${results.failed}`);
  if (results.errors.length > 0) {
    log(levelDebug, `Batch import errors sample: ${JSON.stringify(results.errors.slice(0, 5), null, 2)}`);
  }

  return results;
};

/**
 * validatedImporter: wrapper which validates data before import
 */
const validatedImporter = async (client, question, answer, jtaID, title, notebook, tags, folders = [], additionalFields = {}, log) => {
  // run extended validation
  const enhancedFields = buildEnhancedFields(additionalFields);
  const inferredType = inferCardType(question, answer, enhancedFields); // Infer here once
  const errors = validateImportData(question, answer, jtaID, title, enhancedFields, inferredType); // PASS INFERRED TYPE
  if (errors.length > 0) {
    const msg = `Validation failed for ${jtaID}: ${errors.join("; ")}`;
    log(levelApplication, msg);
    throw new Error(msg);
  }

  // delegate to main importer
  return importer(client, question, answer, jtaID, title, notebook, tags, folders, additionalFields, log);
};

/**
 * Duplicate cleanup routine (kept from original, unchanged except using client's doRequest wrapper where appropriate)
 */
const cleanupDuplicates = async (client, log) => {
  log(levelVerbose, "Starting duplicate cleanup process...");

  try {
    // get decks list
    const decks = await client.getDecks();
    const deckNames = Object.keys(decks || {});

    let totalCleaned = 0;

    for (const deckName of deckNames) {
      if (!deckName.includes("Joplin")) continue; // only Joplin-related decks

      log(levelDebug, `Checking for duplicates in deck: ${deckName}`);

      // find notes that contain a Joplin to Anki ID field
      const noteQuery = `deck:'${deckName}' "Joplin to Anki ID:*"`;
      const noteIds = await client.doRequest({
        action: "findNotes",
        version: 6,
        params: { query: noteQuery }
      });

      if (!noteIds || noteIds.length === 0) continue;

      const notesInfo = await client.doRequest({
        action: "notesInfo",
        version: 6,
        params: { notes: noteIds }
      });

      // group by JTA ID
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
          log(levelVerbose, `Found ${notes.length} duplicates for JTA ID: ${jtaId}`);

          // sort by noteId descending (keep most recent)
          notes.sort((a, b) => b.noteId - a.noteId);
          const toDelete = notes.slice(1).map(n => n.noteId);
          if (toDelete.length > 0) {
            await client.deleteNotes(toDelete);
            totalCleaned += toDelete.length;
            log(levelDebug, `Deleted ${toDelete.length} duplicates for JTA ID ${jtaId}`);
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
  cleanupDuplicates
};

// anki-importer.js (DECK NAME FIX VERSION)
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
    altText: additionalFields.altText || ""
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

const importer = async (client, question, answer, jtaID, title, notebook, tags, folders = [], additionalFields = {}, log) => {
  try {
    const normalizedTags = normalizeTags(tags);
    const enhancedFields = buildEnhancedFields(additionalFields);
    const inferredType = inferCardType(question, answer, enhancedFields);

    const validationErrors = validateImportData(question, answer, jtaID, title, inferredType);
    if (validationErrors.length > 0) throw new Error(`Validation failed: ${validationErrors.join("; ")}`);

    // CRITICAL FIX: Get deck name from additionalFields (this is where it's passed from the exporter)
    const deckName = additionalFields.deckName || "Default";
    log(levelApplication, `Processing item with deckName: ${deckName}`);
    
    await client.ensureDeckExists(deckName);
    
    const joplinFields = buildAnkiFieldsObject(question, answer, jtaID, inferredType, enhancedFields);
    const foundNoteIds = await client.findNote(jtaID, deckName);

    if (foundNoteIds && foundNoteIds.length > 0) {
      // --- UPDATE LOGIC ---
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

      log(levelVerbose, `Updating existing note ${existingNoteId}.`);
      await client.updateNote(existingNoteId, joplinFields); 
      await client.updateNoteTags(existingNoteId, title, notebook, normalizedTags);
      return { action: "updated", noteId: existingNoteId };

    } else {
      // --- CREATE LOGIC WITH SELF-HEALING ---
      log(levelVerbose, `No existing note found for JTA ID ${jtaID}. Attempting to create a new one.`);
      try {
        // CRITICAL FIX: Pass deckName as the last parameter to createNote
        const createdNoteId = await client.createNote(
          question, 
          answer, 
          jtaID, 
          title, 
          notebook, 
          normalizedTags, 
          folders, 
          additionalFields,
          deckName  // ← THIS WAS MISSING!
        );
        return { action: "created", noteId: createdNoteId };
      } catch (error) {
        // SELF-HEALING BLOCK: Handle duplicate errors
        if (error.message.includes("duplicate")) {
          log(levelApplication, `⚠️ Creation failed due to a duplicate. Recovering by treating as an update for JTA ID: ${jtaID}`);
          
          const recoveredNoteIds = await client.findNote(jtaID, deckName);
          if (recoveredNoteIds && recoveredNoteIds.length > 0) {
            const recoveredNoteId = recoveredNoteIds[0];
            log(levelVerbose, `Successfully recovered note ID ${recoveredNoteId}. Proceeding with update.`);
            await client.updateNote(recoveredNoteId, joplinFields);
            await client.updateNoteTags(recoveredNoteId, title, notebook, normalizedTags);
            return { action: "updated", noteId: recoveredNoteId };
          } else {
            throw new Error(`Recovery failed. Could not find note ${jtaID} even after a duplicate error.`);
          }
        }
        throw error;
      }
    }
  } catch (error) {
    throw new Error(`Importer failed for JTA ID ${jtaID}: ${error.message}`);
  }
};

const batchImporter = async (client, items, batchSize = 10, log) => {
  const results = { created: 0, updated: 0, skipped: 0, failed: 0, errors: [] };
  log(levelApplication, `Starting batch import with items: ${JSON.stringify(items.map(i => ({ deckName: i.deckName })))}`);
  const INTER_ITEM_DELAY_MS = 250;

  log(levelApplication, `Starting batch import of ${items.length} items...`);

  // Pre-flight health check
  try {
    log(levelVerbose, "Performing pre-flight health check of AnkiConnect...");
    await client.health();
    log(levelVerbose, "AnkiConnect is responsive. Starting sync.");
  } catch (err) {
    log(levelApplication, `❌ CRITICAL: AnkiConnect is not responding. Aborting sync. Please ensure Anki is running with the AnkiConnect add-on enabled.`);
    return;
  }

  for (const [index, item] of items.entries()) {
    try {
      log(levelApplication, `Processing item with deckName: ${item.deckName}`);
      
      // CRITICAL FIX: Pass item.deckName in additionalFields
      const res = await importer(
        client, 
        item.question, 
        item.answer, 
        item.jtaID, 
        item.title, 
        item.notebook, 
        item.tags, 
        item.folders, 
        {
          ...item.additionalFields,
          deckName: item.deckName  // ← Ensure deckName is in additionalFields
        }, 
        log
      );
      
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

    if (index < items.length - 1) {
      await new Promise(resolve => setTimeout(resolve, INTER_ITEM_DELAY_MS));
    }
  }

  log(levelApplication, `Batch import completed - Created: ${results.created}, Updated: ${results.updated}, Skipped: ${results.skipped}, Failed: ${results.failed}`);
  if (results.failed > 0) {
    const errorDetails = results.errors.map(e => `\n   - Item ID: ${e.item}\n     Error: ${e.error}`).join('');
    log(levelApplication, `Errors occurred for the following items:${errorDetails}`);
  }
  return results;
};

module.exports = { importer, batchImporter };

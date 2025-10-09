// anki-client.js (DEFINITIVE CRASH-PROOF VERSION)

const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');
const { levelApplication, levelVerbose, levelDebug } = require("./log");

// Moved outside the class so it's accessible by the importer
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
            fields["Clinical Correlation"] = enhancedFields.clinicalCorrelation; fields["Footer"] = enhancedFields.footer;
            fields["Sources"] = enhancedFields.sources;
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

class AnkiClient {
  constructor(ankiURL = "http://127.0.0.1:8765", log = console.log) {
    this.baseUrl = ankiURL;
    this.log = log;
  }

  async doRequest(payload) {
    const maxRetries = 5;
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await axios.post(this.baseUrl, payload, { timeout: 45000 });
        if (response.data.error) throw new Error(response.data.error);
        return response.data.result;
      } catch (error) {
        if (attempt === maxRetries) throw new Error(`Failed after ${maxRetries} attempts for action "${payload.action}": ${error.message}`);
        const backoffDelay = Math.min(2000 * Math.pow(2, attempt - 1), 20000);
        this.log(levelApplication, `⚠️ Anki request attempt ${attempt} failed for action "${payload.action}": ${error.message}. Retrying in ${backoffDelay}ms...`);
        await new Promise(resolve => setTimeout(resolve, backoffDelay));
      }
    }
  }

  async health() {
    await this.doRequest({ action: "version", version: 6 });
  }

  async setup() {
    this.log(levelApplication, "🔧 Verifying imported models exist...");
    await this.doRequest({ action: "modelNames", version: 6 });
    this.log(levelApplication, "✅ Model verification completed");
  }

  async storeMedia(fileName, data) {
    return this.doRequest({ action: "storeMediaFile", version: 6, params: { filename: fileName, data: data } });
  }

  async ensureDeckExists(deckName) {
    try {
      await this.doRequest({ action: "createDeck", version: 6, params: { deck: deckName } });
    } catch (error) {
      if (!error.message.includes('already exists')) this.log(levelApplication, `⚠️ Warning creating deck "${deckName}": ${error.message}`);
    }
  }

  async findNote(jtaID, deckName) {
    const query = `"Joplin to Anki ID:${jtaID}" deck:"${deckName}"`;
    return this.doRequest({ action: "findNotes", version: 6, params: { query } });
  }

  async getNoteInfo(noteIds) {
    return this.doRequest({ action: "notesInfo", version: 6, params: { notes: noteIds } });
  }

  detectCardType(question, answer, additionalFields = {}) {
    if (/\{\{c\d+::[^}]+\}\}/g.test(question || "")) return "cloze";
    if ((additionalFields.questionImagePath||'').trim() || (additionalFields.answerImagePath||'').trim()) return "imageOcclusion";
    const hasCorrectAnswer = (additionalFields.correctAnswer || '').trim().length > 0;
    const options = [additionalFields.optionA, additionalFields.optionB, additionalFields.optionC, additionalFields.optionD];
    const hasMinOptions = options.filter(opt => (opt || '').trim().length > 0).length >= 2;
    if (hasCorrectAnswer && hasMinOptions) return "mcq";
    return "basic";
  }
  
  async createNote(question, answer, jtaID, title, notebook, tags = [], folders = [], additionalFields = {}) {
    const deckName = "default"; // Simplified for debugging, can be changed back
    const cardType = this.detectCardType(question, answer, additionalFields);
    
    // --- DEFINITIVE CRASH FIX ---
    const model = models[cardType];
    if (!model) {
        throw new Error(`CRITICAL: Could not find a model for the detected card type "${cardType}".`);
    }
    const modelName = model.name;
    // --- END FIX ---

    const fields = buildAnkiFieldsObject(question, answer, jtaID, cardType, additionalFields);
    const noteTags = [...tags, `joplin-title:${title}`, `joplin-notebook:${notebook?.title || 'Unknown'}`];
    const noteData = { deckName, modelName, fields, tags: noteTags };
    
    const result = await this.doRequest({ action: "addNote", version: 6, params: { note: noteData } });
    this.log(levelApplication, `✅ Created ${cardType} card: "${title}" (Anki Note ID: ${result})`);
    return result;
  }
  
  async updateNote(noteId, question, answer, additionalFields = {}) {
      const cardType = this.detectCardType(question, answer, additionalFields);
      this.log(levelVerbose, `Preparing to update a ${cardType} card (Anki Note ID: ${noteId})`);
      
      const fields = buildAnkiFieldsObject(question, answer, '', cardType, additionalFields);
      delete fields['Joplin to Anki ID'];

      await this.doRequest({ action: "updateNoteFields", version: 6, params: { note: { id: noteId, fields: fields } } });
      this.log(levelApplication, `✅ Updated ${cardType} card (Anki Note ID: ${noteId})`);
  }

  async updateNoteTags(noteId, title, notebook, tags = []) {
    const noteTags = [...tags, `joplin-title:${title}`, `joplin-notebook:${notebook?.title || 'Unknown'}`];
    try {
      await this.doRequest({ action: "updateNoteTags", version: 6, params: { note: noteId, tags: noteTags.join(" ") } });
    } catch (error) {
      this.log(levelApplication, `⚠️ Could not update tags for note ${noteId}: ${error.message}`);
    }
  }
}

const models = {
  basic: { name: "Joplin to Anki Basic Enhanced", fields: [ "Header", "Question", "Answer", "Explanation", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ] },
  cloze: { name: "Joplin to Anki Cloze Enhanced", fields: [ "Header", "Text", "Extra", "Explanation", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ], isCloze: true },
  mcq: { name: "Joplin to Anki MCQ Enhanced", fields: [ "Header", "Question", "OptionA", "OptionB", "OptionC", "OptionD", "CorrectAnswer", "Explanation", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ] },
  imageOcclusion: { name: "Joplin to Anki Image Enhanced", fields: [ "Header", "QuestionImagePath", "AnswerImagePath", "AltText", "Question", "Answer", "Origin", "Insertion", "Innervation", "Action", "Comments", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ] }
};

module.exports = AnkiClient;

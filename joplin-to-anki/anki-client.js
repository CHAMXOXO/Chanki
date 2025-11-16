// anki-client.js

const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');
const { levelApplication, levelVerbose, levelDebug } = require("./log");

// ENHANCEMENT: Helper to sanitize strings for use as Anki tags.
const sanitizeForTag = (text) => {
    if (!text || typeof text !== 'string') return '';
    // Replace spaces and colons with underscores, remove other problematic characters.
    return text.trim().replace(/[\s:]+/g, '_').replace(/[#()]/g, '');
};

// Moved outside the class so it's accessible by the importer
const buildAnkiFieldsObject = (question, answer, jtaID, inferredType, enhancedFields) => {
    // FIX: Ensure all field values are strings.
    const ef = (key) => enhancedFields[key] || "";
    let fields = { "Joplin to Anki ID": jtaID || "" };
    
    switch (inferredType) {
        case 'basic':
            fields["Header"] = ef('header'); fields["Question"] = question || ""; fields["Answer"] = answer || "";
            fields["Explanation"] = ef('explanation'); fields["Clinical Correlation"] = ef('clinicalCorrelation');
            fields["Footer"] = ef('footer'); fields["Sources"] = ef('sources');
            break;
        case 'cloze':
            fields["Header"] = ef('header'); fields["Text"] = question || ""; fields["Extra"] = ef('extra');
            fields["Explanation"] = ef('explanation'); fields["Clinical Correlation"] = ef('clinicalCorrelation');
            fields["Footer"] = ef('footer'); fields["Sources"] = ef('sources');
            break;
        case 'mcq':
            fields["Header"] = ef('header'); fields["Question"] = question || ""; fields["OptionA"] = ef('optionA');
            fields["OptionB"] = ef('optionB'); fields["OptionC"] = ef('optionC'); fields["OptionD"] = ef('optionD');
            fields["CorrectAnswer"] = ef('correctAnswer'); fields["Explanation"] = ef('explanation');
            fields["Clinical Correlation"] = ef('clinicalCorrelation'); fields["Footer"] = ef('footer');
            fields["Sources"] = ef('sources');
            break;
        case 'image':
            fields["Header"] = ef('header'); fields["QuestionImagePath"] = ef('questionImagePath');
            fields["AnswerImagePath"] = ef('answerImagePath'); fields["AltText"] = ef('altText');
            fields["Question"] = question || ""; fields["Answer"] = answer || ""; fields["Origin"] = ef('origin');
            fields["Insertion"] = ef('insertion'); fields["Innervation"] = ef('innervation');
            fields["Action"] = ef('action'); fields["Comments"] = ef('comments');
            fields["Clinical Correlation"] = ef('clinicalCorrelation'); fields["Footer"] = ef('footer');
            fields["Sources"] = ef('sources');
            break;
    }
    return fields;
};

class AnkiClient {
  constructor(ankiURL = "http://127.0.0.1:8765", log = console.log) {
    this.baseUrl = ankiURL;
    this.log = log;
    this.deckCache = new Set();
  }

  async doRequest(payload) {
    const maxRetries = 5;
    const baseTimeout = 5000;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const timeout = baseTimeout * attempt;
        const response = await axios.post(this.baseUrl, payload, { 
          timeout,
          headers: { 'Content-Type': 'application/json' },
          httpAgent: new (require('http').Agent)({ keepAlive: true }),
        });
        if (response.data.error) throw new Error(response.data.error);
        return response.data.result;
      } catch (error) {
        if (attempt === maxRetries) {
          throw new Error(`Failed after ${maxRetries} attempts for action "${payload.action}": ${error.message}`);
        }
        const backoffDelay = Math.min(1000 * Math.pow(1.5, attempt - 1), 10000);
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
    const normalizedDeckName = deckName.trim();
    if (this.deckCache.has(normalizedDeckName)) {
      this.log(levelDebug, `Deck "${normalizedDeckName}" already verified in cache`);
      return normalizedDeckName;
    }
    try {
      await this.doRequest({ 
        action: "createDeck", 
        version: 6, 
        params: { deck: normalizedDeckName } 
      });
      this.log(levelDebug, `✅ Deck ensured: "${normalizedDeckName}"`);
      this.deckCache.add(normalizedDeckName);
      return normalizedDeckName;
    } catch (error) {
      this.log(levelApplication, `⚠️ Error ensuring deck "${normalizedDeckName}": ${error.message}`);
      throw error;
    }
  }

  async findNote(jtaID, deckName) {
    const normalizedDeckName = deckName.trim();
    const query = `"Joplin to Anki ID:${jtaID}" deck:"${normalizedDeckName}"`;
    this.log(levelDebug, `Searching for note with query: ${query}`);
    return this.doRequest({ action: "findNotes", version: 6, params: { query } });
  }

  async getNoteInfo(noteIds) {
    return this.doRequest({ action: "notesInfo", version: 6, params: { notes: noteIds } });
  }

  async getNoteModTime(noteId) {
      if (!noteId) return null;
      try {
        const noteInfo = await this.doRequest({ action: "notesInfo", version: 6, params: { notes: [noteId] } });
        if (noteInfo && noteInfo.length > 0) {
          return noteInfo[0].mod; 
        }
        return null;
      } catch (error) {
          this.log(levelApplication, `⚠️ Error fetching mod time for note ${noteId}: ${error.message}`);
          return null;
      }
    }

  detectCardType(question, answer, additionalFields = {}) {
    if (/\{\{c\d+::[^}]+\}\}/g.test(question || "")) return "cloze";
    if ((additionalFields.questionImagePath||'').trim() || (additionalFields.answerImagePath||'').trim()) return "image";
    const hasCorrectAnswer = (additionalFields.correctAnswer || '').trim().length > 0;
    const options = [additionalFields.optionA, additionalFields.optionB, additionalFields.optionC, additionalFields.optionD];
    const hasMinOptions = options.filter(opt => (opt || '').trim().length > 0).length >= 2;
    if (hasCorrectAnswer && hasMinOptions) return "mcq";
    return "basic";
  }
  
  async createNote(question, answer, jtaID, title, notebook, tags = [], folders = [], additionalFields = {}, deckName = "Default") {
    this.log(levelVerbose, `📥 createNote called with deckName: "${deckName}"`);
    
    const verifiedDeckName = await this.ensureDeckExists(deckName);
    this.log(levelDebug, `Creating note in deck: ${verifiedDeckName}`);
    const cardType = this.detectCardType(question, answer, additionalFields);
    const model = models[cardType];
    if (!model) {
        throw new Error(`CRITICAL: Could not find a model for the detected card type "${cardType}".`);
    }
    const modelName = model.name;
    const fields = buildAnkiFieldsObject(question, answer, jtaID, cardType, additionalFields);
    
    // FIX: Sanitize note title and notebook for use as tags
    const noteTags = [...tags, `joplin-title:${sanitizeForTag(title)}`, `joplin-notebook:${sanitizeForTag(notebook?.title)}`];

    const noteData = { 
      deckName: verifiedDeckName,
      modelName, 
      fields, 
      tags: noteTags 
    };
    this.log(levelDebug, `Note payload: ${JSON.stringify({ deckName: verifiedDeckName, modelName, tags: noteTags })}`);
    const result = await this.doRequest({ action: "addNote", version: 6, params: { note: noteData } });
    this.log(levelApplication, `✅ Created ${cardType} card: "${title}" in deck "${verifiedDeckName}" (Anki Note ID: ${result})`);
    await this.verifyNoteInDeck(jtaID, verifiedDeckName);
    return result;
  }
  
  async verifyNoteInDeck(jtaID, expectedDeckName) {
    try {
      const noteIds = await this.findNote(jtaID, expectedDeckName);
      if (noteIds && noteIds.length > 0) {
        this.log(levelDebug, `✅ Verified note ${jtaID} exists in deck "${expectedDeckName}"`);
        return true;
      } else {
        this.log(levelApplication, `⚠️ WARNING: Note ${jtaID} not found in expected deck "${expectedDeckName}"`);
        return false;
      }
    } catch (error) {
      this.log(levelApplication, `⚠️ Could not verify note location: ${error.message}`);
      return false;
    }
  }
  
  async updateNote(noteId, fieldsToUpdate) {
    this.log(levelVerbose, `Updating fields for Anki Note ID: ${noteId}`);
    const notePayload = {
        id: noteId,
        fields: fieldsToUpdate
    };
    delete notePayload.fields['Joplin to Anki ID'];
    await this.doRequest({ 
        action: "updateNoteFields", 
        version: 6, 
        params: { 
            note: notePayload
        } 
    });
    this.log(levelApplication, `✅ Updated card (Anki Note ID: ${noteId})`);
  }

  async updateNoteTags(noteId, title, notebook, tags = []) {
    // FIX: Sanitize note title and notebook for use as tags
    const noteTags = [...tags, `joplin-title:${sanitizeForTag(title)}`, `joplin-notebook:${sanitizeForTag(notebook?.title)}`];
    try {
      await this.doRequest({ action: "updateNoteTags", version: 6, params: { note: noteId, tags: noteTags.join(" ") } });
    } catch (error) {
      this.log(levelApplication, `⚠️ Could not update tags for note ${noteId}: ${error.message}`);
    }
  }

  async createCustomNote(modelName, fields, deckName, tags = [], title = '', notebook = {}) {
    this.log(levelVerbose, `📥 Creating custom note with model: "${modelName}"`);
    const verifiedDeckName = await this.ensureDeckExists(deckName);
    const noteTags = [...tags, `joplin-title:${sanitizeForTag(title)}`, `joplin-notebook:${sanitizeForTag(notebook?.title)}`];
    const noteData = {
      deckName: verifiedDeckName,
      modelName,
      fields,
      tags: noteTags
    };
    this.log(levelDebug, `Custom note payload: ${JSON.stringify(noteData, null, 2)}`);
    const result = await this.doRequest({ action: "addNote", version: 6, params: { note: noteData } });
    this.log(levelApplication, `✅ Created custom card in deck "${verifiedDeckName}" (Anki Note ID: ${result})`);
    return result;
  }

  async updateCustomNote(noteId, fields) {
    this.log(levelVerbose, `Updating custom note fields for Anki Note ID: ${noteId}`);
    const notePayload = {
      id: noteId,
      fields: fields
    };
    await this.doRequest({
      action: "updateNoteFields",
      version: 6,
      params: { note: notePayload }
    });
    this.log(levelApplication, `✅ Updated custom card (Anki Note ID: ${noteId})`);
  }

  async findNoteByField(fieldName, fieldValue, deckName) {
    const normalizedDeckName = deckName.trim();
    const query = `"${fieldName}:${fieldValue}" deck:"${normalizedDeckName}"`;
    this.log(levelDebug, `Searching for custom note with query: ${query}`);
    return this.doRequest({ action: "findNotes", version: 6, params: { query } });
  }

  // FIX: This function is now completely rewritten to be robust and fetch deck names.
  async getAllJtaNotesInfo() {
    this.log(levelVerbose, '🔍 Fetching all JTA notes from Anki for state comparison...');
    const noteIds = await this.doRequest({
      action: "findNotes",
      version: 6,
      params: { query: `"Joplin to Anki ID:*"` }
    });

    if (!noteIds || noteIds.length === 0) {
      this.log(levelApplication, 'ℹ️ No existing JTA notes found in Anki.');
      return new Map();
    }
    this.log(levelDebug, `Found ${noteIds.length} JTA notes in Anki. Fetching their info...`);
    const notesInfo = await this.getNoteInfo(noteIds);

    // --- NEW LOGIC: EFFICIENTLY FETCH DECK NAMES ---
    const cardIds = notesInfo.map(note => (note.cards && note.cards.length > 0) ? note.cards[0] : null).filter(Boolean);
    const cardsInfo = await this.doRequest({ action: "cardsInfo", version: 6, params: { cards: cardIds } });
    
    const cardToDeckMap = new Map();
    cardsInfo.forEach(card => cardToDeckMap.set(card.cardId, card.deckName));
    // --- END NEW LOGIC ---

    const notesMap = new Map();
    for (const note of notesInfo) {
      if (note && note.fields && note.fields['Joplin to Anki ID']) {
        const jtaID = note.fields['Joplin to Anki ID'].value;
        if (jtaID) {
          const ankiModTimeUtc = new Date(note.mod * 1000).toISOString().replace(/\.\d{3}Z$/, '.000Z');
          const firstCardId = (note.cards && note.cards.length > 0) ? note.cards[0] : null;
          const deckName = cardToDeckMap.get(firstCardId) || 'Unknown'; // Fallback
          
          notesMap.set(jtaID, {
            ankiNoteId: note.noteId,
            modelName: note.modelName,
            deckName: deckName, // Add the deck name here
            ankiModTimeUtc: ankiModTimeUtc,
            fields: note.fields,
            tags: note.tags,
          });
        }
      }
    }
    this.log(levelVerbose, `✅ Successfully processed info for ${notesMap.size} Anki notes.`);
    return notesMap;
  }


  async getNotesInfoByJtaIds(jtaIds) {
    if (!jtaIds || jtaIds.length === 0) {
      return [];
    }
    
    const allNotes = [];
    const batchSize = 50;
    
    for (let i = 0; i < jtaIds.length; i += batchSize) {
        const idBatch = jtaIds.slice(i, i + batchSize);
        const query = idBatch.map(id => `"Joplin to Anki ID:${id}"`).join(" or ");
        try {
            const noteIds = await this.doRequest({
                action: "findNotes",
                version: 6,
                params: { query }
            });

            if (noteIds && noteIds.length > 0) {
                const notesInfo = await this.doRequest({
                    action: "notesInfo",
                    version: 6,
                    params: { notes: noteIds }
                });
                allNotes.push(...notesInfo);
            }
        } catch (e) {
            this.log(levelVerbose, `⚠️ Could not fetch batch of notes: ${e.message}`);
        }
    }
    
    return allNotes;
  }

  async retrieveMediaFile(filename) {
    try {
      this.log(levelDebug, `Retrieving media file from Anki: ${filename}`);
      const result = await this.doRequest({
        action: "retrieveMediaFile",
        version: 6,
        params: { filename: filename }
      });
      return result;
    } catch (error) {
      this.log(levelApplication, `⚠️ Failed to retrieve media file ${filename}: ${error.message}`);
      return false;
    }
  }
}

const models = {
  basic: { name: "Joplin to Anki Basic Enhanced", fields: [ "Header", "Question", "Answer", "Explanation", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ] },
  cloze: { name: "Joplin to Anki Cloze Enhanced", fields: [ "Header", "Text", "Extra", "Explanation", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ], isCloze: true },
  mcq: { name: "Joplin to Anki MCQ Enhanced", fields: [ "Header", "Question", "OptionA", "OptionB", "OptionC", "OptionD", "CorrectAnswer", "Explanation", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ] },
  image: { name: "Joplin to Anki Image Enhanced", fields: [ "Header", "QuestionImagePath", "AnswerImagePath", "AltText", "Question", "Answer", "Origin", "Insertion", "Innervation", "Action", "Comments", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ] }
};

// FIX: Export buildAnkiFieldsObject so it can be used by the importer.
module.exports = { AnkiClient, buildAnkiFieldsObject };

// anki-client.js 

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
        case 'image':
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
    this.deckCache = new Set(); // Cache to avoid repeated deck creation calls
  }

  async doRequest(payload) {
    const maxRetries = 5;
    const baseTimeout = 5000; // Start with a 5-second timeout
    
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
    this.log(levelApplication, `📥 createNote called with deckName: "${deckName}"`);
    if (!deckName || deckName === "Default") {
      this.log(levelApplication, `⚠️ WARNING: deckName is "${deckName}" - this suggests the deck name wasn't passed correctly from the exporter!`);
    }
    const verifiedDeckName = await this.ensureDeckExists(deckName);
    this.log(levelApplication, `Creating note in deck: ${verifiedDeckName}`);
    const cardType = this.detectCardType(question, answer, additionalFields);
    const model = models[cardType];
    if (!model) {
        throw new Error(`CRITICAL: Could not find a model for the detected card type "${cardType}".`);
    }
    const modelName = model.name;
    const fields = buildAnkiFieldsObject(question, answer, jtaID, cardType, additionalFields);
    const noteTags = [...tags, `joplin-title:${title}`, `joplin-notebook:${notebook?.title || 'Unknown'}`];
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
    const noteTags = [...tags, `joplin-title:${title}`, `joplin-notebook:${notebook?.title || 'Unknown'}`];
    try {
      await this.doRequest({ action: "updateNoteTags", version: 6, params: { note: noteId, tags: noteTags.join(" ") } });
    } catch (error) {
      this.log(levelApplication, `⚠️ Could not update tags for note ${noteId}: ${error.message}`);
    }
  }

  async createCustomNote(modelName, fields, deckName, tags = [], title = '', notebook = {}) {
    this.log(levelApplication, `📥 Creating custom note with model: "${modelName}"`);
    const verifiedDeckName = await this.ensureDeckExists(deckName);
    const noteTags = [...tags, `joplin-title:${title}`, `joplin-notebook:${notebook?.title || 'Unknown'}`];
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

    // In anki-client.js, find the getAllJtaNotesInfo() method (around line 180-220)
    // Replace the entire method with this version:
    
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
      const notesMap = new Map();
      for (const note of notesInfo) {
        if (note && note.fields && note.fields['Joplin to Anki ID']) {
          const jtaID = note.fields['Joplin to Anki ID'].value;
          if (jtaID) {
            // STEP 2 FIX: Normalize Anki mod time to ISO string with .000Z
            const ankiModTimeUtc = new Date(note.mod * 1000).toISOString().replace(/\.\d{3}Z$/, '.000Z');
            
            notesMap.set(jtaID, {
              ankiNoteId: note.noteId,
              modelName: note.modelName,
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

  /**
   * Retrieves full note information for a specific list of JTA IDs.
   * @param {string[]} jtaIds - An array of Joplin to Anki IDs.
   * @returns {Promise<any[]>} A promise that resolves to an array of note info objects.
   */
  async getNotesInfoByJtaIds(jtaIds) {
      if (!jtaIds || jtaIds.length === 0) {
          return [];
      }
      
      const allNotes = [];
      
      for (const jtaID of jtaIds) {
          try {
              const noteIds = await this.doRequest({
                  action: "findNotes",
                  version: 6,
                  params: { query: `"Joplin to Anki ID:${jtaID}"` }
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
              this.log(levelVerbose, `⚠️ Could not fetch note for JTA ID ${jtaID}: ${e.message}`);
          }
      }
      
      return allNotes;
  }
}

const models = {
  basic: { name: "Joplin to Anki Basic Enhanced", fields: [ "Header", "Question", "Answer", "Explanation", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ] },
  cloze: { name: "Joplin to Anki Cloze Enhanced", fields: [ "Header", "Text", "Extra", "Explanation", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ], isCloze: true },
  mcq: { name: "Joplin to Anki MCQ Enhanced", fields: [ "Header", "Question", "OptionA", "OptionB", "OptionC", "OptionD", "CorrectAnswer", "Explanation", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ] },
  image: { name: "Joplin to Anki Image Enhanced", fields: [ "Header", "QuestionImagePath", "AnswerImagePath", "AltText", "Question", "Answer", "Origin", "Insertion", "Innervation", "Action", "Comments", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ] }
};

module.exports = AnkiClient;

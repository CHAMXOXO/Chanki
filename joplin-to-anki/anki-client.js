const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');
const { levelApplication, levelVerbose, levelDebug } = require("./log");

const sanitizeForTag = (text) => {
    if (!text || typeof text !== 'string') return '';
    // Replace spaces/colons with underscores, remove #/(), but KEEP emojis/unicode
    return text.trim()
               .replace(/[\s:]+/g, '_') 
               .replace(/[#()]/g, ''); 
};

const buildAnkiFieldsObject = (question, answer, jtaID, inferredType, enhancedFields) => {
    const ef = (key) => enhancedFields[key] || "";
    let fields = { "Joplin to Anki ID": jtaID || "" };
    
    // Core Hardcoded Basic Fallback
    fields["Header"] = ef('header');
    fields["Question"] = question || "";
    fields["Answer"] = answer || "";
    fields["Explanation"] = ef('explanation');
    fields["Clinical Correlation"] = ef('clinicalCorrelation');
    fields["Footer"] = ef('footer');
    fields["Sources"] = ef('sources');

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
        if (attempt === maxRetries) throw new Error(`Failed after ${maxRetries} attempts: ${error.message}`);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  }

  async health() { await this.doRequest({ action: "version", version: 6 }); }

  async setup() {
    this.log(levelApplication, "🔧 Verifying imported models exist...");
    await this.doRequest({ action: "modelNames", version: 6 });
  }

  async storeMedia(fileName, data) {
    return this.doRequest({ action: "storeMediaFile", version: 6, params: { filename: fileName, data: data } });
  }

  async ensureDeckExists(deckName) {
    const normalizedDeckName = deckName.trim();
    if (this.deckCache.has(normalizedDeckName)) return normalizedDeckName;
    await this.doRequest({ action: "createDeck", version: 6, params: { deck: normalizedDeckName } });
    this.deckCache.add(normalizedDeckName);
    return normalizedDeckName;
  }

  async createNote(question, answer, jtaID, title, notebook, tags = [], folders = [], additionalFields = {}, deckName = "Default") {
    // Core Hardcoded Creation (Only Basic)
    const verifiedDeckName = await this.ensureDeckExists(deckName);
    const modelName = "Joplin to Anki Basic Enhanced";
    const fields = buildAnkiFieldsObject(question, answer, jtaID, 'basic', additionalFields);
    const noteTags = [...tags, `joplin-title:${sanitizeForTag(title)}`, `joplin-notebook:${sanitizeForTag(notebook?.title)}`];
    
    const noteData = { deckName: verifiedDeckName, modelName, fields, tags: noteTags };
    return await this.doRequest({ action: "addNote", version: 6, params: { note: noteData } });
  }
  
  async createCustomNote(modelName, fields, deckName, tags = [], title = '', notebook = {}) {
    this.log(levelVerbose, `📥 Creating custom note: "${modelName}"`);
    const verifiedDeckName = await this.ensureDeckExists(deckName);
    const noteTags = [...tags, `joplin-title:${sanitizeForTag(title)}`, `joplin-notebook:${sanitizeForTag(notebook?.title)}`];
    const noteData = { deckName: verifiedDeckName, modelName, fields, tags: noteTags };
    return await this.doRequest({ action: "addNote", version: 6, params: { note: noteData } });
  }

  async updateCustomNote(noteId, fields) {
    const notePayload = { id: noteId, fields: fields };
    return await this.doRequest({ action: "updateNoteFields", version: 6, params: { note: notePayload } });
  }
  
  async updateNote(noteId, fieldsToUpdate) {
    const notePayload = { id: noteId, fields: fieldsToUpdate };
    delete notePayload.fields['Joplin to Anki ID'];
    return await this.doRequest({ action: "updateNoteFields", version: 6, params: { note: notePayload } });
  }

  async updateNoteTags(noteId, title, notebook, tags = []) {
    const noteTags = [...tags, `joplin-title:${sanitizeForTag(title)}`, `joplin-notebook:${sanitizeForTag(notebook?.title)}`];
    try {
      await this.doRequest({ action: "updateNoteTags", version: 6, params: { note: noteId, tags: noteTags.join(" ") } });
    } catch (error) {}
  }

  async getAllJtaNotesInfo() {
    const noteIds = await this.doRequest({ action: "findNotes", version: 6, params: { query: `"Joplin to Anki ID:*"` } });
    if (!noteIds || noteIds.length === 0) return new Map();
    const notesInfo = await this.doRequest({ action: "notesInfo", version: 6, params: { notes: noteIds } });
    
    // Get Card info for Deck Names
    const cardIds = notesInfo.map(note => (note.cards && note.cards.length > 0) ? note.cards[0] : null).filter(Boolean);
    const cardsInfo = await this.doRequest({ action: "cardsInfo", version: 6, params: { cards: cardIds } });
    const cardToDeckMap = new Map();
    cardsInfo.forEach(card => cardToDeckMap.set(card.cardId, card.deckName));

    const notesMap = new Map();
    for (const note of notesInfo) {
      if (note && note.fields && note.fields['Joplin to Anki ID']) {
        const jtaID = note.fields['Joplin to Anki ID'].value;
        if (jtaID) {
          const firstCardId = (note.cards && note.cards.length > 0) ? note.cards[0] : null;
          const deckName = cardToDeckMap.get(firstCardId) || 'Default';
          notesMap.set(jtaID, {
            ankiNoteId: note.noteId,
            modelName: note.modelName,
            deckName: deckName,
            ankiModTimeUtc: new Date(note.mod * 1000).toISOString().replace(/\.\d{3}Z$/, '.000Z'),
            fields: note.fields,
            tags: note.tags,
          });
        }
      }
    }
    return notesMap;
  }

  async getNotesInfoByJtaIds(jtaIds) {
    if (!jtaIds || jtaIds.length === 0) return [];
    const query = jtaIds.map(id => `"Joplin to Anki ID:${id}"`).join(" or ");
    try {
        const noteIds = await this.doRequest({ action: "findNotes", version: 6, params: { query } });
        if (noteIds && noteIds.length > 0) {
            return await this.doRequest({ action: "notesInfo", version: 6, params: { notes: noteIds } });
        }
    } catch (e) {}
    return [];
  }

  async retrieveMediaFile(filename) {
    try {
      return await this.doRequest({ action: "retrieveMediaFile", version: 6, params: { filename: filename } });
    } catch (error) { return false; }
  }
  
  detectCardType(question, answer, additionalFields = {}) { return "basic"; }
}

module.exports = { AnkiClient, buildAnkiFieldsObject };

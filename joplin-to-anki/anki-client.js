// anki-client.js (FINAL INTELLIGENT UPDATE VERSION)

const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');
const { levelApplication, levelVerbose, levelDebug } = require("./log");
const { buildAnkiFieldsObject } = require('./anki-importer'); // Import the helper

class AnkiClient {
  constructor(ankiURL = "http://127.0.0.1:8765", log = console.log) {
    this.baseUrl = ankiURL;
    this.log = log;
    this.log(levelDebug, "AnkiClient initialized.");
  }

  async doRequest(payload) {
    const maxRetries = 5;
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        this.log(levelDebug, `Attempt ${attempt} for AnkiConnect action: ${payload.action}`);
        const response = await axios.post(this.baseUrl, payload, { timeout: 45000 });
        if (response.data.error) throw new Error(response.data.error);
        this.log(levelDebug, `AnkiConnect action "${payload.action}" successful on attempt ${attempt}.`);
        return response.data.result;
      } catch (error) {
        const isNetworkError = error.code === 'ECONNRESET' || error.code === 'EPIPE' || error.code === 'ECONNABORTED' || error.message.includes('socket hang up') || error.message.includes('timeout');
        if (attempt === maxRetries) {
          this.log(levelApplication, `❌ Failed after ${maxRetries} attempts for action "${payload.action}": ${error.message}`);
          throw new Error(`Failed after ${maxRetries} attempts for action "${payload.action}": ${error.message}`);
        }
        const backoffDelay = Math.min(2000 * Math.pow(2, attempt - 1), 20000);
        const retryMessage = isNetworkError ? `Retrying in ${backoffDelay}ms...` : `Retrying...`;
        this.log(levelApplication, `⚠️ Anki request attempt ${attempt} failed for action "${payload.action}": ${error.message}. ${retryMessage}`);
        await new Promise(resolve => setTimeout(resolve, backoffDelay));
      }
    }
  }

  async health() {
    return this.healthCheck();
  }

  async healthCheck() {
    try {
      const result = await this.doRequest({ action: "version", version: 6 });
      this.log(levelDebug, `Anki health check successful. Version: ${result}`);
      return { healthy: true, version: result };
    } catch (error) {
      this.log(levelApplication, `❌ Anki connection failed during health check: ${error.message}`);
      throw new Error(`Anki connection failed: ${error.message}`);
    }
  }

  async setup() {
    try {
      this.log(levelApplication, "🔧 Verifying imported models exist...");
      const modelNames = await this.doRequest({ action: "modelNames", version: 6 });
      const expectedModels = [
        "Joplin to Anki Basic Enhanced", "Joplin to Anki Cloze Enhanced",
        "Joplin to Anki MCQ Enhanced", "Joplin to Anki Image Enhanced"
      ];
      for (const modelName of expectedModels) {
        if (modelNames.includes(modelName)) {
          this.log(levelApplication, `✅ Found model: ${modelName}`);
        } else {
          this.log(levelApplication, `⚠️ Missing model: ${modelName}. Please ensure the .apkg with models is imported.`);
        }
      }
      this.log(levelApplication, "✅ Model verification completed");
    } catch (error) {
      this.log(levelApplication, `⚠️ Model verification error: ${error.message}. Continuing sync, but cards might fail.`);
    }
  }

  async storeMedia(fileName, data) {
    return this.doRequest({ action: "storeMediaFile", version: 6, params: { filename: fileName, data: data } });
  }

  async processImagePath(imagePath) {
    if (!imagePath || !imagePath.trim()) return '';
    if (!imagePath.includes('/') && !imagePath.includes('\\')) return imagePath;
    if (imagePath.startsWith(':/')) return imagePath;
    try {
      const expandedPath = imagePath.replace(/^~/, process.env.HOME || process.env.USERPROFILE);
      const fileName = path.basename(expandedPath);
      await fs.access(expandedPath);
      const fileData = await fs.readFile(expandedPath);
      const base64Data = fileData.toString('base64');
      await this.storeMedia(fileName, base64Data);
      this.log(levelVerbose, `✓ Copied to Anki media: ${fileName}`);
      return fileName;
    } catch (error) {
      this.log(levelApplication, `⚠️ Failed to process image ${imagePath}: ${error.message}`);
      return imagePath;
    }
  }

  async createDeck(deckName) {
    return this.doRequest({ action: "createDeck", version: 6, params: { deck: deckName } });
  }

  async getDecks() {
    return this.doRequest({ action: "deckNames", version: 6 });
  }

  async ensureDeckExists(deckName) {
    try {
      await this.createDeck(deckName);
      this.log(levelVerbose, `Created new deck: "${deckName}"`);
    } catch (error) {
      if (!error.message.includes('already exists')) {
        this.log(levelApplication, `⚠️ Warning creating deck "${deckName}": ${error.message}`);
      }
    }
  }

  async findNotes(query) {
    return this.doRequest({ action: "findNotes", version: 6, params: { query } });
  }

  async findNote(jtaID, deckName) {
    const query = `"Joplin to Anki ID:${jtaID}" deck:"${deckName}"`;
    return this.findNotes(query);
  }

  async getNoteInfo(noteIds) {
    return this.doRequest({ action: "notesInfo", version: 6, params: { notes: noteIds } });
  }

  async addNote(note) {
    return this.doRequest({ action: "addNote", version: 6, params: { note } });
  }

  async updateNoteFields(note) {
    return this.doRequest({ action: "updateNoteFields", version: 6, params: { note } });
  }

  async deleteNotes(noteIds) {
    return this.doRequest({ action: "deleteNotes", version: 6, params: { notes: noteIds } });
  }

  determineDeckName(tags = [], folders = [], notebookId) {
    let deckName = null;
    let subdeckName = null;
    for (const tag of tags) {
      const tagStr = (tag || "").toString().toLowerCase();
      if (tagStr.startsWith('deck::')) deckName = tag.substring(6).trim();
      else if (tagStr.startsWith('subdeck::')) subdeckName = tag.substring(9).trim();
    }
    if (deckName) return subdeckName ? `${deckName}::${subdeckName}` : deckName;
    if (folders && folders.length > 0 && notebookId) {
      const notebookHierarchy = this.buildNotebookHierarchy(folders, notebookId);
      if (notebookHierarchy.length > 0) return notebookHierarchy.join('::');
    }
    return "Joplin to Anki";
  }

  buildNotebookHierarchy(folders = [], currentNotebookId) {
    if (!currentNotebookId || !folders.length) return [];
    const hierarchy = [];
    let currentId = currentNotebookId;
    while (currentId) {
      const folder = folders.find(f => f.id === currentId);
      if (folder) {
        hierarchy.unshift(folder.title);
        currentId = folder.parent_id;
      } else break;
    }
    return hierarchy;
  }

  detectCardType(question, answer, additionalFields = {}) {
    const combinedText = (question || "") + (answer || "");
    if (/\{\{c\d+::[^}]+\}\}/g.test(combinedText)) return "cloze";
    const hasImage = (additionalFields.questionImagePath && additionalFields.questionImagePath.trim() !== '') || (additionalFields.answerImagePath && additionalFields.answerImagePath.trim() !== '');
    if (hasImage) return "imageOcclusion";
    const hasMcqFields = [additionalFields.optionA, additionalFields.optionB, additionalFields.optionC, additionalFields.optionD].some(opt => opt && opt.trim() !== '') || (additionalFields.correctAnswer && additionalFields.correctAnswer.trim() !== '');
    if (hasMcqFields) return "mcq";
    return "basic";
  }

  async createNote(question, answer, jtaID, title, notebook, tags = [], folders = [], additionalFields = {}) {
    const deckName = this.determineDeckName(tags, folders, notebook?.id);
    const cardType = this.detectCardType(question, answer, additionalFields);
    const modelName = models[cardType].name;
    const fields = buildAnkiFieldsObject(question, answer, jtaID, cardType, additionalFields);
    const noteTags = [...tags, `joplin-title:${title}`, `joplin-notebook:${notebook?.title || 'Unknown'}`];
    const noteData = { deckName, modelName, fields, tags: noteTags };
    const result = await this.addNote(noteData);
    this.log(levelApplication, `✅ Created ${cardType} card: "${title}" (Anki Note ID: ${result})`);
    return result;
  }

  async updateNote(noteId, question, answer, additionalFields = {}) {
    const cardType = this.detectCardType(question, answer, additionalFields);
    this.log(levelVerbose, `Preparing to update a ${cardType} card (Anki Note ID: ${noteId})`);
    
    // Use the helper to build the full fields object
    const fields = buildAnkiFieldsObject(question, answer, '', cardType, additionalFields);
    
    // We don't need to update the ID field, so remove it
    delete fields['Joplin to Anki ID'];

    this.log(levelDebug, `Final Note Data for Anki (update):
      Note ID: ${noteId}
      Fields: ${JSON.stringify(fields, null, 2)}
    `);

    await this.updateNoteFields({
      id: noteId,
      fields: fields
    });

    this.log(levelApplication, `✅ Updated ${cardType} card (Anki Note ID: ${noteId})`);
  }

  async updateNoteTags(noteId, title, notebook, tags = []) {
    const noteTags = [...tags, `joplin-title:${title}`, `joplin-notebook:${notebook?.title || 'Unknown'}`];
    try {
      await this.doRequest({ action: "updateNoteTags", version: 6, params: { note: noteId, tags: noteTags.join(" ") } });
      this.log(levelVerbose, `Updated tags for note ${noteId}.`);
    } catch (error) {
      this.log(levelApplication, `⚠️ Could not update tags for note ${noteId}: ${error.message}`);
    }
  }

  async canAddNotes(notes) {
    return this.doRequest({ action: "canAddNotes", version: 6, params: { notes } });
  }

  async createModel(modelType = 'basic') {
    const model = models[modelType];
    if (!model) throw new Error(`Unknown model type: ${modelType}`);
    const params = { modelName: model.name, inOrderFields: model.fields, cardTemplates: model.cardTemplates };
    if (model.isCloze) params.isCloze = true;
    try {
      await this.doRequest({ action: "createModel", version: 6, params });
      this.log(levelApplication, `✅ Successfully created Anki model: "${model.name}"`);
    } catch (error) {
      if (error.message.includes('already exists')) {
        this.log(levelApplication, `⚠️ Model "${model.name}" already exists. Skipping creation.`);
      } else {
        throw error;
      }
    }
  }
}

const models = { /* This object containing your note type definitions remains the same */ };

module.exports = AnkiClient;

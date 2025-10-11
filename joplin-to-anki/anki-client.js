// anki-client.js (ENHANCED DECK HANDLING VERSION)

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
    this.deckCache = new Set(); // Cache to avoid repeated deck creation calls
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

  /**
   * Enhanced deck creation with validation
   */
  async ensureDeckExists(deckName) {
    // Normalize deck name (trim whitespace)
    const normalizedDeckName = deckName.trim();
    
    // Check cache first
    if (this.deckCache.has(normalizedDeckName)) {
      this.log(levelDebug, `Deck "${normalizedDeckName}" already verified in cache`);
      return normalizedDeckName;
    }

    try {
      // Create the deck (this is idempotent - won't error if deck exists)
      await this.doRequest({ 
        action: "createDeck", 
        version: 6, 
        params: { deck: normalizedDeckName } 
      });
      
      this.log(levelDebug, `✅ Deck ensured: "${normalizedDeckName}"`);
      
      // Add to cache
      this.deckCache.add(normalizedDeckName);
      
      return normalizedDeckName;
    } catch (error) {
      this.log(levelApplication, `⚠️ Error ensuring deck "${normalizedDeckName}": ${error.message}`);
      throw error;
    }
  }

  /**
   * Verify that a note actually exists in the specified deck
   */
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
    if ((additionalFields.questionImagePath||'').trim() || (additionalFields.answerImagePath||'').trim()) return "imageOcclusion";
    const hasCorrectAnswer = (additionalFields.correctAnswer || '').trim().length > 0;
    const options = [additionalFields.optionA, additionalFields.optionB, additionalFields.optionC, additionalFields.optionD];
    const hasMinOptions = options.filter(opt => (opt || '').trim().length > 0).length >= 2;
    if (hasCorrectAnswer && hasMinOptions) return "mcq";
    return "basic";
  }
  
  async createNote(question, answer, jtaID, title, notebook, tags = [], folders = [], additionalFields = {}, deckName = "Default") {
    // CRITICAL: Log what deck name we received
    this.log(levelApplication, `📥 createNote called with deckName: "${deckName}"`);
    
    // Check if deckName is actually set and not just the default
    if (!deckName || deckName === "Default") {
      this.log(levelApplication, `⚠️ WARNING: deckName is "${deckName}" - this suggests the deck name wasn't passed correctly from the exporter!`);
    }
    
    // CRITICAL: Ensure deck exists and get normalized name
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
    
    // CRITICAL: Use the verified deck name in the note data
    const noteData = { 
      deckName: verifiedDeckName,  // Use verified name
      modelName, 
      fields, 
      tags: noteTags 
    };
    
    this.log(levelDebug, `Note payload: ${JSON.stringify({ deckName: verifiedDeckName, modelName, tags: noteTags })}`);
    
    const result = await this.doRequest({ action: "addNote", version: 6, params: { note: noteData } });
    this.log(levelApplication, `✅ Created ${cardType} card: "${title}" in deck "${verifiedDeckName}" (Anki Note ID: ${result})`);
    
    // Verify the note was created in the correct deck
    await this.verifyNoteInDeck(jtaID, verifiedDeckName);
    
    return result;
  }
  
  /**
   * Verify that a note exists in the expected deck
   */
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
    
    // Never update the unique ID field
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
}

const models = {
  basic: { name: "Joplin to Anki Basic Enhanced", fields: [ "Header", "Question", "Answer", "Explanation", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ] },
  cloze: { name: "Joplin to Anki Cloze Enhanced", fields: [ "Header", "Text", "Extra", "Explanation", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ], isCloze: true },
  mcq: { name: "Joplin to Anki MCQ Enhanced", fields: [ "Header", "Question", "OptionA", "OptionB", "OptionC", "OptionD", "CorrectAnswer", "Explanation", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ] },
  imageOcclusion: { name: "Joplin to Anki Image Enhanced", fields: [ "Header", "QuestionImagePath", "AnswerImagePath", "AltText", "Question", "Answer", "Origin", "Insertion", "Innervation", "Action", "Comments", "Clinical Correlation", "Footer", "Sources", "Joplin to Anki ID" ] }
};

module.exports = AnkiClient;

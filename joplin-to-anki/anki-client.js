// anki-client.js - Revised Version

const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');
const { levelApplication, levelVerbose, levelDebug } = require("./log"); // Assuming log levels are defined here

class AnkiClient {
  constructor(ankiURL = "http://127.0.0.1:8765", log = console.log) {
    this.baseUrl = ankiURL;
    this.maxRetries = 3;
    this.retryDelay = 3000;
    this.log = log;
    this.log(levelDebug, "AnkiClient initialized.");
  }

  // anki-client.js
  
    async doRequest(payload) {
      // --- START OF MODIFICATIONS ---
      const maxRetries = 5; // MODIFIED: Increased from 3 to 5 retries
      
      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          this.log(levelDebug, `Attempt ${attempt} for AnkiConnect action: ${payload.action}`);
          
          // MODIFIED: Added a specific timeout to the request
          const response = await axios.post(this.baseUrl, payload, { timeout: 45000 }); // 45-second timeout
  
          if (response.data.error) {
            throw new Error(response.data.error);
          }
          
          this.log(levelDebug, `AnkiConnect action "${payload.action}" successful on attempt ${attempt}.`);
          return response.data.result;
  
        } catch (error) {
          // MODIFIED: Refined error message checking for network issues
          const isNetworkError = error.code === 'ECONNRESET' || 
                                 error.code === 'EPIPE' || 
                                 error.code === 'ECONNABORTED' ||
                                 error.message.includes('socket hang up') ||
                                 error.message.includes('timeout');
  
          if (attempt === maxRetries) {
            this.log(levelApplication, `❌ Failed after ${maxRetries} attempts for action "${payload.action}": ${error.message}`);
            throw new Error(`Failed after ${maxRetries} attempts for action "${payload.action}": ${error.message}`);
          }
  
          // MODIFIED: Implemented exponential backoff for retries
          const backoffDelay = Math.min(2000 * Math.pow(2, attempt - 1), 20000); // Starts at 2s, doubles, max 20s
          const retryMessage = isNetworkError ? `Retrying in ${backoffDelay}ms...` : `Retrying...`;
  
          this.log(levelApplication, `⚠️ Anki request attempt ${attempt} failed for action "${payload.action}": ${error.message}. ${retryMessage}`);
          await new Promise(resolve => setTimeout(resolve, backoffDelay));
        }
      }
      // --- END OF MODIFICATIONS ---
    }

  async health() {
    return this.healthCheck();
  }

  async healthCheck() {
    try {
      const result = await this.doRequest({
        action: "version",
        version: 6
      });
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

      const modelNames = await this.doRequest({
        action: "modelNames",
        version: 6
      });

      const expectedModels = [
        "Joplin to Anki Basic Enhanced",
        "Joplin to Anki Cloze Enhanced",
        "Joplin to Anki MCQ Enhanced",
        "Joplin to Anki Image Enhanced" // Updated name
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
    return this.doRequest({
      action: "storeMediaFile",
      version: 6,
      params: {
        filename: fileName,
        data: data
      }
    });
  }

  async processImagePath(imagePath) {
    if (!imagePath || !imagePath.trim()) {
      return '';
    }

    // If it's already just a filename (no path separators), return as-is
    if (!imagePath.includes('/') && !imagePath.includes('\\')) {
      this.log(levelDebug, `Image already in Anki format: ${imagePath}`);
      return imagePath;
    }

    // If it's a Joplin resource ID (:/resource_id), skip - handled separately
    // The joplin-exporter.js's addResources function should convert these to filenames
    if (imagePath.startsWith(':/')) {
      this.log(levelDebug, `Joplin resource ID detected: ${imagePath}. Should be handled by exporter.`);
      return imagePath; // Return original, exporter should translate it later
    }

    // It's a file path - copy to Anki media
    try {
      // Expand ~ to home directory
      const expandedPath = imagePath.replace(/^~/, process.env.HOME || process.env.USERPROFILE); // Support Windows ~
      const fileName = path.basename(expandedPath);

      this.log(levelVerbose, `Processing external image: ${expandedPath} -> ${fileName}`);

      // Check if file exists
      await fs.access(expandedPath);

      // Read the file
      const fileData = await fs.readFile(expandedPath);
      const base64Data = fileData.toString('base64');

      // Store in Anki via AnkiConnect
      await this.storeMedia(fileName, base64Data);

      this.log(levelVerbose, `✓ Copied to Anki media: ${fileName}`);
      return fileName;

    } catch (error) {
      this.log(levelApplication, `⚠️ Failed to process image ${imagePath}: ${error.message}`);
      return imagePath; // Return original on failure
    }
  }

  async createDeck(deckName) {
    return this.doRequest({
      action: "createDeck",
      version: 6,
      params: { deck: deckName }
    });
  }

  async getDecks() {
    return this.doRequest({
      action: "deckNames",
      version: 6
    });
  }

  async ensureDeckExists(deckName) {
    try {
      await this.createDeck(deckName);
      this.log(levelVerbose, `Created new deck: "${deckName}"`);
    } catch (error) {
      // Deck might already exist, that's fine
      if (!error.message.includes('already exists')) {
        this.log(levelApplication, `⚠️ Warning creating deck "${deckName}": ${error.message}`);
      } else {
        this.log(levelVerbose, `Deck "${deckName}" already exists.`);
      }
    }
  }

  async findNotes(query) {
    return this.doRequest({
      action: "findNotes",
      version: 6,
      params: { query }
    });
  }

  // Find note by JTA ID in specific deck
  async findNote(jtaID, deckName) {
    const query = `"Joplin to Anki ID:${jtaID}" deck:"${deckName}"`;
    this.log(levelDebug, `Searching for note with query: "${query}"`);
    return this.findNotes(query);
  }

  async getNoteInfo(noteIds) {
    return this.doRequest({
      action: "notesInfo",
      version: 6,
      params: { notes: noteIds }
    });
  }

  async addNote(note) {
    return this.doRequest({
      action: "addNote",
      version: 6,
      params: { note }
    });
  }

  async updateNoteFields(note) {
    return this.doRequest({
      action: "updateNoteFields",
      version: 6,
      params: { note }
    });
  }

  async deleteNotes(noteIds) {
    return this.doRequest({
      action: "deleteNotes",
      version: 6,
      params: { notes: noteIds }
    });
  }

  // Determine deck name with fallback hierarchy: tags -> notebooks -> default
  determineDeckName(tags = [], folders = [], notebookId) {
    this.log(levelDebug, `DEBUG determineDeckName called with: tags=${JSON.stringify(tags)}, notebookId=${notebookId}, folders count=${folders ? folders.length : 0}`);

    let deckName = null;
    let subdeckName = null;

    // FIRST: Check for explicit deck:: and subdeck:: tags
    for (const tag of tags) {
      const tagStr = (tag || "").toString().toLowerCase();
      this.log(levelDebug, `DEBUG checking tag: "${tag}" -> normalized: "${tagStr}"`);

      if (tagStr.startsWith('deck::')) {
        deckName = tag.substring(6).trim();
        this.log(levelDebug, `DEBUG found deck from tag: "${deckName}"`);
      } else if (tagStr.startsWith('subdeck::')) {
        subdeckName = tag.substring(9).trim();
        this.log(levelDebug, `DEBUG found subdeck from tag: "${subdeckName}"`);
      }
    }

    // If found deck tags, use them
    if (deckName) {
      const finalDeck = subdeckName ? `${deckName}::${subdeckName}` : deckName;
      this.log(levelDebug, `DEBUG using tag-based deck: "${finalDeck}"`);
      return finalDeck;
    }

    // SECOND: Fallback to notebook hierarchy
    if (folders && folders.length > 0 && notebookId) {
      const notebookHierarchy = this.buildNotebookHierarchy(folders, notebookId);
      if (notebookHierarchy.length > 0) {
        const hierarchyDeck = notebookHierarchy.join('::');
        this.log(levelDebug, `DEBUG using notebook hierarchy: "${hierarchyDeck}"`);
        return hierarchyDeck;
      }
    }

    // THIRD: Default fallback
    this.log(levelDebug, `DEBUG using default deck: "Joplin to Anki"`);
    return "Joplin to Anki";
  }

  // Build notebook hierarchy path
  buildNotebookHierarchy(folders = [], currentNotebookId) {
    if (!currentNotebookId || !folders.length) return [];

    const hierarchy = [];
    let currentId = currentNotebookId;

    // Walk up the folder tree
    while (currentId) {
      const folder = folders.find(f => f.id === currentId);
      if (folder) {
        hierarchy.unshift(folder.title); // Add to beginning
        currentId = folder.parent_id;
      } else {
        break;
      }
    }
    return hierarchy;
  }

  // Detect card type based on content
  detectCardType(question, answer, additionalFields = {}) {
    const combinedText = (question || "") + (answer || "");
    const clozePattern = /\{\{c\d+::[^}]+\}\}/g;

    if (clozePattern.test(combinedText)) {
      this.log(levelDebug, "Detected card type: cloze");
      return "cloze";
    }

    // Check for specific question and answer image paths for image occlusion
    const hasQuestionImage = additionalFields.questionImagePath && additionalFields.questionImagePath.trim() !== '';
    const hasAnswerImage = additionalFields.answerImagePath && additionalFields.answerImagePath.trim() !== '';

    if (hasQuestionImage || hasAnswerImage) {
      this.log(levelDebug, "Detected card type: imageOcclusion");
      return "imageOcclusion";
    }
    // Original single imagePath check (if still needed for other use cases)
    if (additionalFields.imagePath && additionalFields.imagePath.trim() !== '') {
      this.log(levelDebug, "Detected card type: imageOcclusion (single imagePath)");
      return "imageOcclusion";
    }

    const mcqFields = [additionalFields.optionA, additionalFields.optionB, additionalFields.optionC, additionalFields.optionD];
    if (mcqFields.some(opt => opt && opt.trim() !== '') || (additionalFields.correctAnswer && additionalFields.correctAnswer.trim() !== '')) {
      this.log(levelDebug, "Detected card type: mcq");
      return "mcq";
    }

    this.log(levelDebug, "Detected card type: basic");
    return "basic";
  }

  // Create note with proper model detection
  async createNote(question, answer, jtaID, title, notebook, tags = [], folders = [], additionalFields = {}) {
    const deckName = this.determineDeckName(tags, folders, notebook?.id);
    const cardType = this.detectCardType(question, answer, additionalFields);
    const modelName = models[cardType].name;

    this.log(levelVerbose, `Preparing to create a new ${cardType} card for "${title}" (JTA ID: ${jtaID})`);

    // Process image paths for image occlusion cards
    if (cardType === 'imageOcclusion') {
        if (additionalFields.questionImagePath) {
            additionalFields.questionImagePath = await this.processImagePath(additionalFields.questionImagePath);
        }
        if (additionalFields.answerImagePath) {
            additionalFields.answerImagePath = await this.processImagePath(additionalFields.answerImagePath);
        }
    } else if (additionalFields.imagePath) { // For other card types that might still use a single imagePath field
        additionalFields.imagePath = await this.processImagePath(additionalFields.imagePath);
    }

    // Build fields based on card type
    let fields = {};

    switch (cardType) {
      case 'basic':
          fields = {
            "Header": additionalFields.header || "",                     
            "Question": question,
            "Answer": answer,
            "Explanation": additionalFields.explanation || "",
            "Clinical Correlation": additionalFields.clinicalCorrelation || "",
            "Footer": additionalFields.footer || "",                      
            "Sources": additionalFields.sources || "",                   
            "Joplin to Anki ID": jtaID
          };
          break;

      case 'cloze':
          fields = {
            "Header": additionalFields.header || "",                      
            "Text": question,
            "Extra": additionalFields.extra || "",
            "Explanation": additionalFields.explanation || "",
            "Clinical Correlation": additionalFields.clinicalCorrelation || "",
            "Footer": additionalFields.footer || "",                      
            "Sources": additionalFields.sources || "",                    
            "Joplin to Anki ID": jtaID
          };
          break;

      case 'mcq':
          fields = {
            "Header": additionalFields.header || "",                      
            "Question": question,
            "OptionA": additionalFields.optionA || "",
            "OptionB": additionalFields.optionB || "",
            "OptionC": additionalFields.optionC || "",
            "OptionD": additionalFields.optionD || "",
            "CorrectAnswer": additionalFields.correctAnswer || "",
            "Explanation": additionalFields.explanation || "",
            "Clinical Correlation": additionalFields.clinicalCorrelation || "",
            "Footer": additionalFields.footer || "",                      
            "Sources": additionalFields.sources || "",                    
            "Joplin to Anki ID": jtaID
          };
          break;

     case 'imageOcclusion':
       // **CRITICAL FIX:** Ensure Question and Answer fields always have content
       console.log(`DEBUG imageOcclusion before cleaning:
         Raw question: "${question}"
         Raw answer: "${answer}"
       `);
       
       const cleanQuestion = question.trim().replace(/<[^>]*>/g, '').trim();
       const cleanAnswer = answer.trim().replace(/<[^>]*>/g, '').trim();
       
       console.log(`DEBUG imageOcclusion after cleaning:
         Clean question: "${cleanQuestion}" (length: ${cleanQuestion.length})
         Clean answer: "${cleanAnswer}" (length: ${cleanAnswer.length})
       `);
       
       fields = {
             "Header": additionalFields.header || "",                      
             "QuestionImagePath": additionalFields.questionImagePath || "",
             "AnswerImagePath": additionalFields.answerImagePath || "",
             "AltText": additionalFields.altText || "",
             "Question": question, 
             "Answer": answer,
             "Origin": additionalFields.origin || "",
             "Insertion": additionalFields.insertion || "",
             "Innervation": additionalFields.innervation || "",
             "Action": additionalFields.action || "",
             "Comments": additionalFields.comments || "",
             "Clinical Correlation": additionalFields.clinicalCorrelation || "",
             "Footer": additionalFields.footer || "",                      
             "Sources": additionalFields.sources || "",                    
             "Joplin to Anki ID": jtaID
           };
           break;
     }

    // Build note tags
    const noteTags = [
      ...tags,
      `joplin-title:${title}`,
      `joplin-notebook:${notebook?.title || 'Unknown'}`
    ];

    const noteData = {
      deckName: deckName,
      modelName: modelName,
      fields: fields,
      tags: noteTags
    };

    this.log(levelDebug, `Final Note Data for Anki (create):
      Deck: ${noteData.deckName}
      Model: ${noteData.modelName}
      Fields: ${JSON.stringify(noteData.fields, null, 2)}
      Tags: ${noteData.tags.join(', ')}
    `);
    
    // ADD THIS NEW DEBUG
    console.log(`DEBUG: About to call addNote with full payload:`);
    console.log(JSON.stringify({
      deckName: noteData.deckName,
      modelName: noteData.modelName,
      fields: noteData.fields,
      tags: noteData.tags
    }, null, 2));
    
    const result = await this.addNote(noteData);
    this.log(levelApplication, `✅ Created ${cardType} card: "${title}" (Anki Note ID: ${result})`);
    return result;
  }

  // Update existing note
  async updateNote(noteId, question, answer, additionalFields = {}) {
    const noteInfo = await this.getNoteInfo([noteId]);
    if (!noteInfo || noteInfo.length === 0) {
      throw new Error(`Note ${noteId} not found`);
    }

    const note = noteInfo[0];
    const cardType = this.detectCardType(question, answer, additionalFields); // Re-detect card type

    this.log(levelVerbose, `Preparing to update a ${cardType} card (Anki Note ID: ${noteId})`);

    // Process image paths for image occlusion cards
    if (cardType === 'imageOcclusion') {
        if (additionalFields.questionImagePath) {
            additionalFields.questionImagePath = await this.processImagePath(additionalFields.questionImagePath);
        }
        if (additionalFields.answerImagePath) {
            additionalFields.answerImagePath = await this.processImagePath(additionalFields.answerImagePath);
        }
    } else if (additionalFields.imagePath) { // For other card types that might still use a single imagePath field
        additionalFields.imagePath = await this.processImagePath(additionalFields.imagePath);
    }

    // Build updated fields
    let fields = {};

    switch (cardType) {
      case 'basic':
          fields = {
            "Header": additionalFields.header || "",                     
            "Question": question,
            "Answer": answer,
            "Explanation": additionalFields.explanation || "",
            "Clinical Correlation": additionalFields.clinicalCorrelation || "",
            "Footer": additionalFields.footer || "",                     
            "Sources": additionalFields.sources || "",                    
          };
        break;

      case 'cloze':
          fields = {
            "Header": additionalFields.header || "",                      
            "Text": question,
            "Extra": additionalFields.extra || "",
            "Explanation": additionalFields.explanation || "",
            "Clinical Correlation": additionalFields.clinicalCorrelation || "",
            "Footer": additionalFields.footer || "",                     
            "Sources": additionalFields.sources || "",                  
          };
          break;

      case 'mcq':
          fields = {
            "Header": additionalFields.header || "",                      
            "Question": question,
            "OptionA": additionalFields.optionA || "",
            "OptionB": additionalFields.optionB || "",
            "OptionC": additionalFields.optionC || "",
            "OptionD": additionalFields.optionD || "",
            "CorrectAnswer": additionalFields.correctAnswer || "",
            "Explanation": additionalFields.explanation || "",
            "Clinical Correlation": additionalFields.clinicalCorrelation || "",
            "Footer": additionalFields.footer || "",                      
            "Sources": additionalFields.sources || "",                    
          };
          break;

      case 'imageOcclusion':
        // **CRITICAL FIX:** Ensure Question and Answer fields always have content
        const cleanQuestion = question.trim().replace(/<[^>]*>/g, '').trim();
        const cleanAnswer = answer.trim().replace(/<[^>]*>/g, '').trim();
        
        fields = {
              "Header": additionalFields.header || "",                      
              "QuestionImagePath": additionalFields.questionImagePath || "",
              "AnswerImagePath": additionalFields.answerImagePath || "",
              "AltText": additionalFields.altText || "",
              "Question": question, 
              "Answer": answer,
              "Origin": additionalFields.origin || "",
              "Insertion": additionalFields.insertion || "",
              "Innervation": additionalFields.innervation || "",
              "Action": additionalFields.action || "",
              "Comments": additionalFields.comments || "",
              "Clinical Correlation": additionalFields.clinicalCorrelation || "",
              "Footer": additionalFields.footer || "",                      
              "Sources": additionalFields.sources || "",                    
            };
            break;
      }

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

  // Update note tags
  async updateNoteTags(noteId, title, notebook, tags = []) {
    const noteTags = [
      ...tags,
      `joplin-title:${title}`,
      `joplin-notebook:${notebook?.title || 'Unknown'}`
    ];

    try {
      await this.doRequest({
        action: "updateNoteTags",
        version: 6,
        params: {
          note: noteId,
          tags: noteTags.join(" ")
        }
      });
      this.log(levelVerbose, `Updated tags for note ${noteId}.`);
    } catch (error) {
      // Non-fatal, just log warning
      this.log(levelApplication, `⚠️ Could not update tags for note ${noteId}: ${error.message}`);
    }
  }

  async canAddNotes(notes) {
    return this.doRequest({
      action: "canAddNotes",
      version: 6,
      params: { notes }
    });
  }

  async createModel(modelType = 'basic') {
    const model = models[modelType];
    if (!model) {
      this.log(levelApplication, `❌ Unknown model type: ${modelType}`);
      throw new Error(`Unknown model type: ${modelType}`);
    }

    const params = {
      modelName: model.name,
      inOrderFields: model.fields,
      cardTemplates: model.cardTemplates,
    };

    if (model.isCloze) params.isCloze = true;

    this.log(levelApplication, `Attempting to create Anki model: "${model.name}"`);
    try {
      await this.doRequest({
        action: "createModel",
        version: 6,
        params
      });
      this.log(levelApplication, `✅ Successfully created Anki model: "${model.name}"`);
    } catch (error) {
      if (error.message.includes('already exists')) {
        this.log(levelApplication, `⚠️ Model "${model.name}" already exists. Skipping creation.`);
      } else {
        this.log(levelApplication, `❌ Failed to create model "${model.name}": ${error.message}`);
        throw error;
      }
    }
  }
}

// --- START OF REVISED MODELS OBJECT ---
const models = {
  basic: {
    name: "Joplin to Anki Basic Enhanced",
        fields: [
          "Header",           
          "Question",
          "Answer",
          "Explanation",
          "Clinical Correlation",
          "Footer",           
          "Sources",          
          "Joplin to Anki ID"
        ],
    cardTemplates: [{
      Name: "Enhanced Basic Card",
      Front: `
        <div class="card">
          <div class="question">{{Question}}</div>
        </div>
      `,
      Back: `
        <div class="card">
          <div class="question">{{Question}}</div>
          <hr id="answer">
          <div class="answer">{{Answer}}</div>
          <div class="explanation">{{Explanation}}</div>
          <div class="correlation">{{Clinical Correlation}}</div>
        </div>
      `
    }]
  },

  cloze: {
    name: "Joplin to Anki Cloze Enhanced",
        fields: [
          "Header",           
          "Text",
          "Extra",
          "Explanation",
          "Clinical Correlation",
          "Footer",           
          "Sources",          
          "Joplin to Anki ID"
        ],
    cardTemplates: [{
      Name: "Enhanced Cloze Card",
      Front: `
        <div class="card">
          <div class="cloze">{{cloze:Text}}</div>
        </div>
      `,
      Back: `
        <div class="card">
          <div class="cloze">{{cloze:Text}}</div>
          <hr id="answer">
          <div class="extra">{{Extra}}</div>
          <div class="explanation">{{Explanation}}</div>
          <div class="correlation">{{Clinical Correlation}}</div>
        </div>
      `
    }],
    isCloze: true
  },

  mcq: {
    name: "Joplin to Anki MCQ Enhanced",
        fields: [
          "Header",           
          "Question",
          "OptionA",
          "OptionB",
          "OptionC",
          "OptionD",
          "CorrectAnswer",
          "Explanation",
          "Clinical Correlation",
          "Footer",           
          "Sources",          
          "Joplin to Anki ID"
        ],
    cardTemplates: [{
      Name: "Enhanced MCQ Card",
      Front: `
        <div class="card">
          <div class="question">{{Question}}</div>
          <ul class="options">
            <li>A) {{OptionA}}</li>
            <li>B) {{OptionB}}</li>
            <li>C) {{OptionC}}</li>
            <li>D) {{OptionD}}</li>
          </ul>
        </div>
      `,
      Back: `
        <div class="card">
          <div class="question">{{Question}}</div>
          <ul class="options">
            <li>A) {{OptionA}}</li>
            <li>B) {{OptionB}}</li>
            <li>C) {{OptionC}}</li>
            <li>D) {{OptionD}}</li>
          </ul>
          <hr id="answer">
          <div class="correct-answer">Answer: {{CorrectAnswer}}</div>
          <div class="explanation">{{Explanation}}</div>
          <div class="correlation">{{Clinical Correlation}}</div>
        </div>
      `
    }]
  },

  imageOcclusion: { // Renamed to "imageOcclusion" for consistency with detectCardType
    name: "Joplin to Anki Image Enhanced",
        fields: [
          "Header",             
          "QuestionImagePath",
          "AnswerImagePath",
          "AltText",
          "Question",
          "Answer",
          "Origin",             
          "Insertion",
          "Comments",
          "Clinical Correlation",
          "Footer",             
          "Sources",            
          "Joplin to Anki ID"
        ],
    cardTemplates: [{
      Name: "Enhanced Image Occlusion Question", // This is the actual Anki card template name
      Front: `
        <div class="card">
          {{#QuestionImagePath}}
          <img src="{{QuestionImagePath}}" alt="{{AltText}}">
          {{/QuestionImagePath}}
          <div class="image-question">{{Question}}</div>
        </div>
      `,
      Back: `
        <div class="card">
          {{#AnswerImagePath}}
          <img src="{{AnswerImagePath}}" alt="{{AltText}}">
          {{/AnswerImagePath}}
          <div class="image-question">{{Question}}</div>
          <hr id="answer">
          <div class="answer">{{Answer}}</div>
          <div class="comments">{{Comments}}</div>
          <div class="correlation">{{Clinical Correlation}}</div>
        </div>
      `
    }]
  }
};
// --- END OF REVISED MODELS OBJECT ---

module.exports = AnkiClient;

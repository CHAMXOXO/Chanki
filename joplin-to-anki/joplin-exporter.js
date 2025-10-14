// Joplin Exporter - Final Version with Corrected Standard Note Extraction
const cheerio = require('cheerio');
const crypto = require('crypto');
const { levelApplication, levelVerbose, levelDebug } = require('./log');

const typeItem = 'item';
const typeResource = 'resource';
const typeError = 'error';

// ============================================================================
// PREMIUM FEATURE REGISTRATION (Unchanged)
// ============================================================================
let premiumDeckHandler = null;
let dynamicMapper = null;

function registerPremiumDeckHandler(handler) {
  premiumDeckHandler = handler;
}

function registerDynamicMapper(mapper) {
  dynamicMapper = mapper;
}
// ============================================================================

const generateUniqueID = (noteId, index = 0) => {
  const hash = crypto.createHash('md5').update(`${noteId}${index}`).digest('hex');
  return `joplin_${hash.substring(0, 12)}`;
};

// ============================================================================
// HELPER FUNCTION TO RESTORE ORIGINAL LOGIC
// ============================================================================
/**
 * This is the restored, powerful function from your original code. 
 * It extracts all possible fields for all standard note types.
 */
const extractAdditionalFieldsFromElement = ($, jtaElement, log) => {
  const fields = {
    // Initialize all possible fields
    explanation: '', clinicalCorrelation: '', extra: '', header: '', footer: '', sources: '',
    comments: '', origin: '', insertion: '', innervation: '', action: '',
    optionA: '', optionB: '', optionC: '', optionD: '', correctAnswer: '',
    questionImagePath: '', answerImagePath: '', altText: ''
  };

  // --- General Field Extraction ---
  fields.header = $('.header', jtaElement).html()?.trim() || '';
  fields.footer = $('.footer', jtaElement).html()?.trim() || '';
  fields.sources = $('.sources', jtaElement).html()?.trim() || '';
  fields.explanation = $('.explanation', jtaElement).html()?.trim() || '';
  fields.clinicalCorrelation = $('.correlation', jtaElement).html()?.trim() || '';
  fields.extra = $('.extra', jtaElement).html()?.trim() || '';
  fields.comments = $('.comments', jtaElement).html()?.trim() || '';
  fields.correctAnswer = $('.correct-answer', jtaElement).text()?.trim() || '';

  // --- Image-Specific Field Extraction ---
  fields.origin = $('.origin', jtaElement).html()?.trim() || '';
  fields.insertion = $('.insertion', jtaElement).html()?.trim() || '';
  fields.innervation = $('.innervation', jtaElement).html()?.trim() || '';
  fields.action = $('.action', jtaElement).html()?.trim() || '';
  
  const questionImgEl = $('img[data-jta-image-type="question"]', jtaElement);
  if (questionImgEl.length > 0) {
    fields.questionImagePath = questionImgEl.attr('src') || '';
    fields.altText = questionImgEl.attr('alt') || '';
  }
  const answerImgEl = $('img[data-jta-image-type="answer"]', jtaElement);
  if (answerImgEl.length > 0) {
    fields.answerImagePath = answerImgEl.attr('src') || '';
  }
  
  // --- MCQ-Specific Field Extraction using REGEX (from your original logic) ---
  const questionTextContent = ($('.question', jtaElement).text() || "");
  if (questionTextContent.length > 0) {
    const optionPatterns = [
        /(?:A\)|A\.)\s*([\s\S]*?)(?=\s*(?:B\)|B\.|$))/i,
        /(?:B\)|B\.)\s*([\s\S]*?)(?=\s*(?:C\)|C\.|$))/i,
        /(?:C\)|C\.)\s*([\s\S]*?)(?=\s*(?:D\)|D\.|$))/i,
        /(?:D\)|D\.)\s*([\s\S]*?)(?=\s*$)/i
    ];
    
    const optionMatches = optionPatterns.map(pattern => {
      const match = questionTextContent.match(pattern);
      return match ? match[1].trim() : '';
    });

    if (optionMatches.filter(Boolean).length >= 2) {
      fields.optionA = optionMatches[0] || '';
      fields.optionB = optionMatches[1] || '';
      fields.optionC = optionMatches[2] || '';
      fields.optionD = optionMatches[3] || '';
    }
  }

  // Clean up any empty fields
  for (const key in fields) {
    if (fields[key] === '' || fields[key] === null) {
      delete fields[key];
    }
  }

  return fields;
};
// ============================================================================


class JoplinExporter {
  constructor(joplinClient, log) {
    this.joplinClient = joplinClient;
    this.log = log;
    this.folders = null;
  }

  async fetchFolders() {
    if (!this.folders) {
      this.folders = await this.joplinClient.getAllFolders();
    }
    return this.folders;
  }

  getNotebookPath(notebookId) {
    const folders = this.folders;
    if (!folders) return "Unknown";

    const path = [];
    let currentId = notebookId;
    while (currentId) {
      const folder = folders.find(f => f.id === currentId);
      if (folder) {
        path.unshift(folder.title);
        currentId = folder.parent_id;
      } else {
        break;
      }
    }
    return path.join('::');
  }
  
    async extractQuizItems(note) {
      const quizItems = [];
      const $ = cheerio.load(note.body);
      const jtaBlocks = $(".jta");
  
      if (jtaBlocks.length === 0) {
        return [];
      }
      
      const details = await this.joplinClient.getNoteDetails(note.id);
      await this.fetchFolders();
  
      jtaBlocks.each((i, el) => {
        let jtaID = $(el).attr("data-id");
        if (!jtaID || jtaID.trim().length === 0) {
          jtaID = generateUniqueID(note.id, i);
        }
  
        const noteType = $(el).attr('data-note-type');
        let item;
  
        // Premium Dynamic Path (Unchanged)
        if (dynamicMapper && noteType && dynamicMapper.getAvailableNoteTypes().includes(noteType)) {
          const extractedData = dynamicMapper.extractFields($(el).html(), jtaID, noteType);
          if (extractedData) {
            item = {
              jtaID: jtaID,
              title: details.note.title,
              notebook: details.notebook,
              tags: details.tags,
              folders: this.folders,
              question: '', 
              answer: '',   
              additionalFields: {
                customNoteType: extractedData.modelName, 
                customFields: extractedData.fields,     
              },
            };
          } else {
            this.log(levelApplication, `Skipping JTA block for note type "${noteType}" because mapping failed. Check logs.`);
            return;
          }
        } else {
          // ==================================================================
          // CORRECTED STANDARD EXTRACTION LOGIC
          // ==================================================================
          this.log(levelDebug, `Using corrected standard extractor for JTA ID: ${jtaID}`);
          
          // Call the powerful helper function to get ALL possible standard fields
          const additionalFields = extractAdditionalFieldsFromElement($, el, this.log);

          item = {
            jtaID: jtaID,
            title: details.note.title,
            notebook: details.notebook,
            question: $(el).find(".question").html(),
            answer: $(el).find(".answer").html(),
            additionalFields: additionalFields, // Use the complete object here
            tags: details.tags,
            folders: this.folders,
          };
        }
  
        if (premiumDeckHandler) {
          item.deckName = premiumDeckHandler(details.tags, details.notebook, this.folders, this.log);
        } else {
          item.deckName = this.getNotebookPath(details.notebook.id);
        }
  
        quizItems.push(item);
      });
  
      return quizItems;
    }
}

// Legacy generator function for one-way sync (Unchanged)
async function* exporter(joplinClient, fromDate, log) {
  const notes = await joplinClient.getAllNotes("id,updated_time,title,parent_id,body", fromDate);
  const exporterInstance = new JoplinExporter(joplinClient, log);

  for (const note of notes) {
    try {
      const items = await exporterInstance.extractQuizItems(note);
      for (const item of items) {
        yield { type: typeItem, data: item };
      }
    } catch (error) {
      yield { type: typeError, data: `Failed to process note ${note.id}: ${error.message}` };
    }
  }
}

// Module exports (Unchanged)
module.exports = {
  JoplinExporter,
  exporter,
  typeItem,
  typeResource,
  typeError,
  registerPremiumDeckHandler,
  registerDynamicMapper
};

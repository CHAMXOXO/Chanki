// Joplin Exporter - Final Version, confirmed against user's actual premium feature code.
const cheerio = require('cheerio');
const crypto = require('crypto');
const { levelApplication, levelVerbose, levelDebug } = require('./log');

const typeItem = 'item';
const typeResource = 'resource';
const typeError = 'error';

// ============================================================================
// PREMIUM FEATURE REGISTRATION (Placeholders)
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

  // This is no longer needed in the premium path but kept for fallback
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
  
        if (dynamicMapper && noteType && dynamicMapper.getAvailableNoteTypes().includes(noteType)) {
          const extractedData = dynamicMapper.extractFields($(el).html(), jtaID, noteType);
          if (extractedData) {
            // --- THIS IS THE CORRECTED STRUCTURE FOR DYNAMIC ITEMS ---
            item = {
              jtaID: jtaID,
              title: details.note.title,
              notebook: details.notebook,
              tags: details.tags,
              folders: this.folders,
              question: '', // Add empty placeholders to ensure function calls don't fail
              answer: '',   // These are not used by the custom path but prevent errors
              additionalFields: {
                customNoteType: extractedData.modelName, // Correctly nested
                customFields: extractedData.fields,     // Correctly nested
              },
            };
          } else {
            this.log(levelApplication, `Skipping JTA block for note type "${noteType}" because mapping failed. Check logs.`);
            return;
          }
        } else {
          // Standard extraction logic (this part is already correct)
          item = {
            jtaID: jtaID,
            title: details.note.title,
            notebook: details.notebook,
            question: $(el).find(".question").html(),
            answer: $(el).find(".answer").html(),
            additionalFields: {
              "Explanation": $(el).find(".explanation").html(),
              "Header": $(el).find(".header").html(),
              "Footer": $(el).find(".footer").html(),
              "Sources": $(el).find(".sources").html(),
              "Clinical Correlation": $(el).find(".correlation").html(),
            },
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

// Legacy generator function for one-way sync
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

module.exports = {
  JoplinExporter,
  exporter,
  typeItem,
  typeResource,
  typeError,
  registerPremiumDeckHandler,
  registerDynamicMapper
};

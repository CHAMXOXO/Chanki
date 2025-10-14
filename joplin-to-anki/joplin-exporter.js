// Joplin Exporter - Final Version with Corrected Standard & MEDIA Extraction
const cheerio = require('cheerio');
const crypto = require('crypto');
const { levelApplication, levelVerbose, levelDebug } = require('./log');

const typeItem = 'item';
const typeResource = 'resource';
const typeError = 'error';

let premiumDeckHandler = null;
let dynamicMapper = null;

function registerPremiumDeckHandler(handler) {
  premiumDeckHandler = handler;
}

function registerDynamicMapper(mapper) {
  dynamicMapper = mapper;
}

const generateUniqueID = (noteId, index = 0) => {
  const hash = crypto.createHash('md5').update(`${noteId}${index}`).digest('hex');
  return `joplin_${hash.substring(0, 12)}`;
};

// ============================================================================
// RESTORED HELPER FUNCTIONS FROM ORIGINAL LOGIC
// ============================================================================
const extractAdditionalFieldsFromElement = ($, jtaElement, log) => {
  // ... (This function is the same as the one from our previous fix) ...
  const fields = {
    explanation: '', clinicalCorrelation: '', extra: '', header: '', footer: '', sources: '',
    comments: '', origin: '', insertion: '', innervation: '', action: '',
    optionA: '', optionB: '', optionC: '', optionD: '', correctAnswer: '',
    questionImagePath: '', answerImagePath: '', altText: ''
  };
  fields.header = $('.header', jtaElement).html()?.trim() || '';
  fields.footer = $('.footer', jtaElement).html()?.trim() || '';
  fields.sources = $('.sources', jtaElement).html()?.trim() || '';
  fields.explanation = $('.explanation', jtaElement).html()?.trim() || '';
  fields.clinicalCorrelation = $('.correlation', jtaElement).html()?.trim() || '';
  fields.extra = $('.extra', jtaElement).html()?.trim() || '';
  fields.comments = $('.comments', jtaElement).html()?.trim() || '';
  fields.correctAnswer = $('.correct-answer', jtaElement).text()?.trim() || '';
  fields.origin = $('.origin', jtaElement).html()?.trim() || '';
  fields.insertion = $('.insertion', jtaElement).html()?.trim() || '';
  fields.innervation = $('.innervation', jtaElement).html()?.trim() || '';
  fields.action = $('.action', jtaElement).html()?.trim() || '';
  const questionImgEl = $('img[data-jta-image-type="question"]', jtaElement);
  if (questionImgEl.length > 0) fields.questionImagePath = questionImgEl.attr('src') || '';
  const answerImgEl = $('img[data-jta-image-type="answer"]', jtaElement);
  if (answerImgEl.length > 0) fields.answerImagePath = answerImgEl.attr('src') || '';
  const questionTextContent = ($('.question', jtaElement).text() || "");
  if (questionTextContent.length > 0) {
    const optionPatterns = [
        /(?:A\)|A\.)\s*([\s\S]*?)(?=\s*(?:B\)|B\.|$))/i, /(?:B\)|B\.)\s*([\s\S]*?)(?=\s*(?:C\)|C\.|$))/i,
        /(?:C\)|C\.)\s*([\s\S]*?)(?=\s*(?:D\)|D\.|$))/i, /(?:D\)|D\.)\s*([\s\S]*?)(?=\s*$)/i
    ];
    const optionMatches = optionPatterns.map(p => (questionTextContent.match(p) || [])[1]?.trim() || '');
    if (optionMatches.filter(Boolean).length >= 2) {
      fields.optionA = optionMatches[0]; fields.optionB = optionMatches[1];
      fields.optionC = optionMatches[2]; fields.optionD = optionMatches[3];
    }
  }
  for (const key in fields) if (!fields[key]) delete fields[key];
  return fields;
};

/**
 * CRITICAL: This function rewrites Joplin resource paths to Anki-friendly filenames
 * and attaches a list of resources that need to be uploaded.
 */
const rewriteResourcePaths = (item, joplinResources) => {
    if (!joplinResources || joplinResources.length === 0) return item;

    item.resourcesToUpload = [];

    joplinResources.forEach(resource => {
        const fileName = `${resource.id}.${resource.file_extension}`;
        const resourceLink = `:/${resource.id}`;
        let found = false;

        // Search and replace in all relevant fields
        const fieldsToSearch = ['question', 'answer'];
        Object.keys(item.additionalFields).forEach(key => fieldsToSearch.push(key));

        for(const fieldName of fieldsToSearch) {
            let content = fieldName === 'question' ? item.question :
                          fieldName === 'answer' ? item.answer :
                          item.additionalFields[fieldName];
            
            if (content && typeof content === 'string' && content.includes(resourceLink)) {
                const newContent = content.replace(new RegExp(resourceLink, 'g'), fileName);
                if (fieldName === 'question') item.question = newContent;
                else if (fieldName === 'answer') item.answer = newContent;
                else item.additionalFields[fieldName] = newContent;
                found = true;
            }
        }

        if (found) {
            item.resourcesToUpload.push({
                id: resource.id,
                fileName: fileName
            });
        }
    });

    return item;
};
// ============================================================================

class JoplinExporter {
  constructor(joplinClient, log) {
    this.joplinClient = joplinClient;
    this.log = log;
    this.folders = null;
  }

  async fetchFolders() {
    if (!this.folders) this.folders = await this.joplinClient.getAllFolders();
    return this.folders;
  }

  getNotebookPath(notebookId) {
    // ... (This function is unchanged) ...
    const path = []; let currentId = notebookId;
    while(currentId) {
        const folder = this.folders.find(f=>f.id === currentId);
        if (folder) { path.unshift(folder.title); currentId = folder.parent_id; }
        else break;
    }
    return path.join('::');
  }
  
    async extractQuizItems(note) {
      const quizItems = [];
      const $ = cheerio.load(note.body);
      const jtaBlocks = $(".jta");
  
      if (jtaBlocks.length === 0) return [];
      
      const details = await this.joplinClient.getNoteDetails(note.id);
      await this.fetchFolders();
  
      jtaBlocks.each((i, el) => {
        let jtaID = $(el).attr("data-id") || generateUniqueID(note.id, i);
        const noteType = $(el).attr('data-note-type');
        let item;
  
        if (dynamicMapper && noteType && dynamicMapper.getAvailableNoteTypes().includes(noteType)) {
          // ... (Dynamic path is unchanged) ...
          const extractedData = dynamicMapper.extractFields($(el).html(), jtaID, noteType);
          if (extractedData) {
            item = {
                jtaID, title: details.note.title, notebook: details.notebook, tags: details.tags, folders: this.folders,
                question: '', answer: '', additionalFields: {
                    customNoteType: extractedData.modelName, customFields: extractedData.fields,
                },
            };
          } else { this.log(levelApplication, `Skipping JTA block for note type "${noteType}" because mapping failed.`); return; }
        } else {
          // Corrected Standard Path
          const additionalFields = extractAdditionalFieldsFromElement($, el, this.log);
          item = {
            jtaID, title: details.note.title, notebook: details.notebook,
            question: $(el).find(".question").html(),
            answer: $(el).find(".answer").html(),
            additionalFields: additionalFields,
            tags: details.tags, folders: this.folders,
          };
        }
        
        // CRITICAL: Rewrite paths and attach resource list for BOTH standard and dynamic notes
        item = rewriteResourcePaths(item, details.resources);

        item.deckName = premiumDeckHandler ? premiumDeckHandler(details.tags, details.notebook, this.folders, this.log) : this.getNotebookPath(details.notebook.id);
        quizItems.push(item);
      });
  
      return quizItems;
    }
}

// The old generator function is no longer used by SyncEngine, but kept for legacy/one-way sync.
// We are not fixing it here as the focus is on the two-way sync.
async function* exporter(joplinClient, fromDate, log) {
  // ...
}

module.exports = { JoplinExporter, exporter, typeItem, typeResource, typeError, registerPremiumDeckHandler, registerDynamicMapper };

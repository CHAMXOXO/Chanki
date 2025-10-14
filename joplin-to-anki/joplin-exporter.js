// Joplin Exporter - FIXED with Index Tracking for Standard Notes
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
// HELPER FUNCTIONS
// ============================================================================
const extractAdditionalFieldsFromElement = ($, jtaElement, log) => {
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
  if (questionImgEl.length > 0) {
    fields.questionImagePath = questionImgEl.attr('src') || '';
    fields.altText = questionImgEl.attr('alt') || '';
  }
  
  const answerImgEl = $('img[data-jta-image-type="answer"]', jtaElement);
  if (answerImgEl.length > 0) {
    fields.answerImagePath = answerImgEl.attr('src') || '';
  }
  
  const questionTextContent = ($('.question', jtaElement).text() || "");
  if (questionTextContent.length > 0) {
    const optionPatterns = [
        /(?:A\)|A\.)\s*([\s\S]*?)(?=\s*(?:B\)|B\.|$))/i, 
        /(?:B\)|B\.)\s*([\s\S]*?)(?=\s*(?:C\)|C\.|$))/i,
        /(?:C\)|C\.)\s*([\s\S]*?)(?=\s*(?:D\)|D\.|$))/i, 
        /(?:D\)|D\.)\s*([\s\S]*?)(?=\s*$)/i
    ];
    const optionMatches = optionPatterns.map(p => (questionTextContent.match(p) || [])[1]?.trim() || '');
    if (optionMatches.filter(Boolean).length >= 2) {
      fields.optionA = optionMatches[0]; 
      fields.optionB = optionMatches[1];
      fields.optionC = optionMatches[2]; 
      fields.optionD = optionMatches[3];
    }
  }
  
  for (const key in fields) {
    if (!fields[key]) delete fields[key];
  }
  
  return fields;
};

const enrichResourcesWithExtension = (resources, log) => {
  if (!resources || resources.length === 0) return resources;
  
  return resources.map(resource => {
    if (!resource.file_extension && resource.title) {
      const parts = resource.title.split('.');
      const extension = parts.length > 1 ? parts[parts.length - 1] : '';
      
      if (extension) {
        resource.file_extension = extension;
        log(levelDebug, `[RESOURCE] Enriched resource ${resource.id}: extracted file_extension="${extension}"`);
      }
    }
    return resource;
  });
};

const rewriteResourcePaths = (item, joplinResources, log) => {
    if (!joplinResources || joplinResources.length === 0) {
        return item;
    }

    if (!item.resourcesToUpload) {
        item.resourcesToUpload = [];
    }

    joplinResources.forEach(resource => {
        if (!resource || !resource.file_extension) {
            return;
        }

        const fileName = `${resource.id}.${resource.file_extension}`;
        const resourceLink = `:/${resource.id}`;
        let found = false;

        const fieldsToSearch = ['question', 'answer'];
        if (item.additionalFields) {
            fieldsToSearch.push('questionImagePath', 'answerImagePath', 
                               'explanation', 'clinicalCorrelation', 'extra', 
                               'header', 'footer', 'sources', 'comments');
        }

        for (const fieldName of fieldsToSearch) {
            let content;
            
            if (fieldName === 'question') {
                content = item.question;
            } else if (fieldName === 'answer') {
                content = item.answer;
            } else if (item.additionalFields) {
                content = item.additionalFields[fieldName];
            }
            
            if (content && typeof content === 'string' && content.includes(resourceLink)) {
                const newContent = content.replace(new RegExp(resourceLink.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), fileName);
                
                if (fieldName === 'question') {
                    item.question = newContent;
                } else if (fieldName === 'answer') {
                    item.answer = newContent;
                } else if (item.additionalFields) {
                    item.additionalFields[fieldName] = newContent;
                }
                
                found = true;
            }
        }

        if (found) {
            if (!item.resourcesToUpload.find(r => r.id === resource.id)) {
                item.resourcesToUpload.push({
                    id: resource.id,
                    fileName: fileName
                });
            }
        }
    });

    return item;
};

// ============================================================================
// MAIN EXPORTER CLASS
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
    const path = []; 
    let currentId = notebookId;
    while(currentId) {
        const folder = this.folders.find(f => f.id === currentId);
        if (folder) { 
          path.unshift(folder.title); 
          currentId = folder.parent_id; 
        } else break;
    }
    return path.join('::');
  }
  
  async extractQuizItems(note) {
    const quizItems = [];
    const $ = cheerio.load(note.body);
    const jtaBlocks = $(".jta");

    if (jtaBlocks.length === 0) return [];
    
    this.log(levelDebug, `🔍 Extracting quiz items from note ${note.id} (${note.title})`);
    
    const details = await this.joplinClient.getNoteDetails(note.id);
    await this.fetchFolders();

    const enrichedResources = enrichResourcesWithExtension(details.resources, this.log);

    // ========================================================================
    // CRITICAL FIX: Track the index of each .jta block
    // ========================================================================
    jtaBlocks.each((i, el) => {
      const jtaID = $(el).attr("data-id") || generateUniqueID(note.id, i);
      const noteType = $(el).attr('data-note-type');
      let item;
      const isDynamic = dynamicMapper && noteType && dynamicMapper.getAvailableNoteTypes().includes(noteType);

      this.log(levelDebug, `Processing JTA block ${i} (ID: ${jtaID}, Type: ${isDynamic ? noteType : 'standard'})`);

      if (isDynamic) {
        const extractedData = dynamicMapper.extractFields($(el).html(), jtaID, noteType);
        if (extractedData) {
          item = {
            jtaID,
            index: i, // ← ADD INDEX
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
            index: i,                 
            joplinNoteId: note.id,    
          };
        } else {
          this.log(levelApplication, `⚠️ Skipping JTA block - dynamic mapping failed for "${noteType}"`);
          return;
        }
      } else {
        const additionalFields = extractAdditionalFieldsFromElement($, el, this.log);
        
        item = {
          jtaID,
          index: i, // ← ADD INDEX FOR STANDARD NOTES TOO
          title: details.note.title,
          notebook: details.notebook,
          question: $(el).find(".question").html() || '',
          answer: $(el).find(".answer").html() || '',
          additionalFields: additionalFields,
          tags: details.tags,
          folders: this.folders,
          index: i,                 
          joplinNoteId: note.id,    
        };
      }
      
      rewriteResourcePaths(item, enrichedResources, this.log);

      if (!isDynamic) {
        if (item.question) {
            const $question = cheerio.load(item.question, null, false);
            $question('img[data-jta-image-type="question"]').remove();
            item.question = $question.html();
        }
        if (item.answer) {
            const $answer = cheerio.load(item.answer, null, false);
            $answer('img[data-jta-image-type="answer"]').remove();
            $answer('.explanation, .correlation, .comments, .extra, .header, .footer, .sources, .origin, .insertion, .innervation, .action').remove();
            item.answer = $answer.html();
        }
      }

      item.deckName = premiumDeckHandler 
        ? premiumDeckHandler(details.tags, details.notebook, this.folders, this.log) 
        : this.getNotebookPath(details.notebook.id);
      
      this.log(levelDebug, `✅ Extracted item ${item.jtaID} (index: ${i})`);
      quizItems.push(item);
    });

    this.log(levelDebug, `📊 Extracted ${quizItems.length} quiz items from note ${note.id}`);
    return quizItems;
  }
}

async function* exporter(joplinClient, fromDate, log) {
  log(levelApplication, "⚠️ Using legacy exporter");
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

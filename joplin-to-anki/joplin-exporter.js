// joplin-exporter.js

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
  fields.origin = $('.origin', jtaElement).html()?.trim() || '';
  fields.insertion = $('.insertion', jtaElement).html()?.trim() || '';
  fields.innervation = $('.innervation', jtaElement).html()?.trim() || '';
  fields.action = $('.action', jtaElement).html()?.trim() || '';
  
  const questionImgEl = $('img[data-jta-image-type="question"]', jtaElement);
  if (questionImgEl.length > 0) {
    fields.questionImagePath = questionImgEl.attr('src') || '';
    fields.altText = questionImgEl.attr('alt') || '';
    log(levelDebug, `[IMAGE-EXTRACT] Found QuestionImagePath: ${fields.questionImagePath}`);
  }
    
  const answerImgEl = $('img[data-jta-image-type="answer"]', jtaElement);
  if (answerImgEl.length > 0) {
    fields.answerImagePath = answerImgEl.attr('src') || '';
    log(levelDebug, `[IMAGE-EXTRACT] Found AnswerImagePath: ${fields.answerImagePath}`);
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
    
    const validOptions = optionMatches.filter(Boolean);
    if (validOptions.length >= 2) {
      fields.optionA = optionMatches[0] || ''; 
      fields.optionB = optionMatches[1] || '';
      fields.optionC = optionMatches[2] || ''; 
      fields.optionD = optionMatches[3] || '';
    }
  }

  const correctAnswerElement = $('.correct-answer', jtaElement);
  if (correctAnswerElement.length > 0) {
    fields.correctAnswer = correctAnswerElement.html()?.trim() || '';
  }
  
  for (const key in fields) { if (!fields[key]) delete fields[key]; }
  
  return fields;
};

const enrichResourcesWithExtension = (resources) => {
  if (!resources) return [];
  return resources.map(resource => {
    if (!resource.file_extension && resource.title) {
      const parts = resource.title.split('.');
      if (parts.length > 1) {
        resource.file_extension = parts.pop();
      }
    }
    if (!resource.file_extension && resource.mime) {
        const mimeParts = resource.mime.split('/');
        if (mimeParts.length > 1) resource.file_extension = mimeParts[1];
    }
    return resource;
  });
};

const rewriteResourcePaths = (item, joplinResources) => {
    if (!joplinResources || joplinResources.length === 0) return item;
    if (!item.resourcesToUpload) item.resourcesToUpload = [];

    joplinResources.forEach(resource => {
        if (!resource || (!resource.file_extension && !resource.title)) return;
        const extension = resource.file_extension || resource.title.split('.').pop() || 'png';

        const fileName = `${resource.id}.${extension}`;
        const resourceLink = `:/${resource.id}`;
        let found = false;

        if (item.additionalFields && item.additionalFields.customFields) {
          for (const fieldName in item.additionalFields.customFields) {
            let content = item.additionalFields.customFields[fieldName];
            if (content && typeof content === 'string' && content.includes(resourceLink)) {
              item.additionalFields.customFields[fieldName] = content.replace(new RegExp(resourceLink, 'g'), fileName);
              found = true;
            }
          }
        }

        const fieldsToSearch = ['question', 'answer', 'correctAnswer', 'questionImagePath', 'answerImagePath', 'explanation', 'clinicalCorrelation', 'extra', 'header', 'footer', 'sources', 'comments', 'action', 'innervation', 'insertion', 'origin'];

        for (const fieldName of fieldsToSearch) {
            let content;
            if (['question', 'answer'].includes(fieldName)) {
                content = item[fieldName];
            } else if (item.additionalFields) {
                content = item.additionalFields[fieldName];
            }
            
            if (content && typeof content === 'string' && content.includes(resourceLink)) {
                const newContent = content.replace(new RegExp(resourceLink, 'g'), fileName);
                if (['question', 'answer'].includes(fieldName)) {
                    item[fieldName] = newContent;
                } else if (item.additionalFields) {
                    item.additionalFields[fieldName] = newContent;
                }
                found = true;
            }
        }

        if (found && !item.resourcesToUpload.find(r => r.id === resource.id)) {
            item.resourcesToUpload.push({ id: resource.id, fileName: fileName, title: resource.title });
        }
    });
    return item;
};

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
          if (folder) { path.unshift(folder.title); currentId = folder.parent_id; }
          else break;
      }
      return path.join('::');
  }
 
  async getFolderByPath(notebookPath) {
    // Ensure folders are loaded
    if (!this.folders) {
      await this.fetchFolders();
    }
    
    if (!notebookPath || notebookPath.trim() === '') {
      return null; // Cards should use tags for root-level placement
    }
    
    const pathParts = notebookPath.split('::');
    let currentFolder = null;
    
    // Start from root level (folders with no parent)
    for (let i = 0; i < pathParts.length; i++) {
      const targetTitle = pathParts[i].trim();
      
      if (i === 0) {
        // Find root level folder
        currentFolder = this.folders.find(f => 
          f.title === targetTitle && !f.parent_id
        );
      } else {
        // Find child folder
        currentFolder = this.folders.find(f => 
          f.title === targetTitle && f.parent_id === currentFolder?.id
        );
      }
      
      if (!currentFolder) {
        this.log(levelVerbose, `⚠️ Could not find folder "${targetTitle}" in path "${notebookPath}"`);
        return null;
      }
    }
    
    return currentFolder;
  }
  
    // In joplin-exporter.js
    
    // ====== START: REPLACE YOUR ENTIRE FUNCTION WITH THIS ONE ======
    async extractQuizItems(note) {
        const quizItems = [];
        const $ = cheerio.load(note.body, { decodeEntities: false });
        const jtaBlocks = $(".jta");
    
        if (jtaBlocks.length === 0) return [];
    
        this.log(levelVerbose, `🔍 Found ${jtaBlocks.length} JTA blocks in note "${note.title}"`);
        
        const details = await this.joplinClient.getNoteDetails(note.id);
        await this.fetchFolders();
        const enrichedResources = enrichResourcesWithExtension(details.resources);
    
        for (let i = 0; i < jtaBlocks.length; i++) {
            const el = jtaBlocks[i];
            const jtaID = $(el).attr("data-id");
            const noteType = $(el).attr('data-note-type') || $(el).attr('note-id');
            let item;
    
            if (!jtaID) {
                this.log(levelVerbose, `⚠️ Block at index ${i} in note "${note.title}" is missing data-id. It will be stamped by the sync engine.`);
                continue;
            }
    
            const isDynamic = dynamicMapper && noteType && dynamicMapper.getAvailableNoteTypes().includes(noteType);
    
            if (isDynamic) {
                // YOUR EXISTING LOGIC FOR DYNAMIC NOTES IS PRESERVED
                const extractedData = dynamicMapper.extractFields($(el).html(), jtaID, noteType);
                if (extractedData) {
                  item = {
                    jtaID, index: i, title: details.note.title, notebook: details.notebook, tags: details.tags, folders: this.folders,
                    question: '', answer: '',
                    additionalFields: { customNoteType: extractedData.modelName, customFields: extractedData.fields },
                    joplinNoteId: note.id,
                  };
                } else continue;
            } else {
                // THIS BLOCK IS NOW ENHANCED TO BE MORE ROBUST
                const additionalFields = extractAdditionalFieldsFromElement($, el, this.log);
                let questionHtml = $(el).find(".question").html() || $(el).find(".image-question").html() || '';
                
                // --- NEW: Intelligent Model Detection Logic ---
                let modelName = 'Joplin to Anki Basic Enhanced'; // Default
                if (additionalFields.optionA || additionalFields.optionB) {
                    modelName = 'Joplin to Anki MCQ Enhanced';
                } else if (additionalFields.questionImagePath || additionalFields.answerImagePath) {
                    modelName = 'Joplin to Anki Image Enhanced';
                } else if (questionHtml.includes('{{c') && questionHtml.includes('}}')) {
                    modelName = 'Joplin to Anki Cloze Enhanced';
                }
    
                // Trust the data-note-type attribute if it exists (from Anki->Joplin sync)
                const explicitNoteType = $(el).attr('data-note-type');
                if (explicitNoteType && explicitNoteType.includes('Enhanced')) {
                     modelName = explicitNoteType;
                }
                // --- END NEW LOGIC ---
                
                // Your original logic for cleaning options from the question field is preserved
                if (modelName === 'Joplin to Anki MCQ Enhanced') {
                  const optionRemovalPattern = /(<br\s*\/?>\s*)?(?:[A-D]\)|[A-D]\.)\s*[\s\S]*?(?=(?:<br\s*\/?>\s*)?(?:[A-D]\)|[A-D]\.)|$)/gi;
                  questionHtml = questionHtml.replace(optionRemovalPattern, '').replace(/(<br\s*\/?>|\s)*$/, '').trim();
                }
      
                item = {
                  jtaID, index: i, title: details.note.title, notebook: details.notebook, question: questionHtml,
                  answer: $(el).find(".answer-text").html() || $(el).find(".answer").html(),
                  additionalFields: additionalFields, tags: details.tags, folders: this.folders, joplinNoteId: note.id,
                };
    
                // NEW: We attach the detected model name to the item object.
                // This is the key that allows the importer to build the correct payload.
                item.additionalFields.ankiModelName = modelName;
            }
            
            const blockHtml = $(el).html();
            const contentHash = crypto.createHash('md5').update(blockHtml).digest('hex');
            item.contentHash = contentHash;
    
            rewriteResourcePaths(item, enrichedResources);
            
            // YOUR EXISTING CLEANUP LOGIC IS PRESERVED
            if (!isDynamic) {
                if (item.additionalFields.questionImagePath) {
                    const $q = cheerio.load(item.question || '', { decodeEntities: false });
                    $q('img[data-jta-image-type="question"]').remove();
                    item.question = $q('body').html().trim();
                }
    
                if (item.additionalFields.answerImagePath) {
                    const $a = cheerio.load(item.answer || '', { decodeEntities: false });
                    $a('img[data-jta-image-type="answer"]').remove();
                    item.answer = $a('body').html().trim();
                }
    
                if (item.answer) {
                    const $a = cheerio.load(item.answer, { decodeEntities: false });
                    $a('.explanation, .correlation, .comments, .extra, .header, .footer, .sources, .origin, .insertion, .innervation, .action').remove();
                    item.answer = $a('body').html();
                }
            }
    
            item.deckName = premiumDeckHandler 
              ? premiumDeckHandler(details.tags, details.notebook, this.folders, this.log) 
              : this.getNotebookPath(details.notebook.id);
            
            quizItems.push(item);
        } 
    
        return quizItems;
    }
}

async function* exporter(joplinClient, fromDate, log) {
  log(levelApplication, "✅ Using legacy one-way exporter.");
  const exporterInstance = new JoplinExporter(joplinClient, log);
  const allNotes = await joplinClient.getAllNotes("id,updated_time,title,parent_id,body");
  for (const note of allNotes) {
    try {
      const items = await exporterInstance.extractQuizItems(note);
      if (items.length > 0) {
        for (const item of items) yield { type: typeItem, data: item };
      }
    } catch (e) {
      log(levelApplication, `⚠️ Error processing note ${note.id} in legacy exporter: ${e.message}`);
      yield { type: typeError, data: e.message };
    }
  }
}

module.exports = { JoplinExporter, exporter, typeItem, typeResource, typeError, registerPremiumDeckHandler, registerDynamicMapper };

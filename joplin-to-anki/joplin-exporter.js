// Joplin Exporter - FIXED with Correct Resource Extension Extraction
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

/**
 * FIXED: Enriches resources with file_extension extracted from the title field.
 * The Joplin API returns resources with id and title, but not file_extension.
 * We extract the extension from the title (e.g., "filename.png" -> "png").
 */
const enrichResourcesWithExtension = (resources, log) => {
  if (!resources || resources.length === 0) return resources;
  
  return resources.map(resource => {
    if (!resource.file_extension && resource.title) {
      // Extract extension from title
      const parts = resource.title.split('.');
      const extension = parts.length > 1 ? parts[parts.length - 1] : '';
      
      if (extension) {
        resource.file_extension = extension;
        log(levelDebug, `[RESOURCE] Enriched resource ${resource.id}: extracted file_extension="${extension}" from title="${resource.title}"`);
      } else {
        log(levelApplication, `⚠️ Could not extract file_extension from title "${resource.title}" for resource ${resource.id}`);
      }
    }
    return resource;
  });
};

/**
 * CRITICAL FIX: This function now properly converts Joplin resource paths
 * to Anki-friendly filenames AND populates the resourcesToUpload array.
 */
const rewriteResourcePaths = (item, joplinResources, log) => {
    if (!joplinResources || joplinResources.length === 0) {
        log(levelDebug, `[RESOURCE] No resources provided for JTA ID ${item.jtaID}`);
        return item;
    }

    if (!item.resourcesToUpload) {
        item.resourcesToUpload = [];
    }

    log(levelApplication, `[RESOURCE] 🔍 Processing ${joplinResources.length} resources for JTA ID ${item.jtaID}`);

    joplinResources.forEach(resource => {
        if (!resource) {
            log(levelApplication, `⚠️ Skipping null/undefined resource`);
            return;
        }

        if (!resource.file_extension) {
            log(levelApplication, `⚠️ Skipping resource ${resource.id} - missing file_extension. Resource object: ${JSON.stringify(resource)}`);
            return;
        }

        const fileName = `${resource.id}.${resource.file_extension}`;
        const resourceLink = `:/${resource.id}`;
        let found = false;

        log(levelDebug, `[RESOURCE] Looking for "${resourceLink}" to replace with "${fileName}"`);

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
                    log(levelApplication, `[RESOURCE] ✅ Rewrote path in question field for ${fileName}`);
                } else if (fieldName === 'answer') {
                    item.answer = newContent;
                    log(levelApplication, `[RESOURCE] ✅ Rewrote path in answer field for ${fileName}`);
                } else if (item.additionalFields) {
                    item.additionalFields[fieldName] = newContent;
                    log(levelApplication, `[RESOURCE] ✅ Rewrote path in ${fieldName} field for ${fileName}`);
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
                log(levelApplication, `📎 Queued resource for upload: ${fileName} (ID: ${resource.id})`);
            }
        } else {
            log(levelDebug, `[RESOURCE] Resource ${resource.id} not found in any fields`);
        }
    });

    log(levelApplication, `[RESOURCE] 📊 Total queued for upload: ${item.resourcesToUpload.length}`);
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
    
    this.log(levelApplication, `🔍 Extracting quiz items from note ${note.id} (${note.title})`);
    
    const details = await this.joplinClient.getNoteDetails(note.id);
    await this.fetchFolders();

    this.log(levelApplication, `[RESOURCE] 📦 Note has ${details.resources?.length || 0} resources attached`);
    if (details.resources && details.resources.length > 0) {
        details.resources.forEach(r => {
            this.log(levelDebug, `[RESOURCE] - Resource ID: ${r.id}, Title: ${r.title}, Has file_extension: ${r.hasOwnProperty('file_extension')}`);
        });
    }

    // === FIX: Enrich resources with file_extension before processing ===
    const enrichedResources = enrichResourcesWithExtension(details.resources, this.log);

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
          this.log(levelDebug, `Created dynamic note item for ${jtaID}`);
        } else {
          this.log(levelApplication, `⚠️ Skipping JTA block - dynamic mapping failed for "${noteType}"`);
          return;
        }
      } else {
        const additionalFields = extractAdditionalFieldsFromElement($, el, this.log);
        
        item = {
          jtaID,
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
        this.log(levelDebug, `Created standard note item for ${jtaID}`);
      }
      
      // === STEP 2: REWRITE RESOURCE PATHS (with enriched resources) ===
      this.log(levelDebug, `[RESOURCE] About to rewrite paths for ${jtaID}...`);
      rewriteResourcePaths(item, enrichedResources, this.log);

      // === STEP 3: CLEANUP HTML ===
      if (!isDynamic) {
        if (item.question) {
            const $question = cheerio.load(item.question, null, false);
            const removedQuestionImgs = $question('img[data-jta-image-type="question"]').length;
            $question('img[data-jta-image-type="question"]').remove();
            item.question = $question.html();
            if (removedQuestionImgs > 0) {
                this.log(levelDebug, `Removed ${removedQuestionImgs} question images from HTML`);
            }
        }
        if (item.answer) {
            const $answer = cheerio.load(item.answer, null, false);
            const removedAnswerImgs = $answer('img[data-jta-image-type="answer"]').length;
            $answer('img[data-jta-image-type="answer"]').remove();
            $answer('.explanation, .correlation, .comments, .extra, .header, .footer, .sources, .origin, .insertion, .innervation, .action').remove();
            item.answer = $answer.html();
            if (removedAnswerImgs > 0) {
                this.log(levelDebug, `Removed ${removedAnswerImgs} answer images from HTML`);
            }
        }
      }

      // === STEP 4: FINALIZE ===
      item.deckName = premiumDeckHandler 
        ? premiumDeckHandler(details.tags, details.notebook, this.folders, this.log) 
        : this.getNotebookPath(details.notebook.id);
      
      this.log(levelApplication, `✅ Extracted item ${item.jtaID} with ${item.resourcesToUpload?.length || 0} resources queued`);
      quizItems.push(item);
    });

    this.log(levelApplication, `📊 Extracted ${quizItems.length} quiz items from note ${note.id}`);
    return quizItems;
  }
}

// Legacy generator function (kept for compatibility)
async function* exporter(joplinClient, fromDate, log) {
  log(levelApplication, "⚠️ Using legacy exporter - consider upgrading to JoplinExporter class");
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

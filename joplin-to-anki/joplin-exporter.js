// Joplin Exporter - FIXED VERSION (MCQ Cleanup + Image Field Preservation)

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
    log(levelDebug, `[EXTRACT] Found questionImagePath: ${fields.questionImagePath}`);
  }
  
  const answerImgEl = $('img[data-jta-image-type="answer"]', jtaElement);
  if (answerImgEl.length > 0) {
    fields.answerImagePath = answerImgEl.attr('src') || '';
    log(levelDebug, `[EXTRACT] Found answerImagePath: ${fields.answerImagePath}`);
  }
  
 // For MCQ, we extract from the plain text content of the .question div
  const questionTextContent = ($('.question', jtaElement).text() || "");
  if (questionTextContent.length > 0) {
    this.log(levelDebug, `[EXTRACT-MCQ] Checking question text for MCQ options: ${questionTextContent.substring(0, 100)}...`);
    
    const optionPatterns = [
        /(?:A\)|A\.)\s*([\s\S]*?)(?=\s*(?:B\)|B\.|$))/i, 
        /(?:B\)|B\.)\s*([\s\S]*?)(?=\s*(?:C\)|C\.|$))/i,
        /(?:C\)|C\.)\s*([\s\S]*?)(?=\s*(?:D\)|D\.|$))/i, 
        /(?:D\)|D\.)\s*([\s\S]*?)(?=\s*$)/i
    ];
    const optionMatches = optionPatterns.map(p => (questionTextContent.match(p) || [])[1]?.trim() || '');
    
    // Check if at least two options were found to consider it an MCQ
    const validOptions = optionMatches.filter(Boolean);
    if (validOptions.length >= 2) {
      this.log(levelApplication, `[EXTRACT-MCQ] ✅ Detected MCQ with ${validOptions.length} options`);
      fields.optionA = optionMatches[0] || ''; 
      fields.optionB = optionMatches[1] || '';
      fields.optionC = optionMatches[2] || ''; 
      fields.optionD = optionMatches[3] || '';
      
      // Log what we extracted
      this.log(levelDebug, `[EXTRACT-MCQ] Option A: ${fields.optionA.substring(0, 30)}...`);
      this.log(levelDebug, `[EXTRACT-MCQ] Option B: ${fields.optionB.substring(0, 30)}...`);
      if (fields.optionC) this.log(levelDebug, `[EXTRACT-MCQ] Option C: ${fields.optionC.substring(0, 30)}...`);
      if (fields.optionD) this.log(levelDebug, `[EXTRACT-MCQ] Option D: ${fields.optionD.substring(0, 30)}...`);
    } else {
      this.log(levelDebug, `[EXTRACT-MCQ] Not an MCQ - only found ${validOptions.length} options`);
    }
  }
  
  // ✅ ALSO EXTRACT CORRECT ANSWER (CRITICAL FOR MCQ DETECTION!)
  // Check for correct answer in multiple possible locations
  const correctAnswerElement = $('.correct-answer', jtaElement);
  if (correctAnswerElement.length > 0) {
    fields.correctAnswer = correctAnswerElement.text()?.trim() || '';
    this.log(levelDebug, `[EXTRACT-MCQ] Found correct answer: ${fields.correctAnswer}`);
  }
  
  for (const key in fields) { if (!fields[key]) delete fields[key]; }
  
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
          log(levelDebug, `[RESOURCE] Enriched resource ${resource.id}: extracted file_extension="${extension}" from title="${resource.title}"`);
        } else {
          log(levelApplication, `⚠️ Could not extract file_extension from title "${resource.title}" for resource ${resource.id}`);
        }
      }
      return resource;
    });
  };

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
                               'header', 'footer', 'sources', 'comments', 'action', 'innervation',
                               'insertion', 'origin');
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
  
  // PASTE THIS ENTIRE BLOCK TO REPLACE THE OLD extractQuizItems FUNCTION
  
    async extractQuizItems(note) {
        const quizItems = [];
        const $ = cheerio.load(note.body);
        const jtaBlocks = $(".jta");
    
        if (jtaBlocks.length === 0) return [];
        
        this.log(levelApplication, `🔍 Extracting quiz items from note ${note.id} (${note.title})`);
        
        const details = await this.joplinClient.getNoteDetails(note.id);
        await this.fetchFolders();
  
        const enrichedResources = enrichResourcesWithExtension(details.resources, this.log);
  
        jtaBlocks.each((i, el) => {
          const jtaID = $(el).attr("data-id") || generateUniqueID(note.id, i);
          const noteType = $(el).attr('data-note-type');
          let item;
  
          // --- ADDED LOGGING START ---
          this.log(levelDebug, `[EXPORTER-DEBUG] JTA block ${i}: found data-note-type attribute with value: "${noteType}"`);
          const isDynamic = dynamicMapper && noteType && dynamicMapper.getAvailableNoteTypes().includes(noteType);
          this.log(levelDebug, `[EXPORTER-DEBUG] JTA block ${i}: Is this a dynamic note? -> ${isDynamic}`);
          // --- ADDED LOGGING END ---
  
          if (isDynamic) {
            this.log(levelDebug, `[EXPORTER-DEBUG] Processing block ${i} as a DYNAMIC note.`);
            const extractedData = dynamicMapper.extractFields($(el).html(), jtaID, noteType);
            if (extractedData) {
              item = {
                jtaID,
                index: i,
                title: details.note.title,
                notebook: details.notebook,
                tags: details.tags,
                folders: this.folders,
                question: '',
                answer: '',
                additionalFields: {
                  customNoteType: extractedData.modelName,
                  customFields: extractedData.fields,
                  joplinNoteID: note.id,
                },
              };
              this.log(levelDebug, `[EXPORTER-DEBUG] Successfully created DYNAMIC item object for ${jtaID}.`);
            } else {
              this.log(levelApplication, `⚠️ Skipping JTA block - dynamic mapping failed for "${noteType}"`);
              return;
            }
          } else {
            this.log(levelDebug, `[EXPORTER-DEBUG] Processing block ${i} as a STANDARD note.`);
            const additionalFields = extractAdditionalFieldsFromElement($, el, this.log);
            
            // --- FIX START: Improved Question Extraction for Image Notes ---
            const isImageNote = additionalFields.questionImagePath || additionalFields.answerImagePath;
            const questionSelector = isImageNote ? ".image-question" : ".question";
            let questionHtml = $(el).find(questionSelector).html() || '';
            // --- FIX END ---
            
            if (additionalFields.optionA || additionalFields.optionB || additionalFields.optionC || additionalFields.optionD) {
              this.log(levelDebug, `[EXTRACT-MCQ] Cleaning options from question HTML...`);
              this.log(levelDebug, `[EXTRACT-MCQ] Original question HTML length: ${questionHtml.length}`);
              
              // ✅ EXTRACT AND PRESERVE IMAGES BEFORE CLEANING OPTIONS
              const $tempQuestion = cheerio.load(questionHtml, { decodeEntities: false });
              const images = $tempQuestion('img');
              const extractedImages = [];
              
              images.each((i, img) => {
                const imgHtml = $tempQuestion.html(img);
                extractedImages.push(imgHtml);
                this.log(levelDebug, `[EXTRACT-MCQ] Preserved image ${i}: ${imgHtml.substring(0, 50)}...`);
              });
              
              // Remove images temporarily
              images.remove();
              let cleanedHtml = $tempQuestion.html();
              
              // Clean the options
              const optionRemovalPattern = /(<br\s*\/?>\s*)?(?:[A-D]\)|[A-D]\.)\s*[\s\S]*?(?=(?:<br\s*\/?>\s*)?(?:[A-D]\)|[A-D]\.)|$)/gi;
              cleanedHtml = cleanedHtml.replace(optionRemovalPattern, '');
              cleanedHtml = cleanedHtml.replace(/(<br\s*\/?>|\s)*$/, '').trim();
              
              // ✅ RE-ADD IMAGES AFTER CLEANING
              if (extractedImages.length > 0) {
                questionHtml = cleanedHtml + '\n' + extractedImages.join('\n');
                this.log(levelApplication, `[EXTRACT-MCQ] ✅ Preserved ${extractedImages.length} image(s) in MCQ question`);
              } else {
                questionHtml = cleanedHtml;
              }
              
              this.log(levelDebug, `[EXTRACT-MCQ] Cleaned question HTML length: ${questionHtml.length}`);
            }
  
            item = {
              jtaID,
              index: i,
              title: details.note.title,
              notebook: details.notebook,
              question: questionHtml,
              answer: $(el).find(".answer").html() || '',
              additionalFields: additionalFields,
              tags: details.tags,
              folders: this.folders,
              joplinNoteId: note.id,
            };
            this.log(levelDebug, `[EXPORTER-DEBUG] Successfully created STANDARD item object for ${jtaID}`);
          }
          
          // --- ADDED LOGGING START ---
          this.log(levelDebug, `[EXPORTER-DEBUG] Item object for ${jtaID} BEFORE resource rewrite: ${JSON.stringify(item, null, 2)}`);
          // --- ADDED LOGGING END ---
  
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
        
        this.log(levelApplication, `✅ Extracted item ${item.jtaID} with ${item.resourcesToUpload?.length || 0} resources queued`);
        
        quizItems.push(item);
      });
  
      this.log(levelApplication, `📊 Extracted ${quizItems.length} quiz items from note ${note.id}`);
      return quizItems;
    }
}

async function* exporter(joplinClient, fromDate, log) {
  log(levelApplication, "✅ Using legacy one-way exporter.");

  const exporterInstance = new JoplinExporter(joplinClient, log);

  const allNotes = await joplinClient.getAllNotes(
    "id,updated_time,title,parent_id,body"
  );
  log(levelVerbose, `Legacy exporter found ${allNotes.length} total notes to check.`);

  for (const note of allNotes) {
    try {
      const items = await exporterInstance.extractQuizItems(note);

      if (items.length > 0) {
        log(levelApplication, `   -> Found ${items.length} item(s) in note "${note.title}"`);
        for (const item of items) {
          // The legacy runner expects the data in this specific format.
          yield { type: typeItem, data: item };
        }
      }
    } catch (e) {
      log(levelApplication, `⚠️ Error processing note ${note.id} in legacy exporter: ${e.message}`);
      yield { type: typeError, data: e.message };
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

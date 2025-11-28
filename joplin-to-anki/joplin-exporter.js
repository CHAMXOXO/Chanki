const cheerio = require('cheerio');
const crypto = require('crypto');
const { levelApplication, levelVerbose, levelDebug } = require('./log');

const typeItem = 'item';
const typeResource = 'resource';
const typeError = 'error';

let premiumDeckHandler = null;
let dynamicMapper = null;

function registerPremiumDeckHandler(handler) { premiumDeckHandler = handler; }
function registerDynamicMapper(mapper) { dynamicMapper = mapper; }

/**
 * Detects note type from HTML structure (Premium failsafe for missing data-note-type)
 * Only detects major types: MCQ, Cloze, Image, Basic
 */
const detectNoteType = ($, el) => {
  // Check for MCQ structure (options)
  if ($('.option-a, .option-b, .option-c, .option-d', el).length > 0) {
    return 'Joplin to Anki MCQ Enhanced';
  }
  
  // Check for Image structure (data-jta-image-type attribute)
  if ($('img[data-jta-image-type]', el).length > 0) {
    return 'Joplin to Anki Image Enhanced';
  }
  
  // Check for Cloze structure ({{c1::text}} syntax)
  const questionHtml = $(el).find('.question').html() || '';
  if (questionHtml.includes('{{c') && questionHtml.includes('}}')) {
    return 'Joplin to Anki Cloze Enhanced';
  }
  
  // Default to Basic Enhanced
  return 'Joplin to Anki Basic Enhanced';
};

// Utility to extract fields for Basic notes (Legacy/Core only)
const extractAdditionalFieldsFromElement = ($, jtaElement) => {
  const fields = { explanation: '', clinicalCorrelation: '', header: '', footer: '', sources: '' };
  fields.header = $('.header', jtaElement).html()?.trim() || '';
  fields.footer = $('.footer', jtaElement).html()?.trim() || '';
  fields.sources = $('.sources', jtaElement).html()?.trim() || '';
  fields.explanation = $('.explanation', jtaElement).html()?.trim() || '';
  fields.clinicalCorrelation = $('.correlation', jtaElement).html()?.trim() || '';
  return fields;
};

// FIXED: Now searches additionalFields to fix broken images in Explanation/Clinical fields
const rewriteResourcePaths = (item, joplinResources) => {
    if (!joplinResources || joplinResources.length === 0) return item;
    if (!item.resourcesToUpload) item.resourcesToUpload = [];

    joplinResources.forEach(resource => {
        if (!resource || (!resource.file_extension && !resource.title)) return;
        const extension = resource.file_extension || resource.title.split('.').pop() || 'png';
        const fileName = `${resource.id}.${extension}`;
        const resourceLink = `:/${resource.id}`;
        let found = false;

        // 1. Search Custom Fields (Premium)
        if (item.additionalFields && item.additionalFields.customFields) {
          for (const fieldName in item.additionalFields.customFields) {
            let content = item.additionalFields.customFields[fieldName];
            if (content && typeof content === 'string' && content.includes(resourceLink)) {
              item.additionalFields.customFields[fieldName] = content.replace(new RegExp(resourceLink, 'g'), fileName);
              found = true;
            }
          }
        }

        // 2. Search Standard Fields (Core/Legacy)
        const directFields = ['question', 'answer'];
        const additionalFields = ['explanation', 'clinicalCorrelation', 'header', 'footer', 'sources'];

        // Check direct fields (Question/Answer)
        for (const fieldName of directFields) {
            if (item[fieldName] && typeof item[fieldName] === 'string' && item[fieldName].includes(resourceLink)) {
                item[fieldName] = item[fieldName].replace(new RegExp(resourceLink, 'g'), fileName);
                found = true;
            }
        }

        // Check additional fields (Explanation, etc)
        if (item.additionalFields) {
            for (const fieldName of additionalFields) {
                if (item.additionalFields[fieldName] && typeof item.additionalFields[fieldName] === 'string' && item.additionalFields[fieldName].includes(resourceLink)) {
                    item.additionalFields[fieldName] = item.additionalFields[fieldName].replace(new RegExp(resourceLink, 'g'), fileName);
                    found = true;
                }
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
    if (!this.folders) await this.fetchFolders();
    if (!notebookPath || notebookPath.trim() === '') return null;
    
    const pathParts = notebookPath.split('::');
    let currentFolder = null;
    
    for (let i = 0; i < pathParts.length; i++) {
      const targetTitle = pathParts[i].trim();
      if (i === 0) {
        currentFolder = this.folders.find(f => f.title === targetTitle && !f.parent_id);
      } else {
        currentFolder = this.folders.find(f => f.title === targetTitle && f.parent_id === currentFolder?.id);
      }
      if (!currentFolder) return null;
    }
    return currentFolder;
  }
  
    async extractQuizItems(note) {
        const quizItems = [];
        const $ = cheerio.load(note.body, { decodeEntities: false });
        const jtaBlocks = $(".jta");
        if (jtaBlocks.length === 0) return [];
    
        const details = await this.joplinClient.getNoteDetails(note.id);
        await this.fetchFolders();
        
        for (let i = 0; i < jtaBlocks.length; i++) {
            const el = jtaBlocks[i];
            let jtaID = $(el).attr("data-id");
            let item;
    
            if (!jtaID) {
                jtaID = `auto_${note.id}_${i}`; 
            }
    
            // --- STEP 1: Determine Note Type ---
            let noteType = $(el).attr('data-note-type');
            
            // Failsafe: Auto-detect if missing (Premium only)
            if (!noteType && dynamicMapper && dynamicMapper.isLoaded()) {
                const detected = detectNoteType($, el);
                
                // Warn user if detection happened (use levelApplication so they see it)
                if (detected !== 'Joplin to Anki Basic Enhanced') {
                    this.log(levelApplication, `⚠️  Block ${jtaID}: Missing data-note-type attribute, auto-detected as "${detected}"`);
                    this.log(levelApplication, `   💡 Tip: Add data-note-type="${detected}" to your block to avoid auto-detection.`);
                }
                
                noteType = detected;
            }
            
            // Final fallback (Legacy users or undetectable types)
            if (!noteType) {
                noteType = 'Joplin to Anki Basic Enhanced';
            }

            // --- STEP 2: Route to Correct Extractor ---
            const isPremium = dynamicMapper && dynamicMapper.isLoaded();
            const isCustomModel = isPremium && dynamicMapper.getAvailableNoteTypes().includes(noteType);

            // 1. PREMIUM DYNAMIC EXPORTER
            if (isCustomModel) {
                const extractedData = dynamicMapper.extractFields($(el).html(), jtaID, noteType);
                if (extractedData) {
                  item = {
                    jtaID, index: i, title: details.note.title, notebook: details.notebook, tags: details.tags, folders: this.folders,
                    question: '', answer: '', // Not used for custom models
                    additionalFields: { customNoteType: extractedData.modelName, customFields: extractedData.fields },
                    joplinNoteId: note.id,
                  };
                } else {
                    // Dynamic mapper failed (missing required fields, etc.)
                    this.log(levelApplication, `❌ Failed to extract custom note type "${noteType}" for block ${jtaID}. Skipping.`);
                    continue;
                }
            } 
            // 2. CORE LEGACY EXPORTER (Fallback to Basic Enhanced)
            else {
                const additionalFields = extractAdditionalFieldsFromElement($, el);
                let questionHtml = $(el).find(".question").html() || '';
                let answerHtml = $(el).find(".answer-text").html() || '';
                
                // Only create if we have content
                if (questionHtml || answerHtml) {
                    item = {
                      jtaID, index: i, title: details.note.title, notebook: details.notebook, 
                      question: questionHtml, answer: answerHtml,
                      additionalFields: {
                          ...additionalFields,
                          ankiModelName: 'Joplin to Anki Basic Enhanced'
                      },
                      tags: details.tags, folders: this.folders, joplinNoteId: note.id,
                    };
                }
            }
            
            if (item) {
                const blockHtml = $(el).html();
                item.contentHash = crypto.createHash('md5').update(blockHtml).digest('hex');
                rewriteResourcePaths(item, details.resources);
                
                // Deck Handler
                item.deckName = premiumDeckHandler 
                  ? premiumDeckHandler(details.tags, details.notebook, this.folders, this.log, {levelApplication, levelVerbose, levelDebug}) 
                  : this.getNotebookPath(details.notebook.id);
                
                quizItems.push(item);
            }
        } 
        return quizItems;
    }
}

async function* exporter(joplinClient, fromDate, log) {
  const exporterInstance = new JoplinExporter(joplinClient, log);
  const allNotes = await joplinClient.getAllNotes("id,updated_time,title,parent_id,body");
  for (const note of allNotes) {
    try {
      const items = await exporterInstance.extractQuizItems(note);
      if (items.length > 0) {
        for (const item of items) yield { type: typeItem, data: item };
      }
    } catch (e) {
      yield { type: typeError, data: e.message };
    }
  }
}

module.exports = { JoplinExporter, exporter, typeItem, typeResource, typeError, registerPremiumDeckHandler, registerDynamicMapper };

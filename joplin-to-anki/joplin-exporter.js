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

const rewriteResourcePaths = (item, joplinResources) => {
    if (!joplinResources || joplinResources.length === 0) return item;
    if (!item.resourcesToUpload) item.resourcesToUpload = [];

    joplinResources.forEach(resource => {
        if (!resource || (!resource.file_extension && !resource.title)) return;
        const extension = resource.file_extension || resource.title.split('.').pop() || 'png';
        const fileName = `${resource.id}.${extension}`;
        const resourceLink = `:/${resource.id}`;
        let found = false;

        // Search Custom Fields
        if (item.additionalFields && item.additionalFields.customFields) {
          for (const fieldName in item.additionalFields.customFields) {
            let content = item.additionalFields.customFields[fieldName];
            if (content && typeof content === 'string' && content.includes(resourceLink)) {
              item.additionalFields.customFields[fieldName] = content.replace(new RegExp(resourceLink, 'g'), fileName);
              found = true;
            }
          }
        }

        // Search Standard Fields
        const fieldsToSearch = ['question', 'answer'];
        for (const fieldName of fieldsToSearch) {
            if (item[fieldName] && item[fieldName].includes(resourceLink)) {
                item[fieldName] = item[fieldName].replace(new RegExp(resourceLink, 'g'), fileName);
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
            const jtaID = $(el).attr("data-id");
            // Anki Sync marks the model name. If not present, assume Basic.
            const noteType = $(el).attr('data-note-type') || 'Joplin to Anki Basic Enhanced';
            let item;
    
            if (!jtaID) continue; // Will be stamped by sync engine
    
            // 1. PREMIUM DYNAMIC EXPORTER
            if (dynamicMapper && dynamicMapper.getAvailableNoteTypes().includes(noteType)) {
                const extractedData = dynamicMapper.extractFields($(el).html(), jtaID, noteType);
                if (extractedData) {
                  item = {
                    jtaID, index: i, title: details.note.title, notebook: details.notebook, tags: details.tags, folders: this.folders,
                    question: '', answer: '', // Populated in custom fields
                    additionalFields: { customNoteType: extractedData.modelName, customFields: extractedData.fields },
                    joplinNoteId: note.id,
                  };
                }
            } 
            // 2. CORE LEGACY EXPORTER (Fallback to Basic)
            else {
                const additionalFields = extractAdditionalFieldsFromElement($, el);
                let questionHtml = $(el).find(".question").html() || '';
                let answerHtml = $(el).find(".answer-text").html() || '';
                
                if (questionHtml && answerHtml) {
                    item = {
                      jtaID, index: i, title: details.note.title, notebook: details.notebook, 
                      question: questionHtml, answer: answerHtml,
                      additionalFields: additionalFields, tags: details.tags, folders: this.folders, joplinNoteId: note.id,
                    };
                    item.additionalFields.ankiModelName = 'Joplin to Anki Basic Enhanced';
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

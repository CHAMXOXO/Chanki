// joplin-client.js - COMPLETE VERSION with Logging Fix

const axios = require("axios");
const fs = require('fs').promises;
const path = require('path');
const FormData = require('form-data');
const { levelApplication, levelVerbose, levelDebug } = require("./log");

const healthyPingResponse = "JoplinClipperServer";

const newClient = (url, token, log) => {
  if (!url) {
    throw new Error("No url for Joplin Api provided");
  }
  if (!token) {
    throw new Error("No token for Joplin Api provided");
  }

  const axiosInstance = axios.create({
    baseURL: url,
    timeout: 30000,
    maxRedirects: 3,
    headers: {
      'User-Agent': 'JoplinAnkiSync/2.0',
      'Connection': 'keep-alive',
      'Keep-Alive': 'timeout=30'
    },
    maxContentLength: Infinity,
    maxBodyLength: Infinity,
    httpAgent: new (require('http').Agent)({
      keepAlive: true,
      keepAliveMsecs: 30000,
      maxSockets: 5,
      maxFreeSockets: 2,
      timeout: 30000,
      freeSocketTimeout: 30000
    }),
    httpsAgent: new (require('https').Agent)({
      keepAlive: true,
      keepAliveMsecs: 30000,
      maxSockets: 5,
      maxFreeSockets: 2,
      timeout: 30000,
      freeSocketTimeout: 30000
    })
  });

  const makeRequestWithRetry = async (config, maxRetries = 5) => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        log(levelDebug, `Request attempt ${attempt}/${maxRetries}: ${config.method} ${config.url}`);
        const response = await axiosInstance(config);
        log(levelDebug, `Request successful on attempt ${attempt}`);
        return response.data;
      } catch (error) {
        const isLastAttempt = attempt === maxRetries;
        
        if (error.code === 'ECONNRESET' || 
            error.code === 'EPIPE' || 
            error.code === 'ECONNABORTED' ||
            error.message.includes('socket hang up') ||
            error.message.includes('timeout')) {
          
          log(levelVerbose, `Connection error on attempt ${attempt}: ${error.message}`);
          
          if (!isLastAttempt) {
            const backoffDelay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
            log(levelDebug, `Retrying in ${backoffDelay}ms...`);
            await new Promise(resolve => setTimeout(resolve, backoffDelay));
            continue;
          }
        }
        
        if (isLastAttempt) {
          log(levelApplication, `Request failed after ${maxRetries} attempts: ${error.message}`);
          throw error;
        }
      }
    }
  };

  const client = {
    url,
    token,
    log,
    axiosInstance,

    ping() {
      return makeRequestWithRetry({
        method: 'GET',
        url: '/ping'
      });
    },

    paramsGen(fields, page = 1, limit = 100, orderBy = 'updated_time', orderDir = 'DESC') {
      const params = new URLSearchParams();
      params.append('token', this.token);
      if (fields) params.append('fields', fields);
      params.append('page', page.toString());
      params.append('limit', limit.toString());
      params.append('order_by', orderBy);
      params.append('order_dir', orderDir);
      return params.toString();
    },

    urlGen(resource, id, subResource) {
      let path = `/${resource}`;
      if (id) path += `/${id}`;
      if (subResource) path += `/${subResource}`;
      return path;
    },

    async request(url, method = 'GET', body, fields, parseJSON = true, encoding, page = 1, limit = 100) {
      const params = this.paramsGen(fields, page, limit);
      const fullUrl = `${url}?${params}`;
      
      const config = {
        method,
        url: fullUrl,
        responseType: encoding === 'binary' ? 'arraybuffer' : 'json'
      };

      if (body) {
        config.data = body;
        config.headers = { 'Content-Type': 'application/json' };
      }

      const response = await makeRequestWithRetry(config);
      
      if (encoding === 'binary') {
        return Buffer.from(response).toString('base64');
      }
      
      return response;
    },

    async getAllNotes(fields = "id,updated_time,title,parent_id", fromDate = null) {
      let allNotes = [];
      let page = 1;
      const limit = 50;
      let hasMore = true;

      while (hasMore) {
        try {
          log(levelDebug, `Fetching notes page ${page} (limit: ${limit})`);
          
          const response = await this.request(
            this.urlGen("notes"),
            "GET",
            undefined,
            fields,
            true,
            undefined,
            page,
            limit
          );

          const notes = response.items || response;
          
          if (!Array.isArray(notes) || notes.length === 0) {
            hasMore = false;
            break;
          }

          const filteredNotes = fromDate ? 
            notes.filter(note => new Date(note.updated_time) >= fromDate) : 
            notes;

          allNotes = allNotes.concat(filteredNotes);
          
          if (notes.length < limit) {
            hasMore = false;
          } else {
            page++;
          }

          await new Promise(resolve => setTimeout(resolve, 100));
          
        } catch (error) {
          log(levelApplication, `Error fetching notes page ${page}: ${error.message}`);
          throw error;
        }
      }

      log(levelVerbose, `Retrieved ${allNotes.length} total notes`);
      return allNotes;
    },

    async getNoteDetails(noteId) {
      try {
        log(levelDebug, `Fetching details for note ${noteId}`);
        
        const [fullNote, allFolders] = await Promise.all([
          this.request(
            this.urlGen("notes", noteId),
            "GET",
            undefined,
            "id,title,body,parent_id,updated_time,user_updated_time"
          ),
          this.request(
            this.urlGen("folders", null),
            "GET",
            undefined,
            "id,title,parent_id"
          )
        ]);

        const [tagsResponse, resourcesResponse] = await Promise.all([
          this.request(
            this.urlGen("notes", noteId, "tags"),
            "GET",
            undefined,
            "id,title"
          ).catch(error => {
            log(levelVerbose, `Warning: Could not fetch tags for note ${noteId}: ${error.message}`);
            return [];
          }),
          this.request(
            this.urlGen("notes", noteId, "resources"),
            "GET",
            undefined,
            "id,title,file_extension,mime,filename"
          ).catch(error => {
            log(levelVerbose, `Warning: Could not fetch resources for note ${noteId}: ${error.message}`);
            return [];
          })
        ]);

        const tags = Array.isArray(tagsResponse) ? 
          tagsResponse.map(tag => tag.title || tag) : 
          (Array.isArray(tagsResponse?.items) ? tagsResponse.items.map(tag => tag.title || tag) : []);
          
        log(levelApplication, `Retrieved tags for note ${noteId}: ${JSON.stringify(tags)}`);

        const foldersArray = Array.isArray(allFolders) ? allFolders : 
          (Array.isArray(allFolders?.items) ? allFolders.items : []);
        
        const notebook = foldersArray.find(folder => folder.id === fullNote.parent_id) || 
          { title: "Unknown", id: fullNote.parent_id };

        const resources = Array.isArray(resourcesResponse) ? resourcesResponse : 
          (Array.isArray(resourcesResponse?.items) ? resourcesResponse.items : []);

        log(levelDebug, `[DIAGNOSTIC] Raw resourcesResponse structure: ${JSON.stringify(resourcesResponse, null, 2)}`);
        
        resources.forEach((resource, idx) => {
          log(levelDebug, `[DIAGNOSTIC] Resource ${idx}:`);
          // FIX: Corrected log to check for 'mime' instead of 'mime_type' to align with API response.
          log(levelDebug, `  Has mime? ${resource.hasOwnProperty('mime')}`);
        });

        return {
          note: fullNote,
          notebook: notebook,
          tags: tags,
          resources: resources,
          folders: foldersArray
        };
      } catch (error) {
        log(levelApplication, `Error fetching note details for ${noteId}: ${error.message}`);
        throw error;
      }
    },

    async getAllFolders() {
      try {
        const response = await this.request(
          this.urlGen("folders"),
          "GET",
          undefined,
          "id,title,parent_id"
        );
        
        return Array.isArray(response) ? response : 
          (Array.isArray(response?.items) ? response.items : []);
      } catch (error) {
        log(levelApplication, `Error fetching folders: ${error.message}`);
        return [];
      }
    },

    async updateNoteBody(noteId, newBody) {
      try {
        this.log(levelVerbose, `Updating note body for ID: ${noteId}`);
        const response = await this.request(
          this.urlGen("notes", noteId),
          "PUT",
          { body: newBody },
          "id,updated_time"
        );
        return response;
      } catch (error) {
        this.log(levelApplication, `Error updating note body for ${noteId}: ${error.message}`);
        throw error;
      }
    },

    async createResource(buffer, filename, mimeType, noteId = null) {
      const form = new FormData();
      
      form.append('data', buffer, {
        filename: filename,
        contentType: mimeType
      });
      
      const props = {
        title: filename,
        mime: mimeType
      };
      form.append('props', JSON.stringify(props));
      
      try {
        const params = new URLSearchParams();
        params.append('token', this.token);
        
        const config = {
          method: 'POST',
          url: `/resources?${params.toString()}`,
          data: form,
          headers: {
            ...form.getHeaders()
          },
          maxContentLength: Infinity,
          maxBodyLength: Infinity
        };
        
        const response = await makeRequestWithRetry(config);
        
        this.log(levelDebug, `Created resource: ${response.id} (${filename})`);
        
        if (noteId && response.id) {
          await this.attachResourceToNote(response.id, noteId);
        }
        
        return response;
      } catch (error) {
        this.log(levelApplication, `❌ Failed to create resource: ${error.message}`);
        throw error;
      }
    },

    async attachResourceToNote(resourceId, noteId) {
      try {
        const params = new URLSearchParams();
        params.append('token', this.token);
        
        await makeRequestWithRetry({
          method: 'POST',
          url: `/notes/${noteId}/resources?${params.toString()}`,
          data: { id: resourceId },
          headers: { 'Content-Type': 'application/json' }
        });
        
        this.log(levelDebug, `Attached resource ${resourceId} to note ${noteId}`);
      } catch (error) {
        this.log(levelVerbose, `Could not attach resource to note: ${error.message}`);
      }
    },

    async health() {
      try {
        const response = await this.ping();
        if (response !== healthyPingResponse && response.message !== healthyPingResponse) {
          throw new Error(
            `Did not receive expected response from Joplin Web Clipper API at ${this.url}/ping\nResponse: ${JSON.stringify(response)}\nExiting.`
          );
        }
        this.log(levelVerbose, "Joplin API Healthy");
      } catch (error) {
        throw new Error(
          `Health check failed for Joplin API at ${this.url}: ${error.message}`
        );
      }
    },
  };

  return client;
};

module.exports = {
  newClient,
};

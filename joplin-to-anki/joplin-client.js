const axios = require("axios");
const { levelApplication, levelVerbose, levelDebug } = require("./log");

const healthyPingResponse = "JoplinClipperServer";

const newClient = (url, token, log) => {
  if (!url) {
    throw new Error("No url for Joplin Api provided");
  }
  if (!token) {
    throw new Error("No token for Joplin Api provided");
  }

  // Create axios instance with enhanced configuration for socket hangup prevention
  const axiosInstance = axios.create({
    baseURL: url,
    timeout: 30000, // 30 second timeout
    maxRedirects: 3,
    headers: {
      'User-Agent': 'JoplinAnkiSync/2.0',
      'Connection': 'keep-alive',
      'Keep-Alive': 'timeout=30'
    },
    // Enhanced retry configuration
    maxContentLength: Infinity,
    maxBodyLength: Infinity,
    // Socket configuration to prevent hangups
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

  // Enhanced retry mechanism with exponential backoff
  const makeRequestWithRetry = async (config, maxRetries = 5) => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        log(levelDebug, `Request attempt ${attempt}/${maxRetries}: ${config.method} ${config.url}`);
        
        const response = await axiosInstance(config);
        
        // Log successful request
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

  return {
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

    // Enhanced method to get all notes with pagination
    async getAllNotes(fields = "id,updated_time,title,parent_id", fromDate = null) {
      let allNotes = [];
      let page = 1;
      const limit = 50; // Smaller chunks to prevent timeouts
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

          // Filter by date if provided
          const filteredNotes = fromDate ? 
            notes.filter(note => new Date(note.updated_time) >= fromDate) : 
            notes;

          allNotes = allNotes.concat(filteredNotes);
          
          // Check if we got fewer notes than requested (end of pages)
          if (notes.length < limit) {
            hasMore = false;
          } else {
            page++;
          }

          // Add small delay between requests to prevent overwhelming the server
          await new Promise(resolve => setTimeout(resolve, 100));
          
        } catch (error) {
          log(levelApplication, `Error fetching notes page ${page}: ${error.message}`);
          throw error;
        }
      }

      log(levelVerbose, `Retrieved ${allNotes.length} total notes`);
      return allNotes;
    },

    // FIXED: Enhanced method to get note details with proper tag and notebook extraction
    async getNoteDetails(noteId) {
      try {
        log(levelDebug, `Fetching details for note ${noteId}`);
        
        // Get note details and folders in parallel
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

        // Get tags and resources separately to avoid timeout issues
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
            "GET"
          ).catch(error => {
            log(levelVerbose, `Warning: Could not fetch resources for note ${noteId}: ${error.message}`);
            return [];
          })
        ]);

        // Extract tags properly
        const tags = Array.isArray(tagsResponse) ? 
          tagsResponse.map(tag => tag.title || tag) : 
          (Array.isArray(tagsResponse?.items) ? tagsResponse.items.map(tag => tag.title || tag) : []);

        // Find the correct notebook from folders
        const foldersArray = Array.isArray(allFolders) ? allFolders : 
          (Array.isArray(allFolders?.items) ? allFolders.items : []);
        
        const notebook = foldersArray.find(folder => folder.id === fullNote.parent_id) || 
          { title: "Unknown", id: fullNote.parent_id };

        // Extract resources properly
        const resources = Array.isArray(resourcesResponse) ? resourcesResponse : 
          (Array.isArray(resourcesResponse?.items) ? resourcesResponse.items : []);

        // DEBUG: Log what we extracted
        log(levelDebug, `Note details extracted:
          - Note ID: ${noteId}
          - Title: ${fullNote.title}
          - Notebook: ${notebook.title} (${notebook.id})
          - Tags: ${JSON.stringify(tags)}
          - Resources: ${resources.length}`);

        return {
          note: fullNote,
          notebook: notebook,
          tags: tags,
          resources: resources,
          folders: foldersArray // Pass all folders for hierarchy building
        };
      } catch (error) {
        log(levelApplication, `Error fetching note details for ${noteId}: ${error.message}`);
        throw error;
      }
    },

    // Get all folders for hierarchy mapping
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
};

module.exports = {
  newClient,
};

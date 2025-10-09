const fs = require('fs');

// Read the file
let content = fs.readFileSync('anki-client.js', 'utf8');

// Replace the health function
content = content.replace(
  /async health\(\) \{[\s\S]*?this\.log\(levelVerbose, "Anki Connect API Healthy"\);\s*\}/,
  `async health() {
      const result = await this.ping();
      let response;
      try {
        response = JSON.parse(result);
        if (response.apiVersion !== "AnkiConnect v.6") {
          throw new Error(
            \`Did not receive expected response from Anki Connect API at \${this.url}\\nResponse: \${result}\\nExiting.\`
          );
        }
      } catch (e) {
        if (result !== "AnkiConnect v.6") {
          throw new Error(
            \`Did not receive expected response from Anki Connect API at \${this.url}\\nResponse: \${result}\\nExiting.\`
          );
        }
      }
      this.log(levelVerbose, "Anki Connect API Healthy");
    }`
);

// Write the file back
fs.writeFileSync('anki-client.js', content);
console.log('Fixed health check function');

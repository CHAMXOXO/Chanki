// log.js
const fs = require('fs');
const path = require('path');

const LogLevel = {
    NONE: 0,
    APPLICATION: 1, // High-level operational messages
    VERBOSE: 2,     // More detailed operational messages
    DEBUG: 3        // All internal debugging messages
};

// --- IMPORTANT: Default log level set to DEBUG ---
// This ensures you get verbose output by default without needing to configure it externally.
let currentLevel = LogLevel.DEBUG; 

// Get the log file path from environment variable or default
// You can set JTA_LOG_FILE=/path/to/your/log.log if you want to override this
const LOG_FILE_PATH = process.env.JTA_LOG_FILE || path.join(__dirname, 'jta_sync.log');

// Ensure the log file directory exists
const logDir = path.dirname(LOG_FILE_PATH);
if (!fs.existsSync(logDir)) {
    try {
        fs.mkdirSync(logDir, { recursive: true });
    } catch (error) {
        console.error(`Failed to create log directory ${logDir}:`, error);
    }
}

const writeToLogFile = (message) => {
    try {
        fs.appendFileSync(LOG_FILE_PATH, `${message}\n`);
    } catch (error) {
        console.error('Failed to write to log file:', error);
    }
};

/**
 * Logs a message if its level is less than or equal to the current global log level.
 * Messages are always printed to console and written to a file.
 * @param {number} level - The log level of the message (e.g., LogLevel.DEBUG).
 * @param {string} message - The message to log.
 */
const log = (level, message) => {
    if (level <= currentLevel) {
        const timestamp = new Date().toISOString();
        let levelTag = '';
        switch (level) {
            case LogLevel.APPLICATION:
                levelTag = '[APP]';
                break;
            case LogLevel.VERBOSE:
                levelTag = '[VERB]';
                break;
            case LogLevel.DEBUG:
                levelTag = '[DEBUG]';
                break;
            case LogLevel.NONE: // Should ideally not be used for logging messages
            default:
                levelTag = '[INFO]';
        }
        const logMessage = `${timestamp} ${levelTag} ${message}`;
        console.log(logMessage); // Always log to console
        writeToLogFile(logMessage); // Always write to file
    }
};

/**
 * Sets the global logging level.
 * @param {number} level - The new log level.
 */
const setLevel = (level) => {
    if (Object.values(LogLevel).includes(level)) {
        currentLevel = level;
        log(LogLevel.APPLICATION, `Log level set to: ${Object.keys(LogLevel).find(key => LogLevel[key] === level)}`);
    } else {
        console.warn(`Invalid log level: ${level}. Keeping current level: ${Object.keys(LogLevel).find(key => LogLevel[key] === currentLevel)}`);
    }
};

module.exports = {
    levelNone: LogLevel.NONE,
    levelApplication: LogLevel.APPLICATION,
    levelVerbose: LogLevel.VERBOSE,
    levelDebug: LogLevel.DEBUG,
    log, // Export the direct log function
    setLevel,
    getLogFilePath: () => LOG_FILE_PATH
};

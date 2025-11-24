// log.js - SYNTAX CORRECTED
const fs = require('fs');
const path = require('path');
const chalk = require('chalk'); 

const LogLevel = { NONE: 0, APPLICATION: 1, VERBOSE: 2, DEBUG: 3 };
let currentLevel = LogLevel.APPLICATION;

const LOG_FILE_PATH = process.env.JTA_LOG_FILE || path.join(__dirname, '..', 'jta_sync.log');
const logDir = path.dirname(LOG_FILE_PATH);

if (!fs.existsSync(logDir)) {
    try { 
        fs.mkdirSync(logDir, { recursive: true }); 
    } catch (error) { 
        console.error('Failed to create log directory:', error); z
    }
}

const writeToLogFile = (message) => {
    try {
        const plain = String(message).replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '');
        fs.appendFileSync(LOG_FILE_PATH, `${plain}\n`);
    } catch (error) { 
        console.error('Failed to write to log file:', error); 
    }
};

const log = (level, message) => {
    // Validation logicz
    if (typeof level !== 'number' || !Object.values(LogLevel).includes(level)) {
        const warningMessage = `[LOGGER-ERROR] log() function called with invalid level. Level: ${level}, Message: ${message}`;
        console.error(chalk.red.bold(warningMessage));
        writeToLogFile(new Date().toISOString() + ' ' + warningMessage);
        level = LogLevel.APPLICATION;
        message = `(INVALID LOG CALL) ${message || level}`;
    }
    
    if (level > currentLevel) return;
    
    if (message === undefined || message === null) {
        message = String(message);
    } else if (typeof message === 'object') {
        message = JSON.stringify(message, null, 2);
    }
    
    // Handle boxen output
    if (message.includes('┌') && message.includes('┐')) {
        console.log(message);
        writeToLogFile(message);
        return;
    }
    
    const timestamp = new Date().toISOString();
    let levelTag = '';
    
    switch (level) {
        case LogLevel.APPLICATION: levelTag = '[APP]'; break;
        case LogLevel.VERBOSE: levelTag = '[VERB]'; break;
        case LogLevel.DEBUG: levelTag = '[DEBUG]'; break;
    }
    
    // FIXED: Changed backticks to parenthesesz
    writeToLogFile(`${timestamp} ${levelTag} ${message}`);
    
    let coloredLevelTag = levelTag;
    let coloredMessage = message;
    
    const coloredTimestamp = (chalk && chalk.dim) ? chalk.dim(timestamp) : timestamp;
    
    try {
        switch (level) {
            case LogLevel.APPLICATION: 
                coloredLevelTag = chalk.blue.bold(levelTag); 
                break;
            case LogLevel.VERBOSE: 
                coloredLevelTag = chalk.cyan(levelTag); 
                break;
            case LogLevel.DEBUG: 
                coloredLevelTag = chalk.gray(levelTag); 
                break;
        }
        
        if (message.includes('✅') || message.includes('Successfully')) {
            coloredMessage = chalk.green(message);
        } else if (message.includes('❌') || message.includes('Error') || message.includes('Failed')) {
            coloredMessage = chalk.red.bold(message);
        } else if (message.includes('⚠️') || message.includes('Warning')) {
            coloredMessage = chalk.yellow(message);
        } else if (message.includes('💎')) {
            coloredMessage = chalk.magenta.bold(message);
        }
    } catch (e) { 
        /* Proceed with uncolored logs */ 
    }
    
    // FIXED: Changed backticks to parentheses
    console.log(`${coloredTimestamp} ${coloredLevelTag} ${coloredMessage}`);
};

const setLevel = (level) => {
    if (Object.values(LogLevel).includes(level)) {
        currentLevel = level;
    }
};

module.exports = { 
    levelApplication: LogLevel.APPLICATION, 
    levelVerbose: LogLevel.VERBOSE, 
    levelDebug: LogLevel.DEBUG, 
    log, 
    setLevel 
};

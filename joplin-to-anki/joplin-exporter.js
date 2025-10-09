const cheerio = require("cheerio");
const { levelApplication, levelVerbose, levelDebug } = require("./log"); // Ensure log is imported

// AUTO-ID generation helper
const generateUniqueID = (content, title, index = 0) => {
  const crypto = require('crypto');
  const hash = crypto.createHash('md5').update(`${title}${content}${index}`).digest('hex');
  return `auto_${hash.substring(0, 12)}`;
};

// --- NEW Helper to get clean text/html content, preserving line breaks for text extraction ---
const getCleanContent = ($, element, log, fieldName = "field") => {
    if (!element || element.length === 0) {
        log(levelDebug, `No element found for ${fieldName}. Returning empty string.`);
        return '';
    }

    // Clone to avoid modifying the original element within Cheerio context
    const clonedElement = element.clone();

    // Replace <br> with a newline for better text extraction
    clonedElement.find('br').replaceWith('\n');

    // Prioritize text content, then HTML
    let content = clonedElement.text().trim();
    if (content.length === 0) {
        content = clonedElement.html() ? clonedElement.html().trim() : '';
    }

    log(levelDebug, `Cleaned content for ${fieldName}: "${content.substring(0, 100)}..." (length: ${content.length})`);
    return content;
};


// STRICT extraction - Look for .jta class elements (with auto-ID generation)
const extractQuiz = (body, title, notebook, tags, log) => {
  const $ = cheerio.load(body);
  let output = [];

  // Look for .jta class elements (with or without data-id)
  $(".jta").each((i, el) => {
    let jtaID = $(el).attr("data-id");

    // Auto-generate ID if missing
    if (!jtaID || jtaID.trim().length === 0) {
      const elementContent = $(el).text().trim();
      jtaID = generateUniqueID(elementContent, title, i);
      log(levelDebug, `Auto-generated JTA ID: ${jtaID} for element index ${i} in note ${title}`);
    }

    // Extract additional fields
    const additionalFields = extractAdditionalFieldsFromElement($, el, log);

    // Extract question and answer from within the jta element
    const questionEl = $(".question", el);
    const answerEl = $(".answer", el);

    let question = "";
    let answer = "";

    // Get question text
    if (questionEl.length > 0) {
      // Get content of .image-question specifically for text overlay
      const imageQuestionTextEl = $(".image-question", questionEl);
      if (imageQuestionTextEl.length > 0) {
        const questionText = imageQuestionTextEl.text().trim();
        question = questionText.length > 0 ? questionText : imageQuestionTextEl.html() || "";
        log(levelDebug, `Extracted image-question text: ${question.substring(0, 50)}...`);
      } else {
        // Fallback to full question content if no specific .image-question
        const questionText = questionEl.text().trim();
        question = questionText.length > 0 ? questionText : questionEl.html() || "";
        log(levelDebug, `Extracted full question text: ${question.substring(0, 50)}...`);
      }
    }

    // joplin-exporter.js
    
    // STRICT extraction - Look for .jta class elements (with auto-ID generation)
    const extractQuiz = (body, title, notebook, tags, log) => {
      const $ = cheerio.load(body);
      let output = [];
    
      // Look for .jta class elements (with or without data-id)
      $(".jta").each((i, el) => {
        let jtaID = $(el).attr("data-id");
    
        // Auto-generate ID if missing
        if (!jtaID || jtaID.trim().length === 0) {
          const elementContent = $(el).text().trim();
          jtaID = generateUniqueID(elementContent, title, i);
          log(levelDebug, `Auto-generated JTA ID: ${jtaID} for element index ${i} in note ${title}`);
        }
    
        // Extract additional fields
        const additionalFields = extractAdditionalFieldsFromElement($, el, log);
    
        // Extract question and answer from within the jta element
        const questionEl = $(".question", el);
        const answerEl = $(".answer", el);
    
        let question = "";
        let answer = "";
    
        // Get question text
        if (questionEl.length > 0) {
          // Get content of .image-question specifically for text overlay
          const imageQuestionTextEl = $(".image-question", questionEl);
          if (imageQuestionTextEl.length > 0) {
            question = imageQuestionTextEl.html() || "";
            log(levelDebug, `Extracted image-question text: ${question.substring(0, 50)}...`);
          } else {
            // Fallback to full question content
            question = questionEl.html() || "";
            log(levelDebug, `Extracted full question html: ${question.substring(0, 50)}...`);
          }
        }
        
        // --- MODIFIED & IMPROVED ANSWER EXTRACTION LOGIC (from previous step) ---
        if (answerEl.length > 0) {
          const specificAnswerEl = answerEl.find('.answer-text, .correct-answer');
          if (specificAnswerEl.length > 0) {
            answer = specificAnswerEl.html() || "";
            log(levelDebug, `Extracted answer from specific container (.answer-text/.correct-answer): ${answer.substring(0, 50)}...`);
          } else {
            const answerClone = answerEl.clone();
            answerClone.find('summary').remove();
            answerClone.find('.explanation, .correlation, .comments, .extra, .header, .footer, .sources, .origin, .insertion, .innervation, .action').remove();
            answerClone.find('img[data-jta-image-type]').remove();
            const remainingHtml = answerClone.html() ? answerClone.html().trim() : '';
            const remainingText = answerClone.text() ? answerClone.text().trim() : '';
            answer = remainingHtml.length > 0 ? remainingHtml : remainingText;
            log(levelDebug, `Extracted answer via fallback method: ${answer.substring(0, 50)}...`);
          }
        }
        
        // Detect card type before cleaning, as cleaning depends on the type
        const cardType = detectCardTypeFromContent(question, answer, additionalFields, log);
        let cleanedQuestion = question.trim();
    
        // --- NEW & ROBUST MCQ QUESTION CLEANING LOGIC ---
        if (cardType === 'mcq' && questionEl.length > 0) {
            const questionClone = questionEl.clone(); // Work on a copy
    
            // Find all text nodes directly inside the .question span, but not inside other elements
            questionClone.contents().filter(function() {
                // This regex matches lines that start with A), B), C), or D) and removes them
                const nodeValue = this.nodeValue || '';
                return this.type === 'text' && /^\s*[A-D][).]?\s*/.test(nodeValue);
            }).remove();
    
            // Also remove <br> tags that are followed by option text
            questionClone.find('br').each((idx, br_el) => {
                const nextNode = br_el.nextSibling;
                if (nextNode && nextNode.type === 'text' && /^\s*[A-D][).]?\s*/.test(nextNode.nodeValue || '')) {
                    $(br_el).remove();
                }
            });
    
            cleanedQuestion = questionClone.html().trim();
            log(levelDebug, `MCQ question cleaned: Original: "${question.substring(0, 100)}..." Cleaned: "${cleanedQuestion.substring(0, 100)}..."`);
        }
        // --- END OF NEW LOGIC ---
    
        const hasQuestionOrAnswerText = cleanedQuestion.length > 0 || (answer && answer.trim().length > 0);
        const hasImagePaths = (additionalFields.questionImagePath && additionalFields.questionImagePath.trim().length > 0) ||
                              (additionalFields.answerImagePath && additionalFields.answerImagePath.trim().length > 0);
    
        if (hasQuestionOrAnswerText || hasImagePaths) {
          output.push({
            question: cleanedQuestion,
            answer: answer ? answer.trim() : '',
            jtaID: jtaID.trim(),
            title,
            notebook,
            tags,
            type: cardType,
            source: 'jta-class',
            additionalFields
          });
    
          log(levelDebug, `Extracted JTA item:
            - Title: "${title}"
            - JTA ID: "${jtaID}"
            - Type: ${cardType}
            - Question length: ${cleanedQuestion.length}
            - Answer length: ${answer ? answer.length : 0}`);
        } else {
          log(levelDebug, `Skipping JTA element (ID: ${jtaID}) due to empty question/answer and no image paths.`);
        }
      });
    
      return output;
    };
    
    // Must have either a valid question/answer or image paths for a valid card
    const cardType = detectCardTypeFromContent(question, answer, additionalFields, log);

    const hasQuestionOrAnswerText = question.trim().length > 0 || answer.trim().length > 0;
    const hasImagePaths = (additionalFields.questionImagePath && additionalFields.questionImagePath.trim().length > 0) ||
                          (additionalFields.answerImagePath && additionalFields.answerImagePath.trim().length > 0);

    if (hasQuestionOrAnswerText || hasImagePaths) {
      // CLEAN MCQ questions - remove A) B) C) D) options from question text
      let cleanedQuestion = question.trim();
      if (cardType === 'mcq') {
        // More precise MCQ cleaning - only remove the options part after the main question
        const lines = cleanedQuestion.split(/<br\s*\/?>/gi);
        const questionLines = [];
        let foundOptions = false;

        for (const line of lines) {
          const trimmedLine = line.trim();
          // Check if this line looks like an option (A) something, B) something, etc.)
          if (/^[A-D][).]?\s/.test(trimmedLine)) {
            foundOptions = true;
            break; // Stop adding lines once we hit options
          }
          if (trimmedLine.length > 0) {
            questionLines.push(trimmedLine);
          }
        }

        if (foundOptions && questionLines.length > 0) {
          cleanedQuestion = questionLines.join('<br>').trim();
        }

        log(levelDebug, `MCQ question cleaned: Original: "${question.substring(0, 100)}..." Cleaned: "${cleanedQuestion.substring(0, 100)}..."`);
      }

      output.push({
        question: cleanedQuestion,
        answer: answer.trim(),
        jtaID: jtaID.trim(),
        title,
        notebook,
        tags,
        type: cardType,
        source: 'jta-class',
        additionalFields
      });

      // DEBUG: Log what we extracted
      log(levelDebug, `Extracted JTA item:
        - Title: "${title}"
        - JTA ID: "${jtaID}"
        - Type: ${cardType}
        - Tags: ${JSON.stringify(tags)}
        - Notebook: ${JSON.stringify(notebook)}
        - Question length: ${cleanedQuestion.length}
        - Answer length: ${answer.length}
        - Header: "${additionalFields.header.substring(0, 50)}..."
        - Footer: "${additionalFields.footer.substring(0, 50)}..."
        - Sources: "${additionalFields.sources.substring(0, 50)}..."`); // Added substring for brevity
    } else {
      log(levelDebug, `Skipping JTA element (ID: ${jtaID}) due to empty question/answer and no image paths.`);
    }
  });

  return output;
};

// Extract additional fields from within the JTA element
const extractAdditionalFieldsFromElement = ($, jtaElement, log) => {
  const fields = {
    explanation: '',
    clinicalCorrelation: '',
    extra: '',
    header: '',
    footer: '',
    sources: '',
    comments: '',
    origin: '',
    insertion: '',
    innervation: '',
    action: '',
    // MCQ fields
    optionA: '',
    optionB: '',
    optionC: '',
    optionD: '',
    correctAnswer: '',
    // Image fields
    questionImagePath: '',
    answerImagePath: ''
  };

  // --- REVISED: Use getCleanContent for these top-level fields ---
  // Extract Header - looking directly within .jta
  console.log(`DEBUG: Attempting to extract Header from ${$(jtaElement).html().substring(0,200)}...`);
  const headerEl = $('.header', jtaElement);
  fields.header = getCleanContent($, headerEl, log, "Header");
  console.log(`DEBUG: Extracted Header field: "${fields.header.substring(0, 50)}..."`);

  // Extract Footer - looking directly within .jta (or its descendants)
  console.log(`DEBUG: Attempting to extract Footer from ${$(jtaElement).html().substring(0,200)}...`);
  const footerEl = $('.footer', jtaElement);
  fields.footer = getCleanContent($, footerEl, log, "Footer");
  console.log(`DEBUG: Extracted Footer field: "${fields.footer.substring(0, 50)}..."`);

  // Extract Sources - looking directly within .jta (or its descendants)
  console.log(`DEBUG: Attempting to extract Sources from ${$(jtaElement).html().substring(0,200)}...`);
  const sourcesEl = $('.sources', jtaElement);
  fields.sources = getCleanContent($, sourcesEl, log, "Sources");
  console.log(`DEBUG: Extracted Sources field: "${fields.sources.substring(0, 50)}..."`);

  // Extract Origin - anatomy field
  console.log(`DEBUG: Attempting to extract Origin from ${$(jtaElement).html().substring(0,200)}...`);
  const originEl = $('.origin', jtaElement);
  fields.origin = getCleanContent($, originEl, log, "Origin");
  console.log(`DEBUG: Extracted Origin field: "${fields.origin.substring(0, 50)}..."`);
  
  // Extract Insertion - anatomy field
  console.log(`DEBUG: Attempting to extract Insertion from ${$(jtaElement).html().substring(0,200)}...`);
  const insertionEl = $('.insertion', jtaElement);
  fields.insertion = getCleanContent($, insertionEl, log, "Insertion");
  console.log(`DEBUG: Extracted Insertion field: "${fields.insertion.substring(0, 50)}..."`);

  // Extract Innervation - anatomy field
  console.log(`DEBUG: Attempting to extract Innervation from ${$(jtaElement).html().substring(0,200)}...`);
  const innervationEl = $('.innervation', jtaElement);
  fields.innervation = getCleanContent($, innervationEl, log, "Innervation");
  console.log(`DEBUG: Extracted Innervation field: "${fields.innervation.substring(0, 50)}..."`);
  
  // Extract Action - anatomy field
  console.log(`DEBUG: Attempting to extract Action from ${$(jtaElement).html().substring(0,200)}...`);
  const actionEl = $('.action', jtaElement);
  fields.action = getCleanContent($, actionEl, log, "Action");
  console.log(`DEBUG: Extracted Action field: "${fields.action.substring(0, 50)}..."`);
  // --- END REVISED ---

  // Look for explanation within the element
  const explanationEl = $('.explanation', jtaElement);
  if (explanationEl.length > 0) {
    fields.explanation = explanationEl.text().replace(/^(Explanation|💡)[:.]?\s*/i, '').trim();
    log(levelDebug, `Extracted Explanation: "${fields.explanation.substring(0, 50)}..."`);
  }

  // Look for clinical correlation
  const correlationEl = $('.correlation', jtaElement);
  if (correlationEl.length > 0) {
    fields.clinicalCorrelation = correlationEl.text().replace(/^(Clinical Correlation|🔗)[:.]?\s*/i, '').trim();
    log(levelDebug, `Extracted Clinical Correlation: "${fields.clinicalCorrelation.substring(0, 50)}..."`);
  }

  // Look for extra information
  const extraEl = $('.extra', jtaElement);
  if (extraEl.length > 0) {
    fields.extra = extraEl.text().replace(/^(Extra|Additional|📚)[:.]?\s*/i, '').trim();
    log(levelDebug, `Extracted Extra: "${fields.extra.substring(0, 50)}..."`);
  }

  // Look for comments (specifically for image occlusion)
  const commentsEl = $('.comments', jtaElement);
  if (commentsEl.length > 0) {
    fields.comments = commentsEl.html() || commentsEl.text() || "";
    log(levelDebug, `Extracted Comments: "${fields.comments.substring(0, 50)}..."`);
  }

  // Look for correct answer
  const correctEl = $('.correct-answer, .correct', jtaElement);
  if (correctEl.length > 0) {
    fields.correctAnswer = correctEl.text().replace(/^(Answer|Correct)[:.]?\s*/i, '').trim();
    log(levelDebug, `Extracted Correct Answer: "${fields.correctAnswer}"`);
  }

  // --- Image field extraction ---
  // Look for image elements with data-jta-image-type attributes
  const questionImgEl = $('img[data-jta-image-type="question"]', jtaElement);
  if (questionImgEl.length > 0) {
    fields.questionImagePath = questionImgEl.attr('src') || '';
    // Use the alt text from the question image as the primary AltText
    fields.altText = questionImgEl.attr('alt') || '';
    log(levelDebug, `Found question image: ${fields.questionImagePath}`);
  }

  const answerImgEl = $('img[data-jta-image-type="answer"]', jtaElement);
  if (answerImgEl.length > 0) {
    fields.answerImagePath = answerImgEl.attr('src') || '';
    log(levelDebug, `Found answer image: ${fields.answerImagePath}`);
  }
  // --- END Image field extraction ---

  // ENHANCED: Extract MCQ options from question text if not found in separate elements
  const questionTextEl = $('.image-question', jtaElement); // Prioritize text from .image-question if present
  let questionTextContent = questionTextEl.length > 0 ? questionTextEl.text() : $('.question', jtaElement).text();

  if (questionTextContent.length > 0) {
    // Parse MCQ options from text format: A) option, B) option, etc.
    const optionPatterns = [
      /A[).]?\s*([^\n\r]+?)(?=\s*<br[^>]*>|\s*B[).]|$)/i,
      /B[).]?\s*([^\n\r]+?)(?=\s*<br[^>]*>|\s*C[).]|$)/i,
      /C[).]?\s*([^\n\r]+?)(?=\s*<br[^>]*>|\s*D[).]|$)/i,
      /D[).]?\s*([^\n\r]+?)(?=\s*<br[^>]*>|\s*$)/i
    ];

    const optionMatches = optionPatterns.map(pattern => {
      const match = questionTextContent.match(pattern);
      return match ? match[1].trim() : '';
    });

    // Only use extracted options if we found at least 2 and explicit option fields are not already set
    if (optionMatches.filter(Boolean).length >= 2) {
      if (!fields.optionA) fields.optionA = optionMatches[0] || '';
      if (!fields.optionB) fields.optionB = optionMatches[1] || '';
      if (!fields.optionC) fields.optionC = optionMatches[2] || '';
      if (!fields.optionD) fields.optionD = optionMatches[3] || '';
      log(levelDebug, `Extracted MCQ options from question text: A:"${fields.optionA}", B:"${fields.optionB}"...`);
    }
  }

  // Look for explicit option elements (fallback or override)
  const optionAEl = $('.option-a, .optionA', jtaElement);
  if (optionAEl.length > 0) {
    fields.optionA = optionAEl.text().replace(/^A[).]?\s*/i, '').trim();
    log(levelDebug, `Explicit Option A: "${fields.optionA}"`);
  }

  const optionBEl = $('.option-b, .optionB', jtaElement);
  if (optionBEl.length > 0) {
    fields.optionB = optionBEl.text().replace(/^B[).]?\s*/i, '').trim();
    log(levelDebug, `Explicit Option B: "${fields.optionB}"`);
  }

  const optionCEl = $('.option-c, .optionC', jtaElement);
  if (optionCEl.length > 0) {
    fields.optionC = optionCEl.text().replace(/^C[).]?\s*/i, '').trim();
    log(levelDebug, `Explicit Option C: "${fields.optionC}"`);
  }

  const optionDEl = $('.option-d, .optionD', jtaElement);
  if (optionDEl.length > 0) {
    fields.optionD = optionDEl.text().replace(/^D[).]?\s*/i, '').trim();
    log(levelDebug, `Explicit Option D: "${fields.optionD}"`);
  }

  return fields;
};

// Detect card type from content within JTA element
const detectCardTypeFromContent = (question, answer, additionalFields = {}, log) => {
  log(levelDebug, `Card Type Detection:
    - Question: "${question ? question.substring(0, 100) : 'EMPTY'}..."
    - Answer: "${answer ? answer.substring(0, 100) : 'EMPTY'}..."
    - Additional fields: ${JSON.stringify({
      explanation: additionalFields.explanation ? 'present' : 'empty',
      clinicalCorrelation: additionalFields.clinicalCorrelation ? 'present' : 'empty',
      extra: additionalFields.extra ? 'present' : 'empty',
      comments: additionalFields.comments ? 'present' : 'empty',
      optionA: additionalFields.optionA || 'empty',
      optionB: additionalFields.optionB || 'empty',
      optionC: additionalFields.optionC || 'empty',
      optionD: additionalFields.optionD || 'empty',
      correctAnswer: additionalFields.correctAnswer ? 'present' : 'empty',
      questionImagePath: additionalFields.questionImagePath || 'empty',
      answerImagePath: additionalFields.answerImagePath || 'empty',
      altText: additionalFields.altText || 'empty',
      header: additionalFields.header ? 'present' : 'empty',
      footer: additionalFields.footer ? 'present' : 'empty',
      sources: additionalFields.sources ? 'present' : 'empty'
    }, null, 2)}`);

  // Check for cloze deletions {{c1::text}}
  const clozePattern = /\{\{c\d+::[^}]+\}\}/g;
  const questionCloze = clozePattern.test(question || "");
  const answerCloze = clozePattern.test(answer || "");

  if (questionCloze || answerCloze) {
    log(levelDebug, `Detected CLOZE card (question: ${questionCloze}, answer: ${answerCloze})`);
    return "cloze";
  }

  // --- Image card detection ---
  const hasQuestionImagePath = additionalFields.questionImagePath && additionalFields.questionImagePath.trim();
  const hasAnswerImagePath = additionalFields.answerImagePath && additionalFields.answerImagePath.trim();

  // Also check if img tags are directly within the question/answer body (less preferred, but robust)
  const hasImageInQuestionBody = question && /<img[^>]+src/i.test(question);
  const hasImageInAnswerBody = answer && /<img[^>]+src/i.test(answer);

  if (hasQuestionImagePath || hasAnswerImagePath || hasImageInQuestionBody || hasImageInAnswerBody) {
    log(levelDebug, `Detected IMAGE OCCLUSION card (questionImagePath: ${hasQuestionImagePath}, answerImagePath: ${hasAnswerImagePath}, inQuestionBody: ${hasImageInQuestionBody}, inAnswerBody: ${hasImageInAnswerBody})`);
    return "imageOcclusion";
  }
  // --- END Image card detection ---

  // Check for MCQ options
  const mcqFields = [
    additionalFields.optionA,
    additionalFields.optionB,
    additionalFields.optionC,
    additionalFields.optionD
  ];
  const hasMCQOptions = mcqFields.some(opt => opt && opt.trim());
  const hasCorrectAnswer = additionalFields.correctAnswer && additionalFields.correctAnswer.trim();

  if (hasMCQOptions || hasCorrectAnswer) {
    log(levelDebug, `Detected MCQ card (optionA: "${additionalFields.optionA}", optionB: "${additionalFields.optionB}", optionC: "${additionalFields.optionC}", optionD: "${additionalFields.optionD}", correctAnswer: "${additionalFields.correctAnswer}")`);
    return "mcq";
  }

  // Default to basic
  log(levelDebug, `Detected BASIC card (default fallback)`);
  return "basic";
};

const escapeRegExp = (string) => {
  const reRegExpChar = /[\\^$.*+?()[\]{}|]/g;
  return string.replace(reRegExpChar, "\\$&");
};

const addResources = (jtaItems, resources, log) => {
  const preppedResources = resources.map((resource) => {
    const fileName = `${resource.id}.${resource.file_extension}`;
    log(levelDebug, `Prepping resource: ${fileName} for ID: ${resource.id}`);
    return {
      fileName,
      expectedLinkRgx: new RegExp(
        escapeRegExp(`![${resource.title}](:\/${resource.id})`),
        "g"
      ),
      replacementLink: `![${resource.title}](${fileName})`,
      id: resource.id,
    };
  });

  jtaItems.forEach((item) => {
    preppedResources.forEach((resource) => {
      let hasResource = false;

      // Check and replace in answer
      if (item.answer && resource.expectedLinkRgx.test(item.answer)) {
        item.answer = item.answer.replace(
          resource.expectedLinkRgx,
          resource.replacementLink
        );
        hasResource = true;
        log(levelDebug, `Replaced resource link in answer for JTA ID: ${item.jtaID}`);
      }

      // Check and replace in question
      if (item.question && resource.expectedLinkRgx.test(item.question)) {
        item.question = item.question.replace(
          resource.expectedLinkRgx,
          resource.replacementLink
        );
        hasResource = true;
        log(levelDebug, `Replaced resource link in question for JTA ID: ${item.jtaID}`);
      }

      // --- NEW: Check and replace in questionImagePath and answerImagePath ---
      if (item.additionalFields) {
        if (item.additionalFields.questionImagePath && item.additionalFields.questionImagePath.includes(`:/${resource.id}`)) {
          item.additionalFields.questionImagePath = resource.fileName;
          hasResource = true;
          log(levelDebug, `Replaced resource in questionImagePath for JTA ID: ${item.jtaID}`);
        }
        if (item.additionalFields.answerImagePath && item.additionalFields.answerImagePath.includes(`:/${resource.id}`)) {
          item.additionalFields.answerImagePath = resource.fileName;
          hasResource = true;
          log(levelDebug, `Replaced resource in answerImagePath for JTA ID: ${item.jtaID}`);
        }
      }
      // --- END NEW ---

      // Add to resources array if found
      if (hasResource) {
        if (!item.resources) {
          item.resources = [];
        }
        item.resources.push({
          id: resource.id,
          fileName: resource.fileName
        });
        log(levelDebug, `Associated resource ${resource.fileName} with JTA ID: ${item.jtaID}`);
      }
    });
  });

  return jtaItems;
};

const typeItem = "item";
const typeResource = "resource";
const typeError = "error";

async function* exporter(client, datetime, log) { // 'log' is passed here
  const date = new Date(datetime);

  try {
    // Get all folders first for hierarchy mapping
    log(levelVerbose, "Fetching folder hierarchy...");
    const folders = await client.getAllFolders();

    // Get all notes
    log(levelVerbose, "Fetching notes...");
    const notes = await client.getAllNotes(
      "id,updated_time,title,parent_id",
      date
    );

    log(levelApplication, `Found ${notes.length} notes updated since ${date.toISOString()}`);

    for (const note of notes) {
      try {
        // Skip if note is too old
        const noteDate = new Date(note.updated_time);
        if (noteDate.getTime() < date.getTime()) {
          log(levelDebug, `Skipping note ${note.title} (${note.id}): Updated before sync start time.`);
          continue;
        }

        log(levelDebug, `Processing note: ${note.title} (${note.id})`);

        // Get detailed note information
        const noteDetails = await client.getNoteDetails(note.id);

        if (!noteDetails || !noteDetails.note) {
          log(levelVerbose, `Skipping note ${note.title}: No content found`);
          continue;
        }

        const { note: fullNote, notebook, tags, resources } = noteDetails;

        // STRICT: Only extract from .jta elements
        const jtaItems = extractQuiz(
          fullNote.body,
          fullNote.title,
          notebook,
          tags,
          log
        );

        if (jtaItems.length === 0) {
          log(levelDebug, `No .jta elements found in note: ${fullNote.title}`);
          continue;
        }

        log(levelVerbose, `Found ${jtaItems.length} JTA items in note: ${fullNote.title}`);

        // Add resource details to items
        const jtaItemsWithResourceDetails = addResources(jtaItems, resources, log);

        // Yield each item
        for (const item of jtaItemsWithResourceDetails) {
          // Add folder hierarchy to item for deck determination
          item.folders = folders;

          yield {
            type: typeItem,
            data: item,
          };

          // Yield resources if any
          if (item.resources && item.resources.length > 0) {
            for (const resource of item.resources) {
              try {
                log(levelDebug, `Fetching resource: ${resource.fileName}`);

                const file = await client.request(
                  client.urlGen("resources", resource.id, "file"),
                  "GET",
                  undefined,
                  undefined,
                  false,
                  "binary"
                );

                yield {
                  type: typeResource,
                  data: {
                    fileName: resource.fileName,
                    data: file,
                  },
                };
              } catch (resourceError) {
                log(levelApplication, `Failed to fetch resource ${resource.fileName}: ${resourceError.message}`);

                yield {
                  type: typeError,
                  data: `Resource fetch error: ${resourceError.message}`,
                };
              }
            }
          }
        }
      } catch (noteError) {
        log(levelApplication, `Error processing note ${note.title} (${note.id}): ${noteError.message}`);

        yield {
          type: typeError,
          data: `Note processing error for ${note.title}: ${noteError.message}`,
        };
      }
    }
  } catch (error) {
    log(levelApplication, `Exporter error: ${error.message}`);

    yield {
      type: typeError,
      data: `Exporter initialization error: ${error.message}`,
    };
  }
}

module.exports = {
  exporter,
  typeItem,
  typeResource,
  typeError,
  extractQuiz,
  detectCardTypeFromContent,
  extractAdditionalFieldsFromElement,
};

// joplin-exporter.js (FINAL CORRECTED VERSION)

const cheerio = require("cheerio");
const { levelApplication, levelVerbose, levelDebug } = require("./log");

const generateUniqueID = (content, title, index = 0) => {
  const crypto = require('crypto');
  const hash = crypto.createHash('md5').update(`${title}${content}${index}`).digest('hex');
  return `auto_${hash.substring(0, 12)}`;
};

const getCleanContent = ($, element, log, fieldName = "field") => {
    if (!element || element.length === 0) {
        log(levelDebug, `No element found for ${fieldName}. Returning empty string.`);
        return '';
    }
    const clonedElement = element.clone();
    clonedElement.find('br').replaceWith('\n');
    let content = clonedElement.text().trim();
    if (content.length === 0) {
        content = clonedElement.html() ? clonedElement.html().trim() : '';
    }
    log(levelDebug, `Cleaned content for ${fieldName}: "${content.substring(0, 100)}..."`);
    return content;
};

const extractQuiz = (body, title, notebook, tags, log) => {
  const $ = cheerio.load(body);
  let output = [];

  $(".jta").each((i, el) => {
    let jtaID = $(el).attr("data-id");
    if (!jtaID || jtaID.trim().length === 0) {
      const elementContent = $(el).text().trim();
      jtaID = generateUniqueID(elementContent, title, i);
      log(levelDebug, `Auto-generated JTA ID: ${jtaID} for element index ${i}`);
    }

    const additionalFields = extractAdditionalFieldsFromElement($, el, log);
    const questionEl = $(".question", el);
    const answerEl = $(".answer", el);
    let question = "";
    let answer = "";

    if (questionEl.length > 0) {
      const imageQuestionTextEl = $(".image-question", questionEl);
      if (imageQuestionTextEl.length > 0) {
        question = imageQuestionTextEl.html() || "";
      } else {
        question = questionEl.html() || "";
      }
    }

    if (answerEl.length > 0) {
      const specificAnswerEl = answerEl.find('.answer-text, .correct-answer');
      if (specificAnswerEl.length > 0) {
        answer = specificAnswerEl.html() || "";
      } else {
        const answerClone = answerEl.clone();
        answerClone.find('summary').remove();
        answerClone.find('.explanation, .correlation, .comments, .extra, .header, .footer, .sources, .origin, .insertion, .innervation, .action').remove();
        answerClone.find('img[data-jta-image-type]').remove();
        const remainingHtml = answerClone.html() ? answerClone.html().trim() : '';
        const remainingText = answerClone.text() ? answerClone.text().trim() : '';
        answer = remainingHtml.length > 0 ? remainingHtml : remainingText;
      }
    }

    const cardType = detectCardTypeFromContent(question, answer, additionalFields, log);
    let cleanedQuestion = question.trim();

    if (cardType === 'mcq' && questionEl.length > 0) {
        const questionClone = questionEl.clone();
        questionClone.contents().filter(function() {
            const nodeValue = this.nodeValue || '';
            return this.type === 'text' && /^\s*[A-D][).]?\s*/.test(nodeValue);
        }).remove();
        questionClone.find('br').each((idx, br_el) => {
            const nextNode = br_el.nextSibling;
            if (nextNode && nextNode.type === 'text' && /^\s*[A-D][).]?\s*/.test(nextNode.nodeValue || '')) {
                $(br_el).remove();
            }
        });
        cleanedQuestion = questionClone.html().trim();
        log(levelDebug, `MCQ question cleaned successfully.`);
    }

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
    } else {
      log(levelDebug, `Skipping JTA element (ID: ${jtaID}) due to empty content.`);
    }
  });
  return output;
};

const extractAdditionalFieldsFromElement = ($, jtaElement, log) => {
  const fields = {
    explanation: '', clinicalCorrelation: '', extra: '', header: '', footer: '', sources: '',
    comments: '', origin: '', insertion: '', innervation: '', action: '',
    optionA: '', optionB: '', optionC: '', optionD: '', correctAnswer: '',
    questionImagePath: '', answerImagePath: '', altText: ''
  };

  fields.header = getCleanContent($, $('.header', jtaElement), log, "Header");
  fields.footer = getCleanContent($, $('.footer', jtaElement), log, "Footer");
  fields.sources = getCleanContent($, $('.sources', jtaElement), log, "Sources");
  fields.origin = getCleanContent($, $('.origin', jtaElement), log, "Origin");
  fields.insertion = getCleanContent($, $('.insertion', jtaElement), log, "Insertion");
  fields.innervation = getCleanContent($, $('.innervation', jtaElement), log, "Innervation");
  fields.action = getCleanContent($, $('.action', jtaElement), log, "Action");

  const explanationEl = $('.explanation', jtaElement);
  if (explanationEl.length > 0) fields.explanation = explanationEl.html().trim();
  
  const correlationEl = $('.correlation', jtaElement);
  if (correlationEl.length > 0) fields.clinicalCorrelation = correlationEl.html().trim();
  
  const extraEl = $('.extra', jtaElement);
  if (extraEl.length > 0) fields.extra = extraEl.html().trim();
  
  const commentsEl = $('.comments', jtaElement);
  if (commentsEl.length > 0) fields.comments = commentsEl.html().trim();
  
  const correctEl = $('.correct-answer, .correct', jtaElement);
  if (correctEl.length > 0) fields.correctAnswer = correctEl.text().replace(/^(Answer|Correct)[:.]?\s*/i, '').trim();

  const questionImgEl = $('img[data-jta-image-type="question"]', jtaElement);
  if (questionImgEl.length > 0) {
    fields.questionImagePath = questionImgEl.attr('src') || '';
    fields.altText = questionImgEl.attr('alt') || '';
  }
  const answerImgEl = $('img[data-jta-image-type="answer"]', jtaElement);
  if (answerImgEl.length > 0) fields.answerImagePath = answerImgEl.attr('src') || '';

  // --- START OF CHANGE 1: Corrected MCQ Option Extraction ---
  const questionTextContent = ($('.question', jtaElement).text() || "");
  if (questionTextContent.length > 0) {
    // This regex is now more precise to avoid grabbing parts of the main question
    const optionPatterns = [
        /(?:A\)|A\.)\s*([\s\S]*?)(?=\s*(?:B\)|B\.|$))/i,
        /(?:B\)|B\.)\s*([\s\S]*?)(?=\s*(?:C\)|C\.|$))/i,
        /(?:C\)|C\.)\s*([\s\S]*?)(?=\s*(?:D\)|D\.|$))/i,
        /(?:D\)|D\.)\s*([\s\S]*?)(?=\s*$)/i
    ];
    
    const optionMatches = optionPatterns.map(pattern => {
      const match = questionTextContent.match(pattern);
      return match ? match[1].trim() : '';
    });

    if (optionMatches.filter(Boolean).length >= 2) {
      if (!fields.optionA) fields.optionA = optionMatches[0] || '';
      if (!fields.optionB) fields.optionB = optionMatches[1] || '';
      if (!fields.optionC) fields.optionC = optionMatches[2] || '';
      if (!fields.optionD) fields.optionD = optionMatches[3] || '';
    }
  }
  // --- END OF CHANGE 1 ---

  return fields;
};

const detectCardTypeFromContent = (question, answer, additionalFields = {}, log) => {
  if (/\{\{c\d+::[^}]+\}\}/g.test(question || "")) return "cloze";
  
  if ((additionalFields.questionImagePath||'').trim() || (additionalFields.answerImagePath||'').trim() || /<img[^>]+src/i.test(question||'') || /<img[^>]+src/i.test(answer||'')) return "imageOcclusion";
  
  // --- START OF CHANGE 2: Corrected Card Type Detection ---
  // A card is only an MCQ if it has a correct answer AND at least two options.
  const hasCorrectAnswer = (additionalFields.correctAnswer || '').trim().length > 0;
  const options = [additionalFields.optionA, additionalFields.optionB, additionalFields.optionC, additionalFields.optionD];
  const hasMinOptions = options.filter(opt => (opt || '').trim().length > 0).length >= 2;

  if (hasCorrectAnswer && hasMinOptions) {
    return "mcq";
  }
  // --- END OF CHANGE 2 ---

  return "basic";
};

const addResources = (jtaItems, resources, log) => {
  jtaItems.forEach(item => {
    (resources || []).forEach(resource => {
      const fileName = `${resource.id}.${resource.file_extension}`;
      const resourceLink = `:/${resource.id}`;
      let hasResource = false;
      if (item.answer && item.answer.includes(resourceLink)) {
        item.answer = item.answer.replace(new RegExp(resourceLink, 'g'), fileName);
        hasResource = true;
      }
      if (item.question && item.question.includes(resourceLink)) {
        item.question = item.question.replace(new RegExp(resourceLink, 'g'), fileName);
        hasResource = true;
      }
      if (item.additionalFields.questionImagePath && item.additionalFields.questionImagePath.includes(resourceLink)) {
        item.additionalFields.questionImagePath = fileName;
        hasResource = true;
      }
      if (item.additionalFields.answerImagePath && item.additionalFields.answerImagePath.includes(resourceLink)) {
        item.additionalFields.answerImagePath = fileName;
        hasResource = true;
      }
      if (hasResource) {
        if (!item.resources) item.resources = [];
        item.resources.push({ id: resource.id, fileName });
      }
    });
  });
  return jtaItems;
};

async function* exporter(client, datetime, log) {
  const date = new Date(datetime);
  try {
    const folders = await client.getAllFolders();
    const notes = await client.getAllNotes("id,updated_time,title,parent_id", date);
    log(levelApplication, `Found ${notes.length} notes updated since ${date.toISOString()}`);

    for (const note of notes) {
      if (new Date(note.updated_time).getTime() < date.getTime()) continue;
      try {
        const noteDetails = await client.getNoteDetails(note.id);
        if (!noteDetails || !noteDetails.note) continue;

        const { note: fullNote, notebook, tags, resources } = noteDetails;
        const jtaItems = extractQuiz(fullNote.body, fullNote.title, notebook, tags, log);
        if (jtaItems.length === 0) continue;

        const itemsWithResources = addResources(jtaItems, resources, log);
        for (const item of itemsWithResources) {
          item.folders = folders;
          yield { type: "item", data: item };

          if (item.resources) {
            for (const resource of item.resources) {
              try {
                const file = await client.request(client.urlGen("resources", resource.id, "file"), "GET", undefined, undefined, false, "binary");
                yield { type: "resource", data: { fileName: resource.fileName, data: file } };
              } catch (resError) {
                yield { type: "error", data: `Resource fetch error: ${resError.message}` };
              }
            }
          }
        }
      } catch (noteError) {
        yield { type: "error", data: `Note processing error for ${note.title}: ${noteError.message}` };
      }
    }
  } catch (error) {
    yield { type: "error", data: `Exporter init error: ${error.message}` };
  }
}

module.exports = {
  exporter,
  typeItem: "item",
  typeResource: "resource",
  typeError: "error",
};

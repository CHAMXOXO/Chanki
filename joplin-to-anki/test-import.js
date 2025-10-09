const AnkiClient = require("./anki-client");

async function runTest(dryRun = true) {
  const client = new AnkiClient();

  console.log("=== Health Check ===");
  const health = await client.healthCheck();
  console.log(health);

  // Example deck path simulation
  const baseDeck = "Joplin Sync Test";

  // --- Sample Notes ---
  const notes = [
    {
      modelType: "basic",
      fields: {
        Question: "What is the powerhouse of the cell?",
        Answer: "Mitochondria",
        Explanation: "It generates ATP through oxidative phosphorylation.",
        "Clinical Correlation": "Mitochondrial diseases affect energy metabolism.",
        "Joplin to Anki ID": "test-basic-001"
      },
      tags: ["biology::cell"]
    },
    {
      modelType: "cloze",
      fields: {
        Text: "The capital of France is {{c1::Paris}}.",
        Extra: "Known as the city of lights.",
        Explanation: "Paris is the capital city of France.",
        "Clinical Correlation": "N/A",
        "Joplin to Anki ID": "test-cloze-001"
      },
      tags: ["geography"]
    },
    {
      modelType: "mcq",
      fields: {
        Question: "Which vitamin is fat soluble?",
        OptionA: "Vitamin C",
        OptionB: "Vitamin B12",
        OptionC: "Vitamin A",
        OptionD: "Vitamin B6",
        CorrectAnswer: "Vitamin A",
        Explanation: "Vitamins A, D, E, K are fat soluble.",
        "Clinical Correlation": "Vitamin A deficiency leads to night blindness.",
        "Joplin to Anki ID": "test-mcq-001"
      },
      tags: ["nutrition"]
    },
    {
      modelType: "imageOcclusion",
      fields: {
        ImagePath: "path/to/fake_image.png",
        AltText: "Human skull diagram",
        Question: "Identify the highlighted structure.",
        Answer: "Foramen magnum",
        Correlation: "Clinical relevance in neurosurgery.",
        "Joplin to Anki ID": "test-imgocc-001"
      },
      tags: ["anatomy::skull"]
    }
  ];

  for (let note of notes) {
    const modelType = note.modelType;
    const model = client.createModel ? modelType : "basic"; // fallback
    const deckName = `${baseDeck}::${modelType}`;

    const notePayload = {
      deckName,
      modelName: `Joplin to Anki ${modelType.charAt(0).toUpperCase() + modelType.slice(1)} Enhanced`,
      fields: note.fields,
      tags: note.tags
    };

    if (dryRun) {
      console.log(`Would add note to deck [${deckName}] with model [${notePayload.modelName}]`);
      console.log(notePayload.fields);
    } else {
      try {
        const result = await client.addNote({ note: notePayload });
        console.log(`Added note, result: ${result}`);
      } catch (err) {
        console.error(`Error adding note: ${err.message}`);
      }
    }
  }
}

runTest(false) // <-- change to false to really push to Anki
  .then(() => console.log("=== Test completed ==="))
  .catch(err => console.error(err));

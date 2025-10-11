// Existing helper functions...

const resolveDeckPath = (tags, notebook, childNotebook) => {
    // Priority 1: Check for deck and subdeck tags
    const deckTag = tags.find(tag => tag.startsWith('deck::'));
    const subdeckTag = tags.find(tag => tag.startsWith('subdeck::'));
    
    if (deckTag) {
        const mainDeck = deckTag.replace('deck::', '').trim();
        const subDeck = subdeckTag ? subdeckTag.replace('subdeck::', '').trim() : null;
        return subDeck ? `${mainDeck}::${subDeck}` : mainDeck;
    }
    
    // Priority 2: Use notebook structure
    if (notebook) {
        return childNotebook ? `${notebook}::${childNotebook}` : notebook;
    }
    
    // Priority 3: Fallback to default
    return 'Default';
};

// Modify the extractQuiz function to accept childNotebook and use deckPath
function extractQuiz(quizData, tags, notebook, childNotebook) {
    const deckPath = resolveDeckPath(tags, notebook, childNotebook);
    // Existing logic to extract quiz...
}

// Update the exporter function to handle notebook hierarchy
function exporter(data) {
    // Existing logic...
    const childNotebook = getChildNotebook(data); // Example function to get child notebook
    extractQuiz(quizData, tags, notebook, childNotebook);
    // Existing logic...
}
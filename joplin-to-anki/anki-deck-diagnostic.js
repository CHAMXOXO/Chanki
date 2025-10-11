// anki-deck-diagnostic.js
// Run this script to diagnose where your cards are actually going

const axios = require('axios');

const ankiRequest = async (action, params = {}) => {
  try {
    const response = await axios.post('http://127.0.0.1:8765', {
      action,
      version: 6,
      params
    });
    
    if (response.data.error) {
      throw new Error(response.data.error);
    }
    
    return response.data.result;
  } catch (error) {
    console.error(`Error with action "${action}":`, error.message);
    return null;
  }
};

const diagnose = async () => {
  console.log('🔍 Starting Anki Deck Diagnostic\n');
  
  // 1. Check AnkiConnect is running
  console.log('1. Checking AnkiConnect...');
  const version = await ankiRequest('version');
  if (version) {
    console.log(`   ✅ AnkiConnect version: ${version}\n`);
  } else {
    console.log('   ❌ Cannot connect to AnkiConnect\n');
    return;
  }
  
  // 2. List all decks
  console.log('2. Listing all available decks:');
  const deckNames = await ankiRequest('deckNames');
  if (deckNames) {
    deckNames.forEach(deck => console.log(`   - ${deck}`));
    console.log('');
  }
  
  // 3. Search for your JTA notes
  console.log('3. Searching for Joplin to Anki notes...');
  const jtaNotes = await ankiRequest('findNotes', { query: '"Joplin to Anki ID:*"' });
  console.log(`   Found ${jtaNotes ? jtaNotes.length : 0} notes with JTA ID\n`);
  
  // 4. Get details of recent JTA notes
  if (jtaNotes && jtaNotes.length > 0) {
    console.log('4. Analyzing note locations (showing last 10 notes):');
    const recentNotes = jtaNotes.slice(-10);
    const notesInfo = await ankiRequest('notesInfo', { notes: recentNotes });
    
    if (notesInfo) {
      const deckCounts = {};
      notesInfo.forEach(note => {
        const deckName = note.cards && note.cards.length > 0 ? 
          note.cards[0].deckName : 'Unknown';
        deckCounts[deckName] = (deckCounts[deckName] || 0) + 1;
        
        const jtaID = note.fields['Joplin to Anki ID']?.value || 'No ID';
        console.log(`   Note ID ${note.noteId}: "${jtaID.substring(0, 20)}..." → Deck: "${deckName}"`);
      });
      
      console.log('\n5. Deck distribution:');
      Object.entries(deckCounts).forEach(([deck, count]) => {
        console.log(`   ${deck}: ${count} note(s)`);
      });
    }
  } else {
    console.log('4. No JTA notes found to analyze\n');
  }
  
  // 6. Check if "anki" deck exists
  console.log('\n6. Checking for "anki" deck specifically:');
  if (deckNames && deckNames.includes('anki')) {
    console.log('   ✅ Deck "anki" exists');
    
    // Count cards in the anki deck
    const cardsInAnki = await ankiRequest('findCards', { query: 'deck:anki' });
    console.log(`   Cards in "anki" deck: ${cardsInAnki ? cardsInAnki.length : 0}`);
    
    // Check for JTA cards specifically in anki deck
    const jtaInAnki = await ankiRequest('findNotes', { query: 'deck:anki "Joplin to Anki ID:*"' });
    console.log(`   JTA cards in "anki" deck: ${jtaInAnki ? jtaInAnki.length : 0}`);
  } else {
    console.log('   ❌ Deck "anki" does not exist');
    console.log('   💡 Try creating it manually in Anki first');
  }
  
  console.log('\n✨ Diagnostic complete!\n');
};

diagnose().catch(console.error);

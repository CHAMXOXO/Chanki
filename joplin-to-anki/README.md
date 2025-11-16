# Chanki - Advanced Joplin ↔ Anki Sync

**Intelligent bidirectional synchronization between Joplin notes and Anki flashcards**

![Version](https://img.shields.io/badge/version-2.0.2-blue)
![License](https://img.shields.io/badge/license-MIT%20%2B%20Proprietary-green)

---

## 🎯 Overview

Chanki provides powerful synchronization between Joplin and Anki with intelligent conflict resolution, state tracking, and premium organizational features designed specifically for medical students and lifelong learners.

### What Makes Chanki Different?

This project began as inspiration of [joplin-to-anki](https://github.com/BartBucknill/joplin-to-anki) by Bart (MIT License), which provided basic one-way sync functionality. Chanki represents a **complete architectural redesign** with:

- ✨ **Bidirectional sync** - Changes AND ✨Creation✨, flow both ways
- 🧠 **Intelligent conflict resolution** - Anki-win policy with content hashing
- 📊 **State-based tracking** - Knows what changed and why
- 🎨 **Advanced media handling** - Automatic image conversion
- 💎 **Premium deck organization** - Notebook Hierarchy and tag-based assignment
- 🔄 **Smart restamping** - Recovers orphaned blocks
- 🛡️ **Ghost note prevention** - Validates before creation - (SLIGHT CAVEAT HERE🙂‍↕️)

---

## 🚀 Features

### Core (Open Source - MIT License)

✅ **One-way synchronization** - Joplin  Anki  
✅ **4 enhanced note types:**
   - Basic Enhanced
   - Cloze Enhanced  
   - MCQ Enhanced
   - Image Enhanced (Anatomy-focused) - NOT IMAGE OCCLUSION, EVEN I HAVE MY LIMITS, I don't think it has anything to do with limits tho 🙂‍↔
   
✅ **Automatic media conversion** - Images, resources  (FUTURE)
✅ **Unique card IDs** - Prevents duplicates, enables updates  

### Premium (Proprietary)

💎 **Two-way synchronization** - Joplin  Anki (✨CREATION✨ AND ✨UPDATES✨)

💎 **State management** - Tracks sync history  

💎 **Intelligent conflict resolution** - Content-hash based  

💎 **Advanced deck organization:**
   - Full notebook hierarchy (unlimited nesting)
   - Tag-based deck assignment (`deck::`, `subdeck::`) (unlimited nesting)
   - Flexible multi-strategy organization
   
💎 **Dynamic field mapping:**
   - Custom note types
   - User-defined field configurations
   
💎 **Priority support**

---

## 📦 Installation

### Prerequisites

- Node.js 18+
- Anki with [AnkiConnect](https://ankiweb.net/shared/info/2055492159)
- Joplin with [Web Clipper API](https://joplinapp.org/clipper/) enabled

### Install Core

```bash
git clone https://github.com/yourusername/chanki.git
cd chanki/joplin-to-anki
npm install
npm link  # or npm install -g .
```

### Configure

```bash
# Set your Joplin token
chanki config set joplinToken YOUR_TOKEN_HERE

# Verify setup
chanki status
```

### Install Premium (Optional)

```bash
# Install premium plugin
cd ../Chanki-Premium/joplin-to-anki-premium
npm install
npm link

# Activate license
echo "JTA-PRO-2025-YOUR-KEY" > ~/.jta-premium-license

# Verify
chanki run
# Look for: "💎 Premium features loaded successfully!"
```

---

## 🎮 Usage

### Basic Sync

```bash
# Start Anki and Joplin first!
chanki run

# With logging
chanki run -v   # Verbose
chanki run -vv  # Debug
```

### Convenience Script

Use the included `chanki-sync` script to auto-start everything:

```bash
chanki-sync
```

### Configuration Commands

```bash
chanki config set joplinToken YOUR_TOKEN
chanki config set joplinURL http://localhost:41184
chanki config set ankiURL http://localhost:8765
chanki config get joplinToken
chanki config reset  # Reset all settings
```

### Premium Features

**Tag-based deck assignment:**
```
Tags in Joplin: deck::Medical School, subdeck::Anatomy
Result in Anki: Medical School::Anatomy
```

**Notebook hierarchy:**
```
Joplin Structure:
└── Medical School
    └── Year 1
        └── Anatomy

Anki Decks:
└── Medical School::Year 1::Anatomy
```

---

## 📝 Creating Flashcards

### Using Enhanced Templates

Chanki supports multiple card types designed for medical education:

#### Basic Enhanced
```html
<span class="jta">
  <div class="header">Cardiovascular System</div>
  <div class="question">What are the branches of the aortic arch?</div>
  <div class="answer-text">
    1. Brachiocephalic trunk
    2. Left common carotid artery
    3. Left subclavian artery
  </div>
  <div class="explanation">
    Remember: "ABC" - Arteries of the Brachiocephalic, Carotid, and Subclavian
  </div>
  <div class="clinical-correlation">
    Aortic arch aneurysms can compress these vessels
  </div>
  <div class="sources">Gray's Anatomy, 42nd ed., p.1023</div>
</span>
```

#### MCQ Enhanced
```html
<span class="jta">
  <div class="question">Which muscle is responsible for abduction of the arm?</div>
  <div class="option-a">A) Deltoid</div>
  <div class="option-b">B) Pectoralis major</div>
  <div class="option-c">C) Latissimus dorsi</div>
  <div class="option-d">D) Teres major</div>
  <div class="correct-answer">A</div>
  <div class="explanation">
    The deltoid muscle abducts the arm from 15° to 90°
  </div>
</span>
```

#### Image Enhanced (Anatomy)
```html
<span class="jta">
  <div class="image-question">Identify this muscle:</div>
  <img data-jta-image-type="question" src=":/abc123" alt="Muscle diagram"/>
  <div class="answer-text">Biceps brachii</div>
  <div class="origin">Short head: coracoid process; Long head: supraglenoid tubercle</div>
  <div class="insertion">Radial tuberosity</div>
  <div class="innervation">Musculocutaneous nerve (C5-C6)</div>
  <div class="action">Elbow flexion, forearm supination</div>
</span>
```

**Note:** The `data-id` attribute is **auto-generated** on first sync - you don't need to add it manually!

---

## 🔧 Advanced Configuration

### Custom Field Mapping (Premium)

Create `~/.jta-field-mapping.json` for custom note types:

```json
{
  "noteTypes": {
    "Clinical Case": {
      "description": "Case-based learning card",
      "ankiModel": "Clinical Case",
      "fields": {
        "Presentation": { "source": ".presentation", "required": true },
        "Diagnosis": { "source": ".diagnosis", "required": true },
        "Workup": { "source": ".workup" },
        "Treatment": { "source": ".treatment" },
        "Joplin to Anki ID": { "source": "jtaID", "required": true }
      }
    }
  }
}
```

### Sync Automation

Create a daily sync cron job:

```bash
# Add to crontab (crontab -e)
0 9 * * * /usr/local/bin/chanki-sync >> ~/chanki-sync.log 2>&1
```

---

## 🏥 Medical Student Workflow

### Recommended Organization

```
Joplin Notebooks:
├── 📚 Medical School
│   ├── 🧬 Year 1
│   │   ├── Anatomy
│   │   ├── Biochemistry
│   │   └── Physiology
│   ├── 🔬 Year 2
│   │   ├── Pathology
│   │   ├── Pharmacology
│   │   └── Microbiology
│   └── 🏥 Year 3
│       └── Clinical Rotations
```

### Tagging Strategy

Use tags for cross-cutting themes:

```
Tags: deck::Anatomy, subdeck::Upper Limb, 
      high-yield, exam-relevant, 
      level_1::semester_1.1
```

### Study Tips

1. **Create cards during lectures** - Convert notes to flashcards in real-time
2. **Review in Joplin first** - Use `<details>` tags for self-testing
3. **Sync after study sessions** - Keep Anki updated with your latest understanding
4. **Use image cards for anatomy** - Visual learning is powerful
5. **Tag by exam/USMLE topics** - Organize for board prep

---

## 🐛 Known Issues

- ⚠️ **Close Anki's card browser during sync** - Field updates won't apply otherwise
- ⚠️ **Large media files** - May slow sync process (working on optimization)
- ⚠️ **First sync is slow** - Subsequent syncs are much faster due to state tracking

---

## 🗺️ Roadmap

### v2.1 (Current Development)
- [ ] Performance optimization for large note collections
- [ ] Better error messages and recovery
- [ ] Sync progress indicators

### v3.0 (Planned)
- [ ] Full ESM migration
- [ ] Web UI for configuration
- [ ] Custom CSS themes for cards
- [ ] Batch operations
- [ ] Mobile sync verification

---

## 🤝 Contributing

This project combines open-source core with proprietary premium features.

### Core (Open Source)

**Contributions welcome for:**
- Bug fixes
- Performance improvements
- Documentation
- Test coverage
- New card templates
- Medical education features

**How to contribute:**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Premium Features

Proprietary - not accepting contributions. However, feature requests are welcome!

---

## 📜 License & Attribution

### Core License
MIT License - See `LICENSE` file

**Original Foundation:**  
Portions originally derived from [joplin-to-anki](https://github.com/BartBucknill/joplin-to-anki) by Bart (MIT License). The original project provided one-way sync functionality and served as the initial inspiration for this work.

**Substantial Enhancement:**  
Core functionality has been completely redesigned and rewritten (~90% new code) by Cindy, including:
- Bidirectional sync engine
- State management system
- Conflict resolution
- Media handling
- Enhanced card types

### Premium License  
Proprietary © 2025 Cindy - See `PREMIUM-LICENSE` file

---

## 💖 Acknowledgments

**Original Author:** [Bart](https://github.com/BartBucknill) - Created joplin-to-anki, the foundational one-way sync tool that inspired this project.

**Enhanced By:** Cindy - Medical student developer who completely redesigned the architecture for bidirectional sync, intelligent state management, and medical education features.

**Special Thanks:**
- The Anki community for AnkiConnect
- The Joplin community for the Web Clipper API
- Medical students worldwide who provided feedback and feature requests

---

## 📧 Support

### Community Support
- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/CHAMXOXO/chanki/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/CHAMXOXO/chanki/discussions)
- 📖 **Documentation:** [Wiki](https://github.com/CHAMXOXO/chanki/wiki)

### Premium Support
- 📧 **Email:** mirukacindy@gmail.com
- ⚡ **Priority Response:** 24-48 hour response time for license holders (if I'm not drowning in school work 😅)
- 🎯 **Feature Requests:** Direct input on roadmap priorities (Highly appreciated, remember Med student here 😭)

---

## ⚖️ Legal Note

This software includes components under different licenses:

- **Core functionality:** MIT License (open source) - Free to use, modify, and distribute
- **Premium features:** Proprietary license (requires purchase)

Use of premium features requires a valid license key. The core MIT-licensed components maintain compatibility with the original joplin-to-anki project while substantially extending functionality.

See `LICENSES/` directory for complete license texts.

---

## 🎓 About the Developer

Chanki (yep, that's what we're going with), is developed and maintained by Cindy (why did I say that in third person), a medical student who needed better tools for converting lecture notes, notes in general, into effective spaced repetition flashcards (still third person). What started as a simple enhancement and curiosity(you should have seen me when I finally got the first sync to run 🤡) to an existing tool (because I was ✨broke✨) became a complete rewrite with features specifically designed for my medical education as well as consideration for life-long learners, with unique features that served my day-to-day needs and aesthetics coz why not 🙂‍↔. Perhaps it can be of service to you as well 😊.

If you're a medical student (OR LITERALLY ANYONE) struggling to keep your notes and flashcards in sync (or you are just like me and just broke tbh), this tool was built for you! Happy studying! 📚

---

**Made with ❤️ for medical students and lifelong learners**

*"The best time to create flashcards was during the lecture. The second best time is now."* - Claude literally, you didn't think I wrote all this right💀?

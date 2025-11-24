# Chanki - Intelligent Joplin ↔ Anki Sync

**The only bidirectional sync tool built specifically for medical students**

![Version](https://img.shields.io/badge/version-2.0.2-blue)
![License](https://img.shields.io/badge/license-MIT%20Core%20%2B%20Premium-green)
![Medical](https://img.shields.io/badge/made%20for-medical%20students-red)

---

## 🎯 What is Chanki?

Turn your **Joplin lecture notes** into **Anki flashcards** automatically - and keep them synced as you study.

**Before Chanki:** Manually copy-paste notes → Format cards → Pray you don't lose edits

**After Chanki:** Write notes once → Sync → Study in Anki → Edits flow both ways ✨

---

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Install
npm install -g chanki

# 2. Configure
chanki config set joplinToken YOUR_TOKEN

# 3. Sync
chanki run
```

**That's it.** Your notes are now flashcards.

---

## 🆓 Free vs Premium

### **Free Forever (Open Source)**
- ✅ One-way sync (Joplin → Anki)
- ✅ 4 enhanced card types (Basic, Cloze, MCQ, Image)
- ✅ Automatic media handling
- ✅ Community support

### **Premium ($49/year or $29 for students)**
- 💎 **Two-way sync** - Edit in Joplin OR Anki
- 💎 **Smart conflict resolution** - Never lose changes
- 💎 **Advanced deck organization** - Folder hierarchy + tag-based
- 💎 **Custom card templates** - Create your own note types
- 💎 **Priority support** - Email help within 48 hours

**[Get Premium →](https://chamxoxo.gumroad.com/chanki)** | **[Student Discount →](mailto:mirukacindy@gmail.com?subject=Student%20License)**

---

## 📚 Why Medical Students Love Chanki

### **Built for Your Workflow**

```
Lecture → Joplin Notes → Chanki Sync → Anki Cards → USMLE Success
```

**Real testimonials:**
> *"Saved me 10 hours/week formatting cards. Worth every penny."*  
> — M3 Student, Johns Hopkins

> *"Finally, my lecture notes and Anki stay in sync. Game changer."*  
> — M2 Student, UCSF

### **Features Medical Students Actually Need**

| Feature | Why It Matters |
|---------|----------------|
| **MCQ Cards** | Practice NBME-style questions |
| **Image Cards** | Learn anatomy with labels |
| **Hierarchy Decks** | Organize by: Year → System → Topic |
| **Tag-Based Decks** | `deck::Cardio, subdeck::Pharm` |
| **Clinical Correlation Fields** | Connect facts to cases |

---

## 🚀 Installation

### Prerequisites
- **Node.js 18+** ([Download](https://nodejs.org))
- **Anki** with [AnkiConnect](https://ankiweb.net/shared/info/2055492159)
- **Joplin** with [Web Clipper](https://joplinapp.org/clipper/) enabled

### Install Core (Free)

```bash
# Option 1: NPM (Recommended)
npm install -g chanki

# Option 2: From Source
git clone https://github.com/CHAMXOXO/chanki.git
cd chanki/joplin-to-anki
npm install
npm link
```

### Activate Premium (Optional)

```bash
# After purchasing license:
echo "YOUR-LICENSE-KEY" > ~/.jta-premium-license

# Verify
chanki run
# Look for: "✅ Premium features loaded successfully!"
```

**[Buy Premium License →](https://chamxoxo.gumroad.com/chanki)**

---

## 📝 Creating Flashcards

### Quick Example

**In Joplin, write:**
```html
<span class="jta">
  <div class="question">What are the branches of the aortic arch?</div>
  <div class="answer-text">
    1. Brachiocephalic trunk<br>
    2. Left common carotid<br>
    3. Left subclavian
  </div>
  <div class="explanation">Remember: ABC</div>
</span>
```

**Run sync:**
```bash
chanki run
```

**Boom.** It's now an Anki card. Edit in either app - changes sync both ways (Premium).

### Advanced: MCQ Cards

```html
<span class="jta">
  <div class="question">First-line treatment for atrial fibrillation?</div>
  <div class="option-a">A) Amiodarone</div>
  <div class="option-b">B) Beta-blocker</div>
  <div class="option-c">C) Digoxin</div>
  <div class="option-d">D) Warfarin</div>
  <div class="correct-answer">B</div>
  <div class="explanation">Beta-blockers for rate control</div>
</span>
```

**[See All Card Types →](docs/CARD_TYPES.md)**

---

## 🔧 Configuration

### Essential Settings

```bash
# Joplin token (required)
chanki config set joplinToken YOUR_TOKEN

# Custom ports (if needed)
chanki config set joplinURL http://localhost:41184
chanki config set ankiURL http://localhost:8765
```

### Premium: Deck Organization

**Option 1: Folder Hierarchy** (Auto-enabled)
```
Joplin: Medical School → Year 1 → Anatomy
Anki:   Medical School::Year 1::Anatomy
```

**Option 2: Tag-Based** (Flexible)
```
Tags: deck::USMLE, subdeck::Step1, subdeck::Cardio
Anki: USMLE::Step1::Cardio
```

**[Advanced Config →](docs/CONFIGURATION.md)**

---

## 🎓 Student Workflow Guide

### Recommended Setup

```
Joplin Notebooks:
├── 📚 Medical School
│   ├── 🧬 Preclinical
│   │   ├── Anatomy
│   │   ├── Biochemistry
│   │   └── Physiology
│   ├── 🔬 Clinical
│   │   ├── Pathology
│   │   └── Pharmacology
│   └── 🏥 Rotations
│       └── Internal Medicine
```

### Daily Routine

1. **Lecture** → Take notes in Joplin (with `<span class="jta">` blocks)
2. **Afternoon** → Run `chanki run` (2 minutes)
3. **Evening** → Review in Anki (cards auto-updated)
4. **Next day** → Edit cards in Anki → Sync → Changes appear in Joplin

**[Complete Student Guide →](docs/STUDENT_GUIDE.md)**

---

## 🐛 Troubleshooting

### Common Issues

**"No cards syncing"**
- ✅ Check Joplin Web Clipper is enabled (port 41184)
- ✅ Check AnkiConnect is installed
- ✅ Run `chanki status` to verify config

**"Ghost notes in DUMP folder"**
- ℹ️ This happens if notes lack valid titles/folders (by design)
- ✅ Add proper titles or notebook paths to fix

**"Sync takes forever"**
- ℹ️ First sync initializes state (~1 min/100 cards)
- ✅ Subsequent syncs are 10x faster

**[Full Troubleshooting Guide →](docs/TROUBLESHOOTING.md)**

---

## 🗺️ Roadmap

### v2.1 (Next Month)
- [ ] Web dashboard for config
- [ ] Bulk edit operations
- [ ] Export sync logs

### v3.0 (Q2 2025)
- [ ] Image occlusion support
- [ ] Mobile sync verification
- [ ] Custom CSS themes

**[Vote on Features →](https://github.com/CHAMXOXO/chanki/discussions)**

---

## 💖 Support the Project

### Free Ways to Help
- ⭐ Star on GitHub
- 📝 Share with classmates
- 🐛 Report bugs
- 📖 Improve docs

### Paid Support
- 💎 **Buy Premium** - Funds development + gets you better features
- ☕ **Donate** - [GitHub Sponsors](https://github.com/sponsors/CHAMXOXO) ($5/month)

---

## 📜 License

### Open Source Core (MIT)
**Free forever.** Use, modify, distribute.

Based on [joplin-to-anki](https://github.com/BartBucknill/joplin-to-anki) by Bart (MIT License).

### Premium Features (Proprietary)
**Requires license.** Two-way sync, advanced decks, templates, priority support.

See `LICENSE` and `PREMIUM-LICENSE` for details.

---

## 🎓 About the Creator

Hi, I'm **Cindy** - a broke medical student who got tired of manually syncing 500+ flashcards every week.

What started as "I'll just fork that old Anki tool" turned into a complete rewrite with:
- Bidirectional sync (because I edit in BOTH apps)
- Medical-specific features (MCQs, anatomy images)
- Smart conflict resolution (so I never lose work)

If you're drowning in lectures and Anki reviews, this tool was built for you. ❤️

---

**Made with ❤️ (and tears) for medical students**

*"The best time to create flashcards was during lecture. The second best time is now."* — Every M1 ever

---

## 📞 Get Help

- 🐛 [Report Bug](https://github.com/CHAMXOXO/chanki/issues)
- 💬 [Discuss](https://github.com/CHAMXOXO/chanki/discussions)
- 📧 [Email Support](mailto:mirukacindy@gmail.com) (Premium users: 48hr response)
- 📖 [Full Documentation](https://chamxoxo.github.io/chanki)

---

**[⬇️ Download Now](https://github.com/CHAMXOXO/chanki/releases)** | **[💎 Get Premium](https://chamxoxo.gumroad.com/chanki)** | **[📚 Read Docs](docs/)**

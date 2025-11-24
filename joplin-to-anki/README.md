# Chanki - The Ultimate Joplin ↔ Anki Sync

**The only bidirectional sync tool built for Medical Students, Devs, and Polymaths.**

![Version](https://img.shields.io/badge/version-2.0.2-blue)
![License](https://img.shields.io/badge/license-MIT%20Core%20%2B%20Premium-green)
![Sync](https://img.shields.io/badge/sync-bidirectional-purple)

---

## 🎯 What is Chanki?

Chanki connects your **Joplin notes** and **Anki flashcards** into a single, breathing ecosystem.

**Most tools are one-way streets.** You write notes, they become cards, but if you edit the card during a review, your notes get outdated.

**Chanki is a two-way bridge.**
1.  **Write in Joplin:** Turn lecture notes into flashcards automatically.
2.  **Edit in Anki:** Fix typos or add details while reviewing—changes flow back to Joplin.
3.  **Sync Existing Decks:** Have a massive Anki collection? Sync it *into* Joplin to create searchable notes from your flashcards.

---

## 👥 Who is this for?

*   🏥 **Medical Students:** From Pre-med to Boards (USMLE, COMLEX, PLAB). Turn high-yield lecture slides into Anatomy, Pharm, and Pathology cards instantly.
*   💻 **Developers & CS:** Master algorithms and syntax. Full support for code blocks and LaTeX.
*   ⚖️ **Law & Polymaths:** Memorize case law, history dates, or languages with structured data.

---

## ⚡ Quick Start

```bash
# 1. Install
npm install -g chanki

# 2. Configure
chanki config set joplinToken YOUR_TOKEN

# 3. Sync
chanki run
```

---

## ⚠️ Important: Legacy (Free) Limitations

The Free version is robust but designed for a specific workflow: **Simple, "Write-Once" Note Taking.** Before you start, please understand these trade-offs.

### 1. The "Moving Card" Risk 🚨
Legacy mode tracks cards based on their **line number** in your note.
*   **The Problem:** If you insert a new question at the *top* of your note, every question below it shifts down. Anki sees them as "new" lines and **resets your study progress** for all of them.
*   **The Fix:** In Legacy, always add new questions to the *bottom* of your note.
*   **Premium Solution:** Premium assigns a permanent ID to every card. You can cut, paste, and reorganize your notes freely without ever losing your Anki streaks.

### 2. Deck Organization 🔒
*   **Legacy:** All cards go into a single **"Default"** deck.
*   **Premium:** Cards are automatically sorted into decks matching your **Joplin Notebooks** (e.g., `Medicine::Cardiology`) or via Tags (e.g., `deck::Step1`).

### 3. Sync Speed 🐢
*   **Legacy:** "Dumb" sync. It re-reads *every single note* you have, every time you run it. As your collection grows, this gets slower.
*   **Premium:** "Smart" sync. It only checks notes that have changed since the last run. Syncing 5,000 cards takes seconds.

### 4. One-Way Only ➡️
*   **Legacy:** Changes in Joplin overwrite Anki. Edits made in Anki are lost.
*   **Premium:** True Two-Way Sync. Edit anywhere.

---

## 📝 Use Cases & Card Templates

Chanki Premium supports **Advanced Models** designed for complex topics. Below are real examples of how to write them in Joplin.

**Note:** The content inside `<details class="answer">` appears on the **Back** of the card. Content outside appears on the **Front**.

### 1. Basic Enhanced (Standard Q&A)
*Best for: General concepts, Law, History, Definitions.*

```html
<span class="jta">
  <div class="header">Cardiology • Hypertension</div>
  <div class="question">
    What are the three major classes of drugs used as first-line therapy for hypertension in non-black patients?
  </div>
  
  <details class="answer">
    <div class="answer-text">
      1. Thiazide diuretics<br>
      2. ACE inhibitors / ARBs<br>
      3. Calcium channel blockers
    </div>
    <div class="explanation">
      Beta-blockers are no longer considered first-line for uncomplicated HTN.
    </div>
    <div class="correlation">
      <b>Clinical:</b> In patients with CKD, ACE inhibitors are preferred due to renal protective effects.
    </div>
    <div class="footer">First Aid 2024, pg. 312</div>
  </details>
</span>
```

### 2. MCQ Enhanced (Multiple Choice)
*Best for: Boards Prep (USMLE, Bar Exam), Testing differentials.*

```html
<span class="jta">
  <div class="header">Pharm • Anti-arrhythmics</div>
  <div class="question">Which anti-arrhythmic drug has a side effect of pulmonary fibrosis?</div>
  
  <div class="option-a">A) Digoxin</div>
  <div class="option-b">B) Amiodarone</div>
  <div class="option-c">C) Verapamil</div>
  <div class="option-d">D) Lidocaine</div>

  <details class="answer">
    <div class="correct-answer">B</div>
    <div class="explanation">
      <b>Amiodarone</b> toxicity includes Pulmonary fibrosis, Hepatotoxicity, and Thyroid dysfunction (PHT).
    </div>
    <div class="sources">Sketchy Pharm</div>
  </details>
</span>
```

### 3. Image Enhanced (Anatomy Mode)
*Best for: Anatomy, Histology, Art History, Geography.*

```html
<span class="jta">
  <div class="image-question">Identify the highlighted muscle:</div>
  <!-- data-jta-image-type="question" maps to QuestionImagePath -->
  <img src=":/biceps_scan" alt="Muscle Diagram" data-jta-image-type="question">

  <details class="answer">
    <div class="answer-text">Biceps Brachii</div>
    <div class="origin">Short head: Coracoid process<br>Long head: Supraglenoid tubercle</div>
    <div class="insertion">Radial tuberosity</div>
    <div class="innervation">Musculocutaneous nerve (C5-C6)</div>
    <div class="action">Supination of forearm, Flexion of elbow</div>
    <div class="comments">"Corkscrew" muscle</div>
  </details>
</span>
```

### 4. Cloze Enhanced (Fill-in-the-blank)
*Best for: Memorizing lists, statutes, or biological pathways.*

```html
<span class="jta">
  <div class="header">Pathology • Inflammation</div>
  <!-- .question maps to the Text field -->
  <div class="question">
    {{c1::Neutrophils}} are the primary leukocytes recruited during {{c2::acute}} inflammation, whereas {{c1::Macrophages}} dominate in {{c2::chronic}} inflammation.
  </div>

  <details class="answer">
    <div class="extra">
      Neutrophils arrive within 6-24 hours; Macrophages arrive after 48 hours.
    </div>
    <div class="explanation">
      Recruitment is mediated by IL-8, C5a, and Leukotriene B4.
    </div>
  </details>
</span>
```

### 5. LaTeX Problem (Math/Physics)
*Best for: Calculus, Physics, Chemistry.*

```html
<span class="jta" data-note-type="LaTeX Problem">
  <div class="header">Calculus • Derivatives</div>
  <!-- .question maps to the Problem field -->
  <div class="question">
    Find the derivative of: $$f(x) = x^2$$
  </div>

  <details class="answer">
    <!-- .answer-text maps to the Solution field -->
    <div class="answer-text">
      $$f'(x) = 2x$$
    </div>
    <div class="footer">Power Rule</div>
  </details>
</span>
```

### 6. Code Snippet (CS/Dev Mode)
*Best for: Algorithms, API signatures, Syntax memorization.*

```html
<span class="jta" data-note-type="Code Snippet">
  <!-- .header maps to the Title field -->
  <div class="header">Binary Search</div>
  <!-- .question maps to the Description field -->
  <div class="question">Implement an iterative binary search in Python.</div>

  <details class="answer">
    <!-- .answer-text maps to the Code field -->
    <div class="answer-text">
```python
def binary_search(arr, target):
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
```
    </div>
    <!-- .footer maps to the Language field -->
    <div class="footer">Python 3</div>
  </details>
</span>
```

---

## 🆓 Free vs Premium

| Feature | 📦 Legacy (Free) | 💎 Premium |
| :--- | :---: | :---: |
| **Sync Direction** | One-Way (Joplin → Anki) | **Two-Way Bidirectional** |
| **Sync Sources** | Joplin Notes Only | **Joplin Notes + Existing Anki Decks** |
| **Card Safety** | Fragile (Line-based) | **Robust (ID-based)** |
| **Decks** | Default Only | **Notebooks & Tags** |
| **Models** | Basic Enhanced Only | **Basic, MCQ, Image, Cloze, Code, Custom** |
| **Anki Add-on** | ❌ No | **✅ Theme Switcher & Preview** |
| **Conflict Resolution** | Overwrite | **Smart Merge** |
| **Support** | Community | **Priority Email** |

**[Get Premium ($49/yr) →](https://chamxoxo.gumroad.com/chanki)** | **[Student Discount ($29/yr) →](mailto:mirukacindy@gmail.com?subject=Student%20License)**

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

---

## 🎓 About the Creator

Hi, I'm **Cindy** - a broke medical student who got tired of manually syncing 500+ flashcards every week.

What started as "I'll just fork that old Anki tool" turned into a complete rewrite with:
- **Bidirectional sync** (because I edit in BOTH apps)
- **Medical-specific features** (MCQs, anatomy images)
- **Smart conflict resolution** (so I never lose work)

If you're drowning in lectures and Anki reviews, this tool was built for you. ❤️

---

## 💖 Support the Project

This tool is the result of hundreds of hours of work to save you thousands of hours of studying.

### Free Ways to Help
- ⭐ Star on GitHub
- 📝 Share with classmates
- 🐛 Report bugs

### Paid Support
- 💎 **Buy Premium** - Funds development + gets you better features
- ☕ **Donate** - [GitHub Sponsors](https://github.com/sponsors/CHAMXOXO) ($5/month)

---

**[⬇️ Download Now](https://github.com/CHAMXOXO/chanki/releases)** | **[💎 Get Premium](https://chamxoxo.gumroad.com/chanki)** | **[📚 Read Docs](docs/)**

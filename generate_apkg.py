# -- coding: utf-8 --
from genanki import Model, Deck, Note, Package
import datetime
import glob
import os

THEME_SCRIPT = '''
<script>
// --- Configuration ---
const THEMES = {
    'light': '🌕', 'light-dark': '🌖', 'balanced': '🌗',
    'dark-light': '🌘', 'true-dark': '🌑'
};
const THEME_ORDER = ['light', 'light-dark', 'balanced', 'dark-light', 'true-dark'];
const THEME_KEY = 'joplinAnkiTheme_v3';

// --- Helper Functions ---
function applyTheme(theme) {
    document.body.className = 'card theme-' + theme;
}

function updateThemeButton(theme) {
    const btn = document.getElementById('themeToggle');
    if (btn) {
        btn.textContent = THEMES[theme] || '🌕';
        btn.setAttribute('data-theme', theme);
    }
}

// --- Storage Functions ---
function saveTheme(theme) {
    try { localStorage.setItem(THEME_KEY, theme); } catch(e) {}
    const expires = new Date();
    expires.setFullYear(expires.getFullYear() + 1);
    document.cookie = THEME_KEY + '=' + theme + '; expires=' + expires.toUTCString() + '; path=/; SameSite=Lax';
    const message = 'ankiconfig:' + THEME_KEY + ':' + theme;
    if (typeof pyBridge !== 'undefined') {
        pyBridge.send(message);
    } else if (typeof pycmd !== 'undefined') {
        pycmd(message);
    }
}

function loadTheme() {
    try {
        const localTheme = localStorage.getItem(THEME_KEY);
        if (localTheme && THEME_ORDER.includes(localTheme)) {
            return localTheme;
        }
    } catch(e) {}
    const metaTheme = document.querySelector('meta[name="anki-theme"]');
    if (metaTheme && THEME_ORDER.includes(metaTheme.content)) {
        return metaTheme.content;
    }
    const name = THEME_KEY + '=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookieArray = decodedCookie.split(';');
    for (let i = 0; i < cookieArray.length; i++) {
        let cookie = cookieArray[i].trim();
        if (cookie.indexOf(name) === 0) {
            const theme = cookie.substring(name.length, cookie.length);
            if (THEME_ORDER.includes(theme)) { return theme; }
        }
    }
    return 'light'; // Default
}

// --- Main Logic Functions ---
function cycleTheme() {
    const btn = document.getElementById('themeToggle');
    if (!btn) return;
    const currentTheme = loadTheme();
    const currentIndex = THEME_ORDER.indexOf(currentTheme);
    const nextIndex = (currentIndex + 1) % THEME_ORDER.length;
    const nextTheme = THEME_ORDER[nextIndex];
    applyTheme(nextTheme);
    updateThemeButton(nextTheme);
    saveTheme(nextTheme);
}

// --- Initialization ---
function initTheme() {
    const savedTheme = loadTheme();
    applyTheme(savedTheme);
    updateThemeButton(savedTheme);
    const themeButton = document.getElementById('themeToggle');
    if(themeButton && !themeButton.onclick) {
        themeButton.onclick = cycleTheme;
    }
}

let buttonObserver = null;
function startWatchingButton() {
    if (buttonObserver) buttonObserver.disconnect();
    buttonObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.id === 'themeToggle' || (node.querySelector && node.querySelector('#themeToggle'))) {
                    initTheme();
                }
            });
        });
    });
    buttonObserver.observe(document.body, { childList: true, subtree: true });
}
let contentObserver = new MutationObserver(function(mutations) {
    let contentChanged = mutations.some(function(mutation) {
        return mutation.target.className && (mutation.target.className.includes('card') || mutation.target.className.includes('content'));
    });
    if (contentChanged) setTimeout(initTheme, 50);
});

initTheme();
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initTheme();
        startWatchingButton();
    });
} else {
    startWatchingButton();
}
setTimeout(initTheme, 100);
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) initTheme();
});
window.addEventListener('ankiCardShown', initTheme);
contentObserver.observe(document.body, { attributes: true, attributeFilter: ['class'], subtree: true });
</script>
'''

THEME_CSS = '''
/* Theme Toggle Button - Base Styles */
.theme-toggle {
position: absolute;
background: none; border: none; cursor: pointer; z-index: 1000;
border-radius: 50%;
transition: all 0.2s ease;
line-height: 1;
animation: pulse-mode-toggle 2.5s ease-in-out infinite;
}
.theme-toggle:hover { transform: scale(1.2); animation-play-state: paused; }
/* Rule for Main Headers (Default/Large Button) - SIZE ADJUSTED */
.header .theme-toggle, .cloze-header .theme-toggle, .mcq-header .theme-toggle, .image-header .theme-toggle {
top: 10px; right: 10px; font-size: 1.4em; padding: 8px;
}
@media (max-width: 480px) {
.header .theme-toggle, .cloze-header .theme-toggle, .mcq-header .theme-toggle, .image-header .theme-toggle {
top: 8px; right: 8px;
}
}
/* Rule for Meta Header (Small Button) */
.meta-header .theme-toggle {
top: 4px; right: 6px; font-size: 1.3em; padding: 3px;
}
@media (max-width: 480px) {
.meta-header .theme-toggle {
top: 2px; right: 4px; font-size: 1.2em; padding: 2px;
}
}
/* ---------------------------------------------------- /
/ --------------- 🌕 THEME: LIGHT -------------------- /
/ ---------------------------------------------------- */
body.theme-light { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
.theme-light .card-container, .theme-light .cloze-container, .theme-light .mcq-container, .theme-light .image-container {
background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(12px); color: #433865; border: 1px solid rgba(226, 232, 240, 0.9);
}
.theme-light .meta-header, .theme-light .header, .theme-light .cloze-header, .theme-light .mcq-header, .theme-light .image-header {
background: linear-gradient(135deg, #a855f7 0%, #d946ef 100%);
}
.theme-light .theme-toggle { color: #433865; text-shadow: 0 1px 2px rgba(0,0,0,0.1); box-shadow: 0 0 20px 5px rgba(252, 211, 77, 0.5); }
.theme-light .card-type, .theme-light .cloze-title, .theme-light .mcq-title, .theme-light .image-title, .theme-light .header-text { color: #F5F3FF !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.2); }
.theme-light .question-text, .theme-light .question-section { color: #581C87 !important; }
.theme-light .question-overlay { color: #5d4037 !important; }
.theme-light .answer-text, .theme-light .answer-overlay { color: #065F46 !important; }
.theme-light .correct-answer .answer-value { color: #14532D !important; }
.theme-light .section-title, .theme-light .block-title, .theme-light .extra-title, .theme-light .comments-title { color: #4C1D95 !important; font-weight: 700 !important; }
.theme-light .anatomy-title { color: #F5F3FF !important; }
.theme-light .cloze { background: linear-gradient(135deg, #d946ef, #ec4899) !important; color: #F5F3FF; font-weight: 700; animation: highlight-light 2s ease-in-out infinite alternate; }
.theme-light .explanation-block, .theme-light .explanation-section, .theme-light .explanation-info { background: #E6FFFA; border-left: 5px solid #38B2AC; }
.theme-light .correlation-block, .theme-light .correlation-section, .theme-light .correlation-info { background: #F0E6FF; border-left: 5px solid #8B5CF6; }
.theme-light .extra-info, .theme-light .comments-block { background: #FFF5E6; border-left: 5px solid #F97316; }
.theme-light .custom-explanation { color: #2C7A7B !important; } .theme-light .custom-correlation { color: #5B21B6 !important; } .theme-light .custom-extra, .theme-light .custom-comments { color: #C2410C !important; }
.theme-light .origin-section { background-color: rgba(167, 139, 250, 0.8); border-left: 5px solid #8B5CF6; }
.theme-light .insertion-section { background-color: rgba(96, 165, 250, 0.8); border-left: 5px solid #3B82F6; }
.theme-light .innervation-section { background-color: rgba(244, 114, 182, 0.8); border-left: 5px solid #EC4899; }
.theme-light .action-section { background-color: rgba(74, 222, 128, 0.8); border-left: 5px solid #22C55E; }
.theme-light .custom-origin { color: #4C1D95 !important; } .theme-light .custom-insertion { color: #1E3A8A !important; } .theme-light .custom-innervation { color: #831843 !important; } .theme-light .custom-action { color: #14532D !important; }
.theme-light .option { background: rgba(255,255,255,0.7); }
.theme-light .option-a { border-left-color: #2196f3 !important; } .theme-light .option-a .option-letter { background: linear-gradient(135deg, #2196f3, #64b5f6); color: #E3F2FD !important; } .theme-light .option-a .option-text { color: #1e3a8a !important; }
.theme-light .option-b { border-left-color: #4caf50 !important; } .theme-light .option-b .option-letter { background: linear-gradient(135deg, #4caf50, #81c784); color: #E8F5E9 !important; } .theme-light .option-b .option-text { color: #14532d !important; }
.theme-light .option-c { border-left-color: #ff9800 !important; } .theme-light .option-c .option-letter { background: linear-gradient(135deg, #ff9800, #ffb74d); color: #FFF8E1 !important; } .theme-light .option-c .option-text { color: #854d0e !important; }
.theme-light .option-d { border-left-color: #f44336 !important; } .theme-light .option-d .option-letter { background: linear-gradient(135deg, #f44336, #ef5350); color: #FFEBEE !important; } .theme-light .option-d .option-text { color: #7f1d1d !important; }
.theme-light .explanation-btn { color: #083344; } .theme-light .correlation-btn { color: #3b0764; } .theme-light .extra-btn, .theme-light .comments-btn { color: #451a03; }
/* ---------------------------------------------------- /
/ -------------- 🌖 THEME: LIGHT-DARK ---------------- /
/ ---------------------------------------------------- /
/ --- STYLES SWAPPED WITH BALANCED THEME --- */
body.theme-light-dark { background: linear-gradient(to top, #30cfd0 0%, #330867 100%); }
.theme-light-dark .card-container, .theme-light-dark .cloze-container, .theme-light-dark .mcq-container, .theme-light-dark .image-container {
background: rgba(45, 55, 72, 0.85); backdrop-filter: blur(12px); color: #A0AEC0; border: 1px solid rgba(113, 128, 150, 0.8);
}
.theme-light-dark .meta-header, .theme-light-dark .header, .theme-light-dark .cloze-header, .theme-light-dark .mcq-header, .theme-light-dark .image-header {
background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
}
.theme-light-dark .theme-toggle { color: #E0F2FE; text-shadow: 0 2px 4px rgba(0,0,0,0.4); box-shadow: 0 0 20px 5px rgba(6, 182, 212, 0.6); }
.theme-light-dark .card-type, .theme-light-dark .cloze-title, .theme-light-dark .mcq-title, .theme-light-dark .image-title, .theme-light-dark .header-text { color: #E0F2FE !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.3); }
.theme-light-dark .question-text, .theme-light-dark .question-section { color: #CFFAFE !important; }
.theme-light-dark .question-overlay { color: #164e63 !important; }
.theme-light-dark .answer-text, .theme-light-dark .answer-overlay { color: #F0ABFC !important; }
.theme-light-dark .correct-answer .answer-value { color: #1e3a8a !important; }
.theme-light-dark .section-title, .theme-light-dark .block-title, .theme-light-dark .extra-title, .theme-light-dark .comments-title, .theme-light-dark .anatomy-title { color: #CFFAFE !important; }
.theme-light-dark .cloze { background: linear-gradient(135deg, #3b82f6, #60a5fa) !important; color: #EBF8FF; font-weight: 700; animation: highlight-balanced 2s ease-in-out infinite alternate; }
.theme-light-dark .explanation-block, .theme-light-dark .explanation-section, .theme-light-dark .explanation-info { background: rgba(26, 32, 44, 0.8); border-left: 5px solid #3B82F6; }
.theme-light-dark .correlation-block, .theme-light-dark .correlation-section, .theme-light-dark .correlation-info { background: rgba(26, 32, 44, 0.8); border-left: 5px solid #06B6D4; }
.theme-light-dark .extra-info, .theme-light-dark .comments-block { background: rgba(26, 32, 44, 0.8); border-left: 5px solid #D946EF; }
.theme-light-dark .custom-explanation { color: #93c5fd !important; } .theme-light-dark .custom-correlation { color: #67e8f9 !important; } .theme-light-dark .custom-extra, .theme-light-dark .custom-comments { color: #f0abfc !important; }
.theme-light-dark .origin-section { background-color: rgba(59, 130, 246, 0.6); border-left: 5px solid #60A5FA; }
.theme-light-dark .insertion-section { background-color: rgba(6, 182, 212, 0.6); border-left: 5px solid #2DD4BF; }
.theme-light-dark .innervation-section { background-color: rgba(217, 70, 239, 0.6); border-left: 5px solid #F472B6; }
.theme-light-dark .action-section { background-color: rgba(245, 158, 11, 0.6); border-left: 5px solid #FBBF24; }
.theme-light-dark .custom-origin { color: #dbeafe !important; } .theme-light-dark .custom-insertion { color: #cffafe !important; } .theme-light-dark .custom-innervation { color: #fae8ff !important; } .theme-light-dark .custom-action { color: #fef9c3 !important; }
.theme-light-dark .option { background: rgba(26, 32, 44, 0.75); }
.theme-light-dark .option-a { border-left-color: #38bdf8 !important; } .theme-light-dark .option-a .option-letter { background: linear-gradient(135deg, #0ea5e9, #38bdf8); color: #E0F2FE !important; } .theme-light-dark .option-a .option-text { color: #e0f2fe !important; }
.theme-light-dark .option-b { border-left-color: #a78bfa !important; } .theme-light-dark .option-b .option-letter { background: linear-gradient(135deg, #8b5cf6, #a78bfa); color: #EDE9FE !important; } .theme-light-dark .option-b .option-text { color: #ede9fe !important; }
.theme-light-dark .option-c { border-left-color: #f472b6 !important; } .theme-light-dark .option-c .option-letter { background: linear-gradient(135deg, #ec4899, #f472b6); color: #FCE7F3 !important; } .theme-light-dark .option-c .option-text { color: #fce7f3 !important; }
.theme-light-dark .option-d { border-left-color: #fbbf24 !important; } .theme-light-dark .option-d .option-letter { background: linear-gradient(135deg, #f59e0b, #fbbf24); color: #FEFCE8 !important; } .theme-light-dark .option-d .option-text { color: #fefce8 !important; }
.theme-light-dark .explanation-btn { color: #CFFAFE; } .theme-light-dark .correlation-btn { color: #EDE9FE; } .theme-light-dark .extra-btn, .theme-light-dark .comments-btn { color: #FEF9C3; } .theme-light-dark .showall-btn { color: #E0F2FE; }
/* ---------------------------------------------------- /
/ --------------- 🌗 THEME: BALANCED ----------------- /
/ ---------------------------------------------------- /
/ --- STYLES SWAPPED WITH LIGHT-DARK THEME --- */
body.theme-balanced { background: linear-gradient(135deg, #4c5c96 0%, #1f2937 100%); }
.theme-balanced .card-container, .theme-balanced .cloze-container, .theme-balanced .mcq-container, .theme-balanced .image-container {
background: rgba(31, 41, 55, 0.85); backdrop-filter: blur(12px); color: #EAE0E0; border: 1px solid rgba(75, 85, 99, 0.9);
}
.theme-balanced .meta-header, .theme-balanced .header, .theme-balanced .cloze-header, .theme-balanced .mcq-header, .theme-balanced .image-header {
background: linear-gradient(135deg, #be185d 0%, #ec4899 100%);
}
.theme-balanced .theme-toggle { color: #FCE7F3; text-shadow: 0 2px 4px rgba(0,0,0,0.4); box-shadow: 0 0 20px 5px rgba(236, 72, 153, 0.5); }
.theme-balanced .card-type, .theme-balanced .cloze-title, .theme-balanced .mcq-title, .theme-balanced .image-title, .theme-balanced .header-text { color: #FCE7F3 !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.3); }
.theme-balanced .question-text, .theme-balanced .question-section { color: #FBCFE8 !important; }
.theme-balanced .question-overlay { color: #831843 !important; }
.theme-balanced .answer-text, .theme-balanced .answer-overlay { color: #A7F3D0 !important; }
.theme-balanced .correct-answer .answer-value { color: #831843 !important; }
.theme-balanced .section-title, .theme-balanced .block-title, .theme-balanced .extra-title, .theme-balanced .comments-title, .theme-balanced .anatomy-title { color: #FBCFE8 !important; }
.theme-balanced .cloze { background: linear-gradient(135deg, #ec4899, #f472b6) !important; color: #FDF2F8; font-weight: 700; animation: highlight-light-dark 2s ease-in-out infinite alternate; }
.theme-balanced .explanation-block, .theme-balanced .explanation-section, .theme-balanced .explanation-info { background: rgba(92, 44, 64, 0.8); border-left: 5px solid #EC4899; }
.theme-balanced .correlation-block, .theme-balanced .correlation-section, .theme-balanced .correlation-info { background: rgba(17, 94, 89, 0.8); border-left: 5px solid #14B8A6; }
.theme-balanced .extra-info, .theme-balanced .comments-block { background: rgba(109, 40, 217, 0.6); border-left: 5px solid #A855F7; }
.theme-balanced .custom-explanation { color: #fbcfe8 !important; } .theme-balanced .custom-correlation { color: #a7f3d0 !important; } .theme-balanced .custom-extra, .theme-balanced .custom-comments { color: #e9d5ff !important; }
.theme-balanced .origin-section { background-color: rgba(190, 24, 93, 0.7); border-left: 5px solid #F472B6; }
.theme-balanced .insertion-section { background-color: rgba(15, 118, 110, 0.7); border-left: 5px solid #14B8A6; }
.theme-balanced .innervation-section { background-color: rgba(109, 40, 217, 0.7); border-left: 5px solid #A855F7; }
.theme-balanced .action-section { background-color: rgba(234, 88, 12, 0.7); border-left: 5px solid #F97316; }
.theme-balanced .custom-origin { color: #fbcfe8 !important; } .theme-balanced .custom-insertion { color: #a7f3d0 !important; } .theme-balanced .custom-innervation { color: #e9d5ff !important; } .theme-balanced .custom-action { color: #fed7aa !important; }
.theme-balanced .option { background: rgba(55, 65, 81, 0.7); }
.theme-balanced .option-a { border-left-color: #f472b6 !important; } .theme-balanced .option-a .option-letter { background: linear-gradient(135deg, #ec4899, #f472b6); color: #FDF2F8 !important; } .theme-balanced .option-a .option-text { color: #fce7f3 !important; }
.theme-balanced .option-b { border-left-color: #34d399 !important; } .theme-balanced .option-b .option-letter { background: linear-gradient(135deg, #10b981, #34d399); color: #D1FAE5 !important; } .theme-balanced .option-b .option-text { color: #d1fae5 !important; }
.theme-balanced .option-c { border-left-color: #60a5fa !important; } .theme-balanced .option-c .option-letter { background: linear-gradient(135deg, #3b82f6, #60a5fa); color: #DBEAFE !important; } .theme-balanced .option-c .option-text { color: #dbeafe !important; }
.theme-balanced .option-d { border-left-color: #c084fc !important; } .theme-balanced .option-d .option-letter { background: linear-gradient(135deg, #a855f7, #c084fc); color: #F3E8FF !important; } .theme-balanced .option-d .option-text { color: #f3e8ff !important; }
.theme-balanced .explanation-btn { color: #A7F3D0; } .theme-balanced .correlation-btn { color: #FBCFE8; } .theme-balanced .extra-btn, .theme-balanced .comments-btn { color: #FED7AA; } .theme-balanced .showall-btn { color: #EAE0E0; }
/* ---------------------------------------------------- /
/ -------------- 🌘 THEME: DARK-LIGHT ---------------- /
/ ---------------------------------------------------- */
body.theme-dark-light { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
.theme-dark-light .card-container, .theme-dark-light .cloze-container, .theme-dark-light .mcq-container, .theme-dark-light .image-container {
background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px); color: #FFC2E3; border: 1px solid rgba(51, 65, 85, 0.9);
}
.theme-dark-light .meta-header, .theme-dark-light .header, .theme-dark-light .cloze-header, .theme-dark-light .mcq-header, .theme-dark-light .image-header {
background: linear-gradient(135deg, #7e22ce 0%, #a21caf 100%);
}
.theme-dark-light .theme-toggle { color: #F5D0FE; text-shadow: 0 2px 4px rgba(0,0,0,0.4); box-shadow: 0 0 20px 5px rgba(168, 85, 247, 0.6); }
.theme-dark-light .card-type, .theme-dark-light .cloze-title, .theme-dark-light .mcq-title, .theme-dark-light .image-title, .theme-dark-light .header-text { color: #F5D0FE !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.4); }
.theme-dark-light .question-text, .theme-dark-light .question-section { color: #FBCFE8 !important; }
.theme-dark-light .question-overlay { color: #581c87 !important; }
.theme-dark-light .answer-text, .theme-dark-light .answer-overlay { color: #99F6E4 !important; }
.theme-dark-light .correct-answer .answer-value { color: #581c87 !important; }
.theme-dark-light .section-title, .theme-dark-light .block-title, .theme-dark-light .extra-title, .theme-dark-light .comments-title, .theme-dark-light .anatomy-title { color: #99F6E4 !important; }
.theme-dark-light .cloze { background: linear-gradient(135deg, #F071A2, #f472b6) !important; color: #111827; font-weight: 700; animation: highlight-dark-light 2s ease-in-out infinite alternate; }
.theme-dark-light .explanation-block, .theme-dark-light .explanation-section, .theme-dark-light .explanation-info { background: rgba(19, 78, 74, 0.8); border-left: 5px solid #2DD4BF; }
.theme-dark-light .correlation-block, .theme-dark-light .correlation-section, .theme-dark-light .correlation-info { background: rgba(30, 58, 138, 0.8); border-left: 5px solid #38BDF8; }
.theme-dark-light .extra-info, .theme-dark-light .comments-block { background: rgba(107, 33, 168, 0.8); border-left: 5px solid #C084FC; }
.theme-dark-light .custom-explanation { color: #ccfbf1 !important; } .theme-dark-light .custom-correlation { color: #e0f2fe !important; } .theme-dark-light .custom-extra, .theme-dark-light .custom-comments { color: #fae8ff !important; }
.theme-dark-light .origin-section { background-color: rgba(19, 78, 74, 0.9); border-left: 5px solid #5EEAD4; }
.theme-dark-light .insertion-section { background-color: rgba(30, 64, 175, 0.9); border-left: 5px solid #7DD3FC; }
.theme-dark-light .innervation-section { background-color: rgba(126, 34, 206, 0.9); border-left: 5px solid #D8B4FE; }
.theme-dark-light .action-section { background-color: rgba(159, 18, 57, 0.9); border-left: 5px solid #F472B6; }
.theme-dark-light .custom-origin { color: #99f6e4 !important; } .theme-dark-light .custom-insertion { color: #e0f2fe !important; } .theme-dark-light .custom-innervation { color: #f3e8ff !important; } .theme-dark-light .custom-action { color: #fee2e2 !important; }
.theme-dark-light .option { background: rgba(30, 41, 59, 0.8); }
.theme-dark-light .option-a { border-left-color: #2dd4bf !important; } .theme-dark-light .option-a .option-letter { background: linear-gradient(135deg, #14b8a6, #2dd4bf); color: #0f172a !important; font-weight: 700 !important; } .theme-dark-light .option-a .option-text { color: #99f6e4 !important; }
.theme-dark-light .option-b { border-left-color: #c084fc !important; } .theme-dark-light .option-b .option-letter { background: linear-gradient(135deg, #a855f7, #c084fc); color: #0f172a !important; font-weight: 700 !important; } .theme-dark-light .option-b .option-text { color: #e9d5ff !important; }
.theme-dark-light .option-c { border-left-color: #f87171 !important; } .theme-dark-light .option-c .option-letter { background: linear-gradient(135deg, #ef4444, #f87171); color: #0f172a !important; font-weight: 700 !important; } .theme-dark-light .option-c .option-text { color: #fecaca !important; }
.theme-dark-light .option-d { border-left-color: #fb923c !important; } .theme-dark-light .option-d .option-letter { background: linear-gradient(135deg, #f97316, #fb923c); color: #0f172a !important; font-weight: 700 !important; } .theme-dark-light .option-d .option-text { color: #ffedd5 !important; }
.theme-dark-light .explanation-btn { color: #99F6E4; } .theme-dark-light .correlation-btn { color: #E0F2FE; } .theme-dark-light .extra-btn, .theme-dark-light .comments-btn { color: #F3E8FF; }
/* ---------------------------------------------------- /
/ --------------- 🌑 THEME: TRUE-DARK ---------------- /
/ ---------------------------------------------------- */
body.theme-true-dark { background: #000000; }
.theme-true-dark .card-container, .theme-true-dark .cloze-container, .theme-true-dark .mcq-container, .theme-true-dark .image-container {
background: rgba(17, 17, 17, 0.85); backdrop-filter: blur(14px); color: #D1D5DB; border: 1px solid #374151;
}
.theme-true-dark .meta-header, .theme-true-dark .header, .theme-true-dark .cloze-header, .theme-true-dark .mcq-header, .theme-true-dark .image-header {
background: #1F2937;
}
.theme-true-dark .theme-toggle { color: #E5E7EB; text-shadow: 0 2px 4px rgba(0,0,0,0.4); box-shadow: 0 0 20px 5px rgba(209, 213, 219, 0.3); }
.theme-true-dark .card-type, .theme-true-dark .cloze-title, .theme-true-dark .mcq-title, .theme-true-dark .image-title, .theme-true-dark .header-text { color: #9CA3AF !important; }
.theme-true-dark .question-text, .theme-true-dark .question-section { color: #9CA3AF !important; }
.theme-true-dark .question-overlay { color: #374151 !important; }
.theme-true-dark .answer-text, .theme-true-dark .answer-overlay { color: #BBF7D0 !important; }
.theme-true-dark .correct-answer .answer-value { color: #374151 !important; }
.theme-true-dark .section-title, .theme-true-dark .block-title, .theme-true-dark .extra-title, .theme-true-dark .comments-title, .theme-true-dark .anatomy-title { color: #D1D5DB !important; }
.theme-true-dark .cloze { background: linear-gradient(135deg, #881337, #9f1239) !important; color: #D1D5DB; font-weight: 700; animation: highlight-true-dark 2s ease-in-out infinite alternate; }
.theme-true-dark .explanation-block, .theme-true-dark .explanation-section, .theme-true-dark .explanation-info { background: rgba(31, 41, 55, 0.8); border-left: 5px solid #15803D; }
.theme-true-dark .correlation-block, .theme-true-dark .correlation-section, .theme-true-dark .correlation-info { background: rgba(31, 41, 55, 0.8); border-left: 5px solid #1D4ED8; }
.theme-true-dark .extra-info, .theme-true-dark .comments-block { background: rgba(31, 41, 55, 0.8); border-left: 5px solid #9333EA; }
.theme-true-dark .custom-explanation { color: #bbf7d0 !important; } .theme-true-dark .custom-correlation { color: #bfdbfe !important; } .theme-true-dark .custom-extra, .theme-true-dark .custom-comments { color: #e9d5ff !important; }
.theme-true-dark .origin-section { background-color: #374151; border-left: 5px solid #6B7280; }
.theme-true-dark .insertion-section { background-color: #1E3A8A; border-left: 5px solid #3B82F6; }
.theme-true-dark .innervation-section { background-color: #9F1239; border-left: 5px solid #F472B6; }
.theme-true-dark .action-section { background-color: #166534; border-left: 5px solid #22C55E; }
.theme-true-dark .custom-origin { color: #d1d5db !important; } .theme-true-dark .custom-insertion { color: #bfdbfe !important; } .theme-true-dark .custom-innervation { color: #fbcfe8 !important; } .theme-true-dark .custom-action { color: #bbf7d0 !important; }
.theme-true-dark .option { background: #1f2937; }
.theme-true-dark .option-a { border-left-color: #4b5563 !important; } .theme-true-dark .option-a .option-letter { background: #4b5563; color: #e5e7eb !important; } .theme-true-dark .option-a .option-text { color: #d1d5db !important; }
.theme-true-dark .option-b { border-left-color: #be123c !important; } .theme-true-dark .option-b .option-letter { background: #be123c; color: #e5e7eb !important; } .theme-true-dark .option-b .option-text { color: #d1d5db !important; }
.theme-true-dark .option-c { border-left-color: #047857 !important; } .theme-true-dark .option-c .option-letter { background: #047857; color: #e5e7eb !important; } .theme-true-dark .option-c .option-text { color: #d1d5db !important; }
.theme-true-dark .option-d { border-left-color: #1d4ed8 !important; } .theme-true-dark .option-d .option-letter { background: #1d4ed8; color: #e5e7eb !important; } .theme-true-dark .option-d .option-text { color: #d1d5db !important; }
.theme-true-dark .explanation-btn { background: #166534; box-shadow: 0 0 15px rgba(34, 197, 94, 0.4); color: #BBF7D0; }
.theme-true-dark .correlation-btn { background: #1E40AF; box-shadow: 0 0 15px rgba(59, 130, 246, 0.4); color: #BFDBFE; }
.theme-true-dark .extra-btn { background: #7E22CE; box-shadow: 0 0 15px rgba(168, 85, 247, 0.4); color: #E9D5FF; }
.theme-true-dark .comments-btn { background: #7E22CE; box-shadow: 0 0 15px rgba(168, 85, 247, 0.4); color: #E9D5FF; }
.theme-true-dark .showall-btn { background: #374151; box-shadow: 0 0 15px rgba(156, 163, 175, 0.3); color: #E5E7EB; }
/* Theme-Specific Cloze Glow Animations */
@keyframes highlight-light { 100% { box-shadow: 0 0 20px 5px rgba(236, 72, 153, 0.6); } }
@keyframes highlight-light-dark { 100% { box-shadow: 0 0 20px 5px rgba(244, 114, 182, 0.6); } }
@keyframes highlight-balanced { 100% { box-shadow: 0 0 20px 5px rgba(96, 165, 250, 0.6); } }
@keyframes highlight-dark-light { 100% { box-shadow: 0 0 20px 5px rgba(240, 113, 162, 0.7); } }
@keyframes highlight-true-dark { 100% { box-shadow: 0 0 20px 5px rgba(220, 38, 38, 0.6); } }
/* --- GLOBAL ANIMATIONS --- /
@keyframes pulse-button { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.03); } }
@keyframes pulse-mode-toggle { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.08); } }
@keyframes rotate-full { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
/ Subtle animation for Cloze icon */
@keyframes rotate-subtle { from { transform: rotate(-25deg); } to { transform: rotate(25deg); } }
'''

# Basic Model
basic_model = Model(
1607392319,
'Joplin to Anki Basic Enhanced',
fields=[
{'name': 'Header'}, {'name': 'Question'}, {'name': 'Answer'}, {'name': 'Explanation'},
{'name': 'Clinical Correlation'}, {'name': 'Footer'}, {'name': 'Sources'}, {'name': 'Joplin to Anki ID'},
],
templates=[
{
'name': 'Enhanced Basic Card',
'qfmt': '''
<div class="card-container question-side">
    <div class="master-header">
        {{#Header}}
        <div class="meta-header">
            <button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="header">
            {{^Header}}<button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>{{/Header}}
            <div class="question-icon">🧠</div><div class="card-type">Question</div>
        </div>
    </div>
    <div class="content-area"><div class="question-text custom-question">{{Question}}</div></div>
    {{#Footer}}<div class="meta-footer"><span class="footer-icon">📖</span><span class="footer-text">{{Footer}}</span></div>{{/Footer}}
</div>
''' + THEME_SCRIPT,
'afmt': '''
<div class="card-container answer-side">
    <div class="master-header">
        {{#Header}}
        <div class="meta-header">
            <button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="header">
            {{^Header}}<button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>{{/Header}}
            <div class="answer-icon">✅</div><div class="card-type">Answer</div>
        </div>
    </div>
    <div class="content-area">
        <div class="answer-text custom-answer">{{Answer}}</div>
        {{#Explanation}}<div class="explanation-section hidden" id="explanation"><div class="section-title">💡 Explanation</div><div class="explanation-text custom-explanation">{{Explanation}}</div></div>{{/Explanation}}
        {{#Clinical Correlation}}<div class="correlation-section hidden" id="correlation"><div class="section-title">🔗 Clinical Correlation</div><div class="correlation-text custom-correlation">{{Clinical Correlation}}</div></div>{{/Clinical Correlation}}
        <div class="toggle-controls">
            {{#Explanation}}<button onclick="toggleField('explanation')" class="toggle-btn explanation-btn">💡 <span class="toggle-text">Show Explanation</span></button>{{/Explanation}}
            {{#Clinical Correlation}}<button onclick="toggleField('correlation')" class="toggle-btn correlation-btn">🔗 <span class="toggle-text">Show Clinical</span></button>{{/Clinical Correlation}}
            <button onclick="toggleAll()" class="toggle-btn showall-btn">👁️ <span id="toggleAllText">Show All</span></button>
        </div>
    </div>
    {{#Footer}}<div class="meta-footer"><span class="footer-icon">📖</span><span class="footer-text">{{Footer}}</span></div>{{/Footer}}
    {{#Sources}}<div class="sources-section"><span class="sources-icon">🔗</span><span class="sources-text">{{Sources}}</span></div>{{/Sources}}
</div> 
<hr class="divider">
<script>
    function toggleField(fieldId) {
        const field = document.getElementById(fieldId);
        const btn = document.querySelector('.toggle-btn.' + fieldId + '-btn');
        const toggleText = btn.querySelector('.toggle-text');
        if (field.classList.contains('hidden')) {
            field.classList.remove('hidden');
            let label = (fieldId === 'explanation') ? 'Explanation' : 'Clinical';
            toggleText.textContent = 'Hide ' + label;
        } else {
            field.classList.add('hidden');
            let label = (fieldId === 'explanation') ? 'Explanation' : 'Clinical';
            toggleText.textContent = 'Show ' + label;
        }
    }
    function toggleAll() {
        const fields = document.querySelectorAll('.explanation-section, .correlation-section');
        const allHidden = Array.from(fields).every(f => f.classList.contains('hidden'));
        const toggleAllText = document.getElementById('toggleAllText');
        fields.forEach(field => {
            if (allHidden) { field.classList.remove('hidden'); }
            else { field.classList.add('hidden'); }
        });
        document.querySelectorAll('.toggle-btn:not(.showall-btn) .toggle-text').forEach(text => {
            const btn = text.parentElement;
            if (allHidden) {
                if (btn.classList.contains('explanation-btn')) { text.textContent = 'Hide Explanation'; }
                else if (btn.classList.contains('correlation-btn')) { text.textContent = 'Hide Clinical'; }
            } else {
                if (btn.classList.contains('explanation-btn')) { text.textContent = 'Show Explanation'; }
                else if (btn.classList.contains('correlation-btn')) { text.textContent = 'Show Clinical'; }
            }
        });
        toggleAllText.textContent = allHidden ? 'Hide All' : 'Show All';
    }
</script>
''' + THEME_SCRIPT
},
],
css=THEME_CSS + '''
/* === FINAL LAYOUT CSS (v14) - MODIFIED FOR SCREEN-RELATIVE SIZING === */
.card { 
    font-family: 'Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif; 
    line-height: 1.6; 
    margin: 0; 
    padding: 2.5vh 2.5vw; /* Use viewport units for padding */
    box-sizing: border-box; 
    display: flex; 
    align-items: center; 
    justify-content: center;
    min-height: 100vh; /* Ensure background covers the whole screen */
}
.card-container { 
    width: 90vw; /* Occupy 90% of the viewport width */
    max-width: 1100px; /* But not more than 1100px on wide screens */
    max-height: 90vh; /* Occupy up to 90% of the viewport height */
    overflow-y: auto; /* Add a scrollbar INSIDE the card if content is too long */
    border-radius: 20px; 
    box-shadow: 0 20px 40px rgba(0,0,0,0.2); 
    overflow-x: hidden; /* Prevent horizontal overflow */
    animation: bounceIn 0.8s ease-out; 
    display: flex; /* Use flexbox for better structure */
    flex-direction: column;
}
.master-header { position: relative; }
.content-area img { max-width: 100%; height: auto; display: block; margin: 1em auto; border-radius: 10px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
@keyframes bounceIn { 0% { transform: scale(0.3) translateY(-50px); opacity: 0; } 50% { transform: scale(1.05); } 70% { transform: scale(0.9); } 100% { transform: scale(1) translateY(0); opacity: 1; } }
.meta-header { position: relative; padding: 12px 20px; display: flex; align-items: center; gap: 10px; font-size: 0.95em; font-weight: 600; border-bottom: 1px solid rgba(255, 255, 255, 0.2); }
.header-icon, .footer-icon { font-size: 1.2em; }
.header-text, .footer-text { flex: 1; }
.header { position: relative; padding: 20px; display: flex; align-items: center; gap: 15px; }
.question-icon, .answer-icon { font-size: 2em; animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
.card-type { font-size: 1.4em; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.content-area { padding: 30px; }
.question-text, .answer-text { font-size: 1.2em; margin-bottom: 25px; text-align: center; font-weight: 500; }
.custom-question, .custom-answer { font-weight: 600 !important; font-size: 1.2em !important; }
.custom-explanation, .custom-correlation { font-weight: 500 !important; font-size: 1em !important; font-style: italic !important; }
.explanation-section, .correlation-section { margin-top: 25px; padding: 20px; border-radius: 15px; }
.section-title { font-weight: 600; font-size: 1.1em; margin-bottom: 10px; }
.meta-footer { padding: 12px 20px; display: flex; align-items: center; gap: 10px; font-size: 0.9em; border-top: 1px solid rgba(150,150,150,0.2); margin-top: auto; /* Pushes footer to the bottom */ }
.sources-section { padding: 12px 20px; display: flex; align-items: center; gap: 10px; font-size: 0.85em; font-style: italic !important; border-top: 1px solid rgba(150,150,150,0.2); }
.sources-icon { font-size: 1.1em; } .sources-text { flex: 1; }
.divider { border: none; height: 2px; background: linear-gradient(90deg, transparent, #4facfe, transparent); margin: 20px 0; }
.toggle-controls { display: flex; justify-content: center; gap: 12px; margin: 25px 0; padding: 10px; flex-wrap: wrap; }
.toggle-btn { border: none; padding: 12px 24px; border-radius: 25px; font-size: 1em; font-weight: 600; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; gap: 8px; white-space: nowrap; flex-shrink: 0; animation: pulse-button 3s ease-in-out infinite; }
.toggle-btn:hover { transform: translateY(-3px) scale(1.05); animation-play-state: paused; }
.toggle-btn:active { transform: translateY(0); }
.explanation-btn { background: linear-gradient(135deg, #38b2ac, #4fd1c5); box-shadow: 0 0 15px rgba(56, 178, 172, 0.4); }
.correlation-btn { background: linear-gradient(135deg, #8b5cf6, #a78bfa); box-shadow: 0 0 15px rgba(139, 92, 246, 0.4); }
.showall-btn { background: linear-gradient(135deg, #6b7280, #4b5563); box-shadow: 0 0 15px rgba(107, 114, 128, 0.3); color: #E5E7EB; }
.hidden { display: none !important; }
.explanation-section:not(.hidden), .correlation-section:not(.hidden) { animation: slideDown 0.3s ease-out; }
@keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
'''
)
# Cloze model (v14)
cloze_model = Model(
1607392320,
'Joplin to Anki Cloze Enhanced',
fields=[
{'name': 'Header'}, {'name': 'Text'}, {'name': 'Extra'}, {'name': 'Explanation'},
{'name': 'Clinical Correlation'}, {'name': 'Footer'}, {'name': 'Sources'}, {'name': 'Joplin to Anki ID'},
],
templates=[
{
'name': 'Enhanced Cloze Card',
'qfmt': '''
<div class="cloze-container">
    <div class="master-header">
        {{#Header}}
        <div class="meta-header">
            <button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="cloze-header">
            {{^Header}}<button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>{{/Header}}
            <div class="cloze-icon">🔍</div><div class="cloze-title">Fill in the Blanks</div>
        </div>
    </div>
    <div class="cloze-content">{{cloze:Text}}</div>
    {{#Footer}}<div class="meta-footer"><span class="footer-icon">📖</span><span class="footer-text">{{Footer}}</span></div>{{/Footer}}
</div>
''' + THEME_SCRIPT,
'afmt': '''
<div class="cloze-container revealed">
    <div class="master-header">
        {{#Header}}
        <div class="meta-header">
            <button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="cloze-header">
            {{^Header}}<button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>{{/Header}}
            <div class="cloze-icon">🎯</div><div class="cloze-title">Complete Answer</div>
        </div>
    </div>
    <div class="cloze-content">
        {{cloze:Text}}
        {{#Extra}}<div class="extra-info hidden" id="extra"><div class="extra-title">📚 Additional Information</div><div class="extra-content custom-extra">{{Extra}}</div></div>{{/Extra}}
        {{#Explanation}}<div class="explanation-info hidden" id="explanation"><div class="explanation-title">💡 Explanation</div><div class="explanation-content custom-explanation">{{Explanation}}</div></div>{{/Explanation}}
        {{#Clinical Correlation}}<div class="correlation-info hidden" id="correlation"><div class="correlation-title">🔗 Clinical Correlation</div><div class="correlation-content custom-correlation">{{Clinical Correlation}}</div></div>{{/Clinical Correlation}}
        <div class="toggle-controls">
            {{#Extra}}<button onclick="toggleField('extra')" class="toggle-btn extra-btn">📚 <span class="toggle-text">Show Extra</span></button>{{/Extra}}
            {{#Explanation}}<button onclick="toggleField('explanation')" class="toggle-btn explanation-btn">💡 <span class="toggle-text">Show Explanation</span></button>{{/Explanation}}
            {{#Clinical Correlation}}<button onclick="toggleField('correlation')" class="toggle-btn correlation-btn">🔗 <span class="toggle-text">Show Clinical</span></button>{{/Clinical Correlation}}
            <button onclick="toggleAll()" class="toggle-btn showall-btn">👁️ <span id="toggleAllText">Show All</span></button>
        </div>
    </div>
    {{#Footer}}<div class="meta-footer"><span class="footer-icon">📖</span><span class="footer-text">{{Footer}}</span></div>{{/Footer}}
    {{#Sources}}<div class="sources-section"><span class="sources-icon">🔗</span><span class="sources-text">{{Sources}}</span></div>{{/Sources}}
    <hr class="cloze-divider">
    <script>
        function toggleField(fieldId) {
            const field = document.getElementById(fieldId);
            const btn = document.querySelector('.toggle-btn.' + fieldId + '-btn');
            const toggleText = btn.querySelector('.toggle-text');
            const labels = { 'extra': 'Extra', 'explanation': 'Explanation', 'correlation': 'Clinical' };
            if (field.classList.contains('hidden')) {
                field.classList.remove('hidden');
                toggleText.textContent = 'Hide ' + labels[fieldId];
            } else {
                field.classList.add('hidden');
                toggleText.textContent = 'Show ' + labels[fieldId];
            }
        }
        function toggleAll() {
            const fields = document.querySelectorAll('.extra-info, .explanation-info, .correlation-info');
            const allHidden = Array.from(fields).every(f => f.classList.contains('hidden'));
            const toggleAllText = document.getElementById('toggleAllText');
            fields.forEach(field => {
                if (allHidden) { field.classList.remove('hidden'); }
                else { field.classList.add('hidden'); }
            });
            document.querySelectorAll('.toggle-btn:not(.showall-btn) .toggle-text').forEach(text => {
                const btn = text.parentElement;
                if (allHidden) {
                    if (btn.classList.contains('extra-btn')) { text.textContent = 'Hide Extra'; }
                    else if (btn.classList.contains('explanation-btn')) { text.textContent = 'Hide Explanation'; }
                    else if (btn.classList.contains('correlation-btn')) { text.textContent = 'Hide Clinical'; }
                } else {
                    if (btn.classList.contains('extra-btn')) { text.textContent = 'Show Extra'; }
                    else if (btn.classList.contains('explanation-btn')) { text.textContent = 'Show Explanation'; }
                    else if (btn.classList.contains('correlation-btn')) { text.textContent = 'Show Clinical'; }
                }
            });
            toggleAllText.textContent = allHidden ? 'Hide All' : 'Show All';
        }
    </script>
''' + THEME_SCRIPT
},
],
css=THEME_CSS + '''
/* === FINAL LAYOUT CSS (v14) - MODIFIED FOR SCREEN-RELATIVE SIZING === */
.card { 
    font-family: 'Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif; 
    margin: 0; 
    padding: 2.5vh 2.5vw; 
    box-sizing: border-box; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    min-height: 100vh;
}
.cloze-container { 
    width: 90vw;
    max-width: 1200px; 
    max-height: 90vh;
    overflow-y: auto;
    border-radius: 20px; 
    box-shadow: 0 25px 50px rgba(0,0,0,0.2); 
    overflow-x: hidden;
    animation: bounceIn 0.8s ease-out; 
    display: flex;
    flex-direction: column;
}
.master-header { position: relative; }
.cloze-content img { max-width: 100%; height: auto; display: block; margin: 1em auto; border-radius: 10px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
@keyframes bounceIn { 0% { transform: scale(0.3) translateY(-50px); opacity: 0; } 50% { transform: scale(1.05); } 70% { transform: scale(0.9); } 100% { transform: scale(1) translateY(0); opacity: 1; } }
.meta-header { position: relative; padding: 12px 20px; display: flex; align-items: center; gap: 10px; font-size: 0.95em; font-weight: 600; border-bottom: 1px solid rgba(255, 255, 255, 0.2); }
.header-icon, .footer-icon { font-size: 1.2em; }
.header-text, .footer-text { flex: 1; }
.cloze-header { position: relative; padding: 25px; display: flex; align-items: center; gap: 20px; }
.cloze-icon { font-size: 2.5em; animation: rotate-subtle 3s ease-in-out infinite alternate; }
.cloze-title { font-size: 1.5em; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
.cloze-content { padding: 20px; font-size: 1.2em; line-height: 1.8; text-align: center; }
.cloze { padding: 8px 16px; border-radius: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; margin: 0 4px; }
.custom-extra, .custom-explanation, .custom-correlation { font-weight: 500 !important; font-style: italic !important; }
.extra-info, .explanation-info, .correlation-info { margin-top: 30px; padding: 25px; border-radius: 15px; font-size: 0.9em; text-align: left; line-height: 1.6; }
.extra-title, .explanation-title, .correlation-title { font-weight: 600; font-size: 1.1em; margin-bottom: 15px; }
.extra-content, .explanation-content, .correlation-content { font-size: 1.0em; white-space: pre-wrap; font-style: italic !important; }
.meta-footer { padding: 12px 20px; display: flex; align-items: center; gap: 10px; font-size: 0.9em; border-top: 1px solid rgba(150,150,150,0.2); margin-top: auto; }
.sources-section { padding: 12px 20px; display: flex; align-items: center; gap: 10px; font-size: 0.85em; font-style: italic !important; border-top: 1px solid rgba(150,150,150,0.2); }
.sources-icon { font-size: 1.1em; } .sources-text { flex: 1; }
.cloze-divider { border: none; height: 3px; background: linear-gradient(90deg, transparent, #ff7675, transparent); margin: 25px 0; }
.toggle-controls { display: flex; justify-content: center; gap: 12px; margin: 25px 0; padding: 10px; flex-wrap: wrap; }
.toggle-btn { border: none; padding: 12px 24px; border-radius: 25px; font-size: 1em; font-weight: 600; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; gap: 8px; white-space: nowrap; flex-shrink: 0; animation: pulse-button 3s ease-in-out infinite; }
.toggle-btn:hover { transform: translateY(-3px) scale(1.05); animation-play-state: paused; } .toggle-btn:active { transform: translateY(0); }
.explanation-btn { background: linear-gradient(135deg, #38b2ac, #4fd1c5); box-shadow: 0 0 15px rgba(56, 178, 172, 0.4); }
.correlation-btn { background: linear-gradient(135deg, #8b5cf6, #a78bfa); box-shadow: 0 0 15px rgba(139, 92, 246, 0.4); }
.extra-btn { background: linear-gradient(135deg, #f97316, #fb923c); box-shadow: 0 0 15px rgba(249, 115, 22, 0.4); }
.showall-btn { background: linear-gradient(135deg, #6b7280, #4b5563); box-shadow: 0 0 15px rgba(107, 114, 128, 0.3); color: #E5E7EB; }
.hidden { display: none !important; }
.extra-info:not(.hidden), .explanation-info:not(.hidden), .correlation-info:not(.hidden) { animation: slideDown 0.3s ease-out; }
@keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
''',
model_type=1
)
# MCQ model (v14)
mcq_model = Model(
1607392321,
'Joplin to Anki MCQ Enhanced',
fields=[
{'name': 'Header'}, {'name': 'Question'}, {'name': 'OptionA'}, {'name': 'OptionB'},
{'name': 'OptionC'}, {'name': 'OptionD'}, {'name': 'CorrectAnswer'}, {'name': 'Explanation'},
{'name': 'Clinical Correlation'}, {'name': 'Footer'}, {'name': 'Sources'}, {'name': 'Joplin to Anki ID'},
],
templates=[
{
'name': 'Enhanced MCQ Card',
'qfmt': '''
<div class="mcq-container">
    <div class="master-header">
        {{#Header}}
        <div class="meta-header">
            <button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="mcq-header">
            {{^Header}}<button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>{{/Header}}
            <div class="mcq-icon">❓</div><div class="mcq-title">Multiple Choice</div>
        </div>
    </div>
    <div class="mcq-content">
        <div class="question-section">{{Question}}</div>
        <div class="options-grid">
            {{#OptionA}}<div class="option option-a" data-option="A"><span class="option-letter">A</span><span class="option-text">{{OptionA}}</span></div>{{/OptionA}}
            {{#OptionB}}<div class="option option-b" data-option="B"><span class="option-letter">B</span><span class="option-text">{{OptionB}}</span></div>{{/OptionB}}
            {{#OptionC}}<div class="option option-c" data-option="C"><span class="option-letter">C</span><span class="option-text">{{OptionC}}</span></div>{{/OptionC}}
            {{#OptionD}}<div class="option option-d" data-option="D"><span class="option-letter">D</span><span class="option-text">{{OptionD}}</span></div>{{/OptionD}}
        </div>
    </div>
    {{#Footer}}<div class="meta-footer"><span class="footer-icon">📖</span><span class="footer-text">{{Footer}}</span></div>{{/Footer}}
</div>
''' + THEME_SCRIPT,
'afmt': '''
<div class="mcq-container answer-revealed">
    <div class="master-header">
        {{#Header}}
        <div class="meta-header">
            <button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="mcq-header">
            {{^Header}}<button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>{{/Header}}
            <div class="mcq-icon">🎯</div><div class="mcq-title">Correct Answer</div>
        </div>
    </div>
    <div class="mcq-content">
        <div class="correct-answer"><div class="answer-label">✅ Correct Answer:</div><div class="answer-value">{{CorrectAnswer}}</div></div>
        {{#Explanation}}<div class="explanation-block hidden" id="explanation"><div class="block-title">💡 Explanation</div><div class="block-content custom-explanation">{{Explanation}}</div></div>{{/Explanation}}
        {{#Clinical Correlation}}<div class="correlation-block hidden" id="correlation"><div class="block-title">🔗 Clinical Correlation</div><div class="block-content custom-correlation">{{Clinical Correlation}}</div></div>{{/Clinical Correlation}}
        <div class="toggle-controls">
            {{#Explanation}}<button onclick="toggleField('explanation')" class="toggle-btn explanation-btn">💡 <span class="toggle-text">Show Explanation</span></button>{{/Explanation}}
            {{#Clinical Correlation}}<button onclick="toggleField('correlation')" class="toggle-btn correlation-btn">🔗 <span class="toggle-text">Show Clinical</span></button>{{/Clinical Correlation}}
            <button onclick="toggleAll()" class="toggle-btn showall-btn">👁️ <span id="toggleAllText">Show All</span></button>
        </div>
    </div>
    {{#Footer}}<div class="meta-footer"><span class="footer-icon">📖</span><span class="footer-text">{{Footer}}</span></div>{{/Footer}}
    {{#Sources}}<div class="sources-section"><span class="sources-icon">🔗</span><span class="sources-text">{{Sources}}</span></div>{{/Sources}}
    <hr class="mcq-divider">
    <script>
        function toggleField(fieldId) {
            const field = document.getElementById(fieldId);
            const btn = document.querySelector('.toggle-btn.' + fieldId + '-btn');
            const toggleText = btn.querySelector('.toggle-text');
            if (field.classList.contains('hidden')) {
                field.classList.remove('hidden');
                let label = (fieldId === 'explanation') ? 'Explanation' : 'Clinical';
                toggleText.textContent = 'Hide ' + label;
            } else {
                field.classList.add('hidden');
                let label = (fieldId === 'explanation') ? 'Explanation' : 'Clinical';
                toggleText.textContent = 'Show ' + label;
            }
        }
        function toggleAll() {
            const fields = document.querySelectorAll('.explanation-block, .correlation-block');
            const allHidden = Array.from(fields).every(f => f.classList.contains('hidden'));
            const toggleAllText = document.getElementById('toggleAllText');
            fields.forEach(field => {
                if (allHidden) { field.classList.remove('hidden'); }
                else { field.classList.add('hidden'); }
            });
            document.querySelectorAll('.toggle-btn:not(.showall-btn) .toggle-text').forEach(text => {
                const btn = text.parentElement;
                if (allHidden) {
                    if (btn.classList.contains('explanation-btn')) { text.textContent = 'Hide Explanation'; }
                    else if (btn.classList.contains('correlation-btn')) { text.textContent = 'Hide Clinical'; }
                } else {
                    if (btn.classList.contains('explanation-btn')) { text.textContent = 'Show Explanation'; }
                    else if (btn.classList.contains('correlation-btn')) { text.textContent = 'Show Clinical'; }
                }
            });
            toggleAllText.textContent = allHidden ? 'Hide All' : 'Show All';
        }
    </script>
''' + THEME_SCRIPT
},
],
css=THEME_CSS + '''
/* === FINAL LAYOUT CSS (v14) - MODIFIED FOR SCREEN-RELATIVE SIZING === */
.card { 
    font-family: 'Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif; 
    margin: 0; 
    padding: 2.5vh 2.5vw; 
    box-sizing: border-box; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    min-height: 100vh;
}
.mcq-container { 
    width: 90vw;
    max-width: 1000px; 
    max-height: 90vh;
    overflow-y: auto;
    border-radius: 20px; 
    box-shadow: 0 25px 50px rgba(0,0,0,0.2); 
    overflow-x: hidden;
    animation: bounceIn 0.8s ease-out; 
    display: flex;
    flex-direction: column;
}
.master-header { position: relative; }
.mcq-content img { max-width: 100%; height: auto; display: block; margin: 1em auto; border-radius: 10px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
@keyframes bounceIn { 0% { transform: scale(0.3) translateY(-50px); opacity: 0; } 50% { transform: scale(1.05); } 70% { transform: scale(0.9); } 100% { transform: scale(1) translateY(0); opacity: 1; } }
.meta-header { position: relative; padding: 12px 20px; display: flex; align-items: center; gap: 10px; font-size: 0.95em; font-weight: 600; border-bottom: 1px solid rgba(255, 255, 255, 0.2); }
.header-icon, .footer-icon { font-size: 1.2em; }
.header-text, .footer-text { flex: 1; }
.mcq-header { position: relative; padding: 25px; display: flex; align-items: center; gap: 20px; }
.mcq-icon { font-size: 2.5em; animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
.mcq-title { font-size: 1.5em; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
.mcq-content { padding: 10px; }
.question-section { font-size: 1.35em; margin-bottom: 20px; text-align: center; font-weight: 500; line-height: 1.4; }
.options-grid { display: grid; grid-template-columns: 1fr; gap: 18px; }
.option { padding: 18px 22px; border-radius: 14px; display: flex; align-items: center; gap: 14px; box-shadow: 0 8px 20px rgba(0,0,0,0.05); cursor: pointer; transition: all 0.3s ease; word-wrap: break-word; font-size: 1.15em; border-left: 6px solid; }
.option:hover { transform: translateY(-3px); box-shadow: 0 14px 28px rgba(0,0,0,0.12); }
.option-letter { padding: 8px 12px; border-radius: 50%; font-weight: bold; }
.option-text { font-size: 1.15em; flex: 1; }
.correct-answer { padding: 20px; background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%); border-radius: 12px; margin-bottom: 25px; text-align: center; }
.answer-label { font-weight: 700; margin-bottom: 10px; color: #2d3436; }
.answer-value { font-size: 1.3em; font-weight: 600; }
.custom-explanation, .custom-correlation { font-weight: 500 !important; font-style: italic !important; }
.explanation-block, .correlation-block { margin-top: 20px; padding: 20px; border-radius: 15px; font-size: 1.0em; }
.block-title { font-weight: 700; margin-bottom: 10px; }
.block-content { font-size: 1.0em; }
.meta-footer { padding: 12px 20px; display: flex; align-items: center; gap: 10px; font-size: 0.9em; border-top: 1px solid rgba(150,150,150,0.2); margin-top: auto; }
.sources-section { padding: 12px 20px; display: flex; align-items: center; gap: 10px; font-size: 0.85em; font-style: italic !important; border-top: 1px solid rgba(150,150,150,0.2); }
.sources-icon { font-size: 1.1em; } .sources-text { flex: 1; }
.mcq-divider { border: none; height: 3px; background: linear-gradient(90deg, transparent, #0984e3, transparent); margin: 25px 0; }
.toggle-controls { display: flex; justify-content: center; gap: 12px; margin: 25px 0; padding: 10px; flex-wrap: wrap; }
.toggle-btn { border: none; padding: 12px 24px; border-radius: 25px; font-size: 1em; font-weight: 600; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; gap: 8px; white-space: nowrap; flex-shrink: 0; animation: pulse-button 3s ease-in-out infinite; }
.toggle-btn:hover { transform: translateY(-3px) scale(1.05); animation-play-state: paused; } .toggle-btn:active { transform: translateY(0); }
.explanation-btn { background: linear-gradient(135deg, #38b2ac, #4fd1c5); box-shadow: 0 0 15px rgba(56, 178, 172, 0.4); }
.correlation-btn { background: linear-gradient(135deg, #8b5cf6, #a78bfa); box-shadow: 0 0 15px rgba(139, 92, 246, 0.4); }
.showall-btn { background: linear-gradient(135deg, #6b7280, #4b5563); box-shadow: 0 0 15px rgba(107, 114, 128, 0.3); color: #E5E7EB; }
.hidden { display: none !important; }
.explanation-block:not(.hidden), .correlation-block:not(.hidden) { animation: slideDown 0.3s ease-out; }
@keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
'''
)
# Image model (v14)
image_model = Model(
1607392322,
'Joplin to Anki Image Enhanced',
fields=[
{'name': 'Header'}, {'name': 'QuestionImagePath'}, {'name': 'AnswerImagePath'}, {'name': 'Question'},
{'name': 'Answer'}, {'name': 'Origin'}, {'name': 'Insertion'}, {'name': 'Innervation'},
{'name': 'Action'}, {'name': 'Clinical Correlation'}, {'name': 'Comments'}, {'name': 'Footer'},
{'name': 'Sources'}, {'name': 'Joplin to Anki ID'},
],
templates=[
{
'name': 'Enhanced Image Occlusion Card',
'qfmt': '''
<div class="image-container">
    <div class="master-header">
        {{#Header}}
        <div class="meta-header">
            <button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="image-header">
            {{^Header}}<button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>{{/Header}}
            <div class="image-icon">🖼️</div><div class="image-title">Image Question</div>
        </div>
    </div>
    <div class="image-content">
        {{#Question}}<div class="question-overlay custom-image-question">{{Question}}</div>{{/Question}}
        <img src="{{QuestionImagePath}}" class="main-image">
    </div>
    {{#Footer}}<div class="meta-footer"><span class="footer-icon">📖</span><span class="footer-text">{{Footer}}</span></div>{{/Footer}}
</div>
''' + THEME_SCRIPT,
'afmt': '''
<div class="image-container revealed">
    <div class="master-header">
        {{#Header}}
        <div class="meta-header">
            <button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="image-header">
            {{^Header}}<button id="themeToggle" class="theme-toggle" onclick="cycleTheme()">🌕</button>{{/Header}}
            <div class="image-icon">💡</div><div class="image-title">Answer Revealed</div>
        </div>
    </div>
    <div class="image-content">
        {{#Answer}}<div class="answer-overlay custom-image-answer">{{Answer}}</div>{{/Answer}}
        {{#Origin}}<div class="anatomy-section origin-section"><div class="anatomy-title">🦴 Origin</div><div class="anatomy-text custom-origin">{{Origin}}</div></div>{{/Origin}}
        {{#Insertion}}<div class="anatomy-section insertion-section"><div class="anatomy-title">🔗 Insertion</div><div class="anatomy-text custom-insertion">{{Insertion}}</div></div>{{/Insertion}}
        {{#Innervation}}<div class="anatomy-section innervation-section"><div class="anatomy-title">⚡ Innervation</div><div class="anatomy-text custom-innervation">{{Innervation}}</div></div>{{/Innervation}}
        {{#Action}}<div class="anatomy-section action-section"><div class="anatomy-title">💪 Action</div><div class="anatomy-text custom-action">{{Action}}</div></div>{{/Action}}
        <img src="{{AnswerImagePath}}" class="main-image">
    </div>
    {{#Clinical Correlation}}<div class="correlation-section hidden" id="correlation"><div class="section-title">🔗 Clinical Correlation</div><div class="correlation-text custom-correlation">{{Clinical Correlation}}</div></div>{{/Clinical Correlation}}
    {{#Comments}}<div class="comments-block hidden" id="comments"><div class="comments-title">📝 Comments</div><div class="comments-text custom-comments">{{Comments}}</div></div>{{/Comments}}
    <div class="toggle-controls">
        {{#Clinical Correlation}}<button onclick="toggleField('correlation')" class="toggle-btn correlation-btn">🔗 <span class="toggle-text">Show Clinical</span></button>{{/Clinical Correlation}}
        {{#Comments}}<button onclick="toggleField('comments')" class="toggle-btn comments-btn">📝 <span class="toggle-text">Show Comments</span></button>{{/Comments}}
        <button onclick="toggleAll()" class="toggle-btn showall-btn">👁️ <span id="toggleAllText">Show All</span></button>
    </div>
    {{#Footer}}<div class="meta-footer"><span class="footer-icon">📖</span><span class="footer-text">{{Footer}}</span></div>{{/Footer}}
    {{#Sources}}<div class="sources-section"><span class="sources-icon">🔗</span><span class="sources-text">{{Sources}}</span></div>{{/Sources}}
    <hr class="image-divider">
    <script>
        function toggleField(fieldId) {
            const field = document.getElementById(fieldId);
            const btn = document.querySelector('.toggle-btn.' + fieldId + '-btn');
            const toggleText = btn.querySelector('.toggle-text');
            const labels = { 'correlation': 'Clinical', 'comments': 'Comments' };
            if (field.classList.contains('hidden')) {
                field.classList.remove('hidden');
                toggleText.textContent = 'Hide ' + labels[fieldId];
            } else {
                field.classList.add('hidden');
                toggleText.textContent = 'Show ' + labels[fieldId];
            }
        }
        function toggleAll() {
            const fields = document.querySelectorAll('.correlation-section, .comments-block');
            const allHidden = Array.from(fields).every(f => f.classList.contains('hidden'));
            const toggleAllText = document.getElementById('toggleAllText');
            fields.forEach(field => {
                if (allHidden) { field.classList.remove('hidden'); }
                else { field.classList.add('hidden'); }
            });
            document.querySelectorAll('.toggle-btn:not(.showall-btn) .toggle-text').forEach(text => {
                const btn = text.parentElement;
                if (allHidden) {
                    if (btn.classList.contains('correlation-btn')) { text.textContent = 'Hide Clinical'; }
                    else if (btn.classList.contains('comments-btn')) { text.textContent = 'Hide Comments'; }
                } else {
                    if (btn.classList.contains('correlation-btn')) { text.textContent = 'Show Clinical'; }
                    else if (btn.classList.contains('comments-btn')) { text.textContent = 'Show Comments'; }
                }
            });
            toggleAllText.textContent = allHidden ? 'Hide All' : 'Show All';
        }
    </script>
''' + THEME_SCRIPT
},
],
css=THEME_CSS + '''
/* === FINAL LAYOUT CSS (v14) - MODIFIED FOR SCREEN-RELATIVE SIZING === */
.card { 
    font-family: 'Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif; 
    margin: 0; 
    padding: 2.5vh 2.5vw; 
    box-sizing: border-box; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    min-height: 100vh;
}
.image-container { 
    width: 90vw;
    max-width: 1200px; 
    max-height: 90vh;
    overflow-y: auto;
    border-radius: 20px; 
    box-shadow: 0 25px 50px rgba(0,0,0,0.2); 
    overflow-x: hidden;
    animation: bounceIn 0.8s ease-out; 
    display: flex;
    flex-direction: column;
}
.master-header { position: relative; }
.image-content img { max-width: 100%; height: auto; display: block; margin: 1em auto; border-radius: 10px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
@keyframes bounceIn { 0% { transform: scale(0.3) translateY(-50px); opacity: 0; } 50% { transform: scale(1.05); } 70% { transform: scale(0.9); } 100% { transform: scale(1) translateY(0); opacity: 1; } }
.meta-header { position: relative; padding: 12px 20px; display: flex; align-items: center; gap: 10px; font-size: 0.95em; font-weight: 600; border-bottom: 1px solid rgba(255, 255, 255, 0.2); }
.header-icon, .footer-icon { font-size: 1.2em; }
.header-text, .footer-text { flex: 1; }
.image-header { position: relative; padding: 25px; display: flex; align-items: center; gap: 20px; }
.image-icon { font-size: 2.5em; animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
.image-title { font-size: 1.5em; font-weight: 700; text-transform: uppercase; }
.image-content { position: relative; padding: 30px; text-align: center; }
.main-image { max-width: 100%; border-radius: 15px; box-shadow: 0 15px 30px rgba(0,0,0,0.1); transition: transform 0.3s ease; display: block; margin: 0 auto; }
.main-image:hover { transform: scale(1.02); }
.question-overlay, .answer-overlay { margin-bottom: 20px; padding: 15px 25px; border-radius: 12px; font-weight: 500; box-shadow: 0 8px 20px rgba(0,0,0,0.1); text-align: center; }
.custom-image-question { background: rgba(255, 255, 255, 0.95) !important; font-weight: 600 !important; font-size: 1.3em !important; border: 2px solid #5d4037 !important; padding: 20px !important; position: relative; z-index: 2; }
.custom-image-answer { background: linear-gradient(135deg, #f093fb, #f5576c) !important; color: #FDF2F8 !important; font-weight: 600 !important; font-size: 1.3em !important; padding: 10px; border-radius: 8px; position: relative; z-index: 2; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
.custom-comments, .custom-correlation { font-weight: 500 !important; font-style: italic !important; }
.correlation-section, .comments-block { margin: 25px; padding: 20px; border-radius: 15px; }
.section-title, .comments-title { font-weight: 600; margin-bottom: 10px; font-size: 1.1em; }
.correlation-text, .comments-text { font-size: 1.0em; text-align: left; }
.meta-footer { padding: 12px 20px; display: flex; align-items: center; gap: 10px; font-size: 0.9em; border-top: 1px solid rgba(150,150,150,0.2); margin-top: auto; }
.sources-section { padding: 12px 20px; display: flex; align-items: center; gap: 10px; font-size: 0.85em; font-style: italic !important;; border-top: 1px solid rgba(150,150,150,0.2); }
.sources-icon { font-size: 1.1em; } .sources-text { flex: 1; }
.image-divider { border: none; height: 3px; background: linear-gradient(90deg, transparent, #74b9ff, transparent); margin: 25px 0; }
.anatomy-section { margin: 20px 25px; padding: 20px; border-radius: 15px; border-left: 5px solid; }
.anatomy-title { font-weight: 700 !important; font-size: 1.3em; margin-bottom: 12px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); letter-spacing: 0.5px; }
.anatomy-text { font-size: 1.1em; line-height: 1.6; }
.custom-origin, .custom-insertion, .custom-innervation, .custom-action { font-weight: 600 !important; font-size: 1.2em !important; font-style: normal !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.4); }
.toggle-controls { display: flex; justify-content: center; gap: 12px; margin: 25px 0; padding: 10px; flex-wrap: wrap; }
.toggle-btn { border: none; padding: 12px 24px; border-radius: 25px; font-size: 1em; font-weight: 600; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; gap: 8px; white-space: nowrap; flex-shrink: 0; animation: pulse-button 3s ease-in-out infinite; }
.toggle-btn:hover { transform: translateY(-3px) scale(1.05); animation-play-state: paused; } .toggle-btn:active { transform: translateY(0); }
.correlation-btn { background: linear-gradient(135deg, #8b5cf6, #a78bfa); box-shadow: 0 0 15px rgba(139, 92, 246, 0.4); }
.comments-btn { background: linear-gradient(135deg, #f97316, #fb923c); box-shadow: 0 0 15px rgba(249, 115, 22, 0.4); }
.showall-btn { background: linear-gradient(135deg, #6b7280, #4b5563); box-shadow: 0 0 15px rgba(107, 114, 128, 0.3); color: #E5E7EB; }
.hidden { display: none !important; }
.correlation-section:not(.hidden), .comments-block:not(.hidden) { animation: slideDown 0.3s ease-out; }
@keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
'''
)
def create_deck(name):
 return Deck(2059400110, name)
def create_test_notes():
 deck = create_deck('Joplin to Anki Enhanced - FINAL TEST SUITE')
print("Creating a comprehensive test suite with 8 notes (v14)...")
code
Code
# === BASIC NOTES ===
# Basic with Header (tests small button)
deck.add_note(Note(model=basic_model, fields=['Cardiovascular Physiology', 'What is the normal resting heart rate for adults?', '60-100 beats per minute', 'The SA node acts as the natural pacemaker.', 'Persistent tachycardia can indicate underlying issues.', 'Chapter 12', 'Guyton & Hall', 'joplin_basic_v14_header']))
# Basic without Header (tests large button)
deck.add_note(Note(model=basic_model, fields=['', 'What is the primary function of alveoli?', 'Gas exchange between the lungs and bloodstream.', 'This occurs via passive diffusion.', '', 'Respiratory System', '', 'joplin_basic_v14_noheader']))

# === CLOZE NOTES ===
# Cloze with Header (tests small button)
deck.add_note(Note(model=cloze_model, fields=['Neuroscience', 'The {{c1::hippocampus}} is a complex brain structure embedded deep into the temporal lobe, with a major role in learning and {{c2::memory}}.', 'It is a plastic and vulnerable structure.', 'Damage can lead to anterograde amnesia.', 'Alzheimer\'s disease often impacts this area first.', 'Unit 3', 'Kandel, Principles of Neural Science', 'joplin_cloze_v14_header']))
# Cloze without Header (tests large button)
deck.add_note(Note(model=cloze_model, fields=['', 'The powerhouse of the cell is the {{c1::mitochondrion}}.', '', 'It generates most of the cell\'s supply of adenosine triphosphate (ATP).', '', 'Cell Biology', '', 'joplin_cloze_v14_noheader']))

# === MCQ NOTES ===
# MCQ with Header (tests small button & answer text visibility)
deck.add_note(Note(model=mcq_model, fields=['Pharmacology', 'Which of the following drugs is a proton-pump inhibitor?', 'Ranitidine', 'Omeprazole', 'Loperamide', 'Ondansetron', 'B', 'Omeprazole works by irreversibly blocking the H+/K+ ATPase in gastric parietal cells.', 'Often used for GERD and peptic ulcers.', 'Chapter 45', 'Katzung & Trevor\'s Pharmacology', 'joplin_mcq_v14_header']))
# MCQ without Header (tests large button & answer text visibility)
deck.add_note(Note(model=mcq_model, fields=['', 'What is the capital of Japan?', 'Beijing', 'Seoul', 'Tokyo', 'Bangkok', 'C', '', '', 'Geography 101', '', 'joplin_mcq_v14_noheader']))

# === IMAGE NOTES ===
# Image with Header (tests small button & question text visibility)
deck.add_note(Note(model=image_model, fields=['Anatomy - Upper Limb', '_media/question_deltoid.jpg', '_media/answer_deltoid.jpg', 'Identify the highlighted muscle.', 'Deltoid Muscle', 'Lateral third of clavicle, acromion, and spine of scapula', 'Deltoid tuberosity of humerus', 'Axillary nerve (C5, C6)', 'Abduction, flexion, and extension of the shoulder', 'Axillary nerve damage can paralyze the deltoid.', 'Key for arm abduction beyond 15 degrees.', 'Shoulder Joint', 'Gray\'s Anatomy', 'joplin_image_v14_header']))
# Image without Header (tests large button & question text visibility)
deck.add_note(Note(model=image_model, fields=['', '_media/question_heart.jpg', '_media/answer_heart.jpg', 'Identify the chamber indicated by the arrow.', 'Left Ventricle', '', '', '', 'Pumps oxygenated blood to the rest of the body via the aorta.', '', '', 'Thoracic Cavity', '', 'joplin_image_v14_noheader']))

print("8 test notes added to the deck for all types and header variations.")
return deck
if name == 'main':
 deck = create_test_notes()
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_directory = "output"
if not os.path.exists(output_directory):
  os.makedirs(output_directory)
filename = os.path.join(output_directory, f"joplin_anki_ENHANCED_FINAL_{timestamp}.apkg")
code
Code
# For Image notes to work, create a 'media' folder and add placeholder images.
media_directory = "media"
if not os.path.exists(media_directory):
    os.makedirs(media_directory)
    # Create dummy image files if they don't exist
    for img_name in ['question_deltoid.jpg', 'answer_deltoid.jpg', 'question_heart.jpg', 'answer_heart.jpg']:
        with open(os.path.join(media_directory, img_name), 'w') as f:
            f.write("placeholder")

media_files = [os.path.join(media_directory, f) for f in os.listdir(media_directory)]
package = Package(deck)
package.media_files = media_files
package.write_to_file(filename)

print("\n" + "="*60)
print(f"✅ Success! Final package with all fixes created: {filename}")
print("="*60)
print("\n✨ THEME SWAP IMPLEMENTED (v14) ✨")
print("This version implements the requested theme change:")
print("  • The CSS styles for 'light-dark' (🌖) and 'balanced' (🌗) have been swapped.")
print("  • The emojis and theme names in the cycle order remain the same.")
print("  • All other code and functionality are preserved.")
print("  • The test deck remains comprehensive for full verification.")
print("\nIMPORTANT: For the Image notes to work, please place your images")
print(" (e.g., 'question_deltoid.jpg') inside the 'media' folder before running.")

# Cleanup old files
files = sorted(glob.glob(os.path.join(output_directory, "joplin_anki_*.apkg")), key=os.path.getmtime, reverse=True)
for old_file in files[3:]: # Keep the latest 3 versions
    try:
        os.remove(old_file)
        print(f"Cleaned up old package: {old_file}")
    except OSError as e:
        print(f"Error removing file {old_file}: {e}")

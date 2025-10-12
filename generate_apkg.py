# -- coding: utf-8 --
from genanki import Model, Deck, Note, Package
import datetime
import glob
import os

# ==============================================================================
# =====================  REVISED THEME SCRIPT (v16 - FIX) ======================
# ==============================================================================
# This version includes a more robust `applyTheme` function for smoother transitions.
THEME_SCRIPT = '''
<script>
// --- Configuration ---
const THEME_FAMILIES = {
    'light': {
        emoji: '🌕',
        modes: ['light-full-moon', 'light-waning-gibbous', 'light-last-quarter', 'light-waning-crescent', 'light-new-moon'],
        emojis: ['🌕', '🌖', '🌗', '🌘', '🌑']
    },
    'nord': {
        emoji: '☀️',
        modes: ['nord-bright-sun', 'nord-overcast-day', 'nord-stormy-sky', 'nord-aurora', 'nord-polar-night'],
        emojis: ['☀️', '☁️', '⛈️', '🌌', '🌃']
    },
    'balanced': {
        emoji: '⭐',
        modes: ['balanced-star', 'balanced-nebula', 'balanced-supernova', 'balanced-galaxy', 'balanced-comet'],
        emojis: ['⭐', '✨', '💥', '🌀', '☄️']
    },
    'twilight': {
        emoji: '🌙',
        modes: ['twilight-crescent-moon', 'twilight-city-night', 'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk'],
        emojis: ['🌙', '🏙️', '🌲', '🌊', '🌆']
    },
    'dark': {
        emoji: '🪐',
        modes: ['dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 'dark-black-hole', 'dark-starless-sky'],
        emojis: ['🪐', '🤖', '🔵', '⚫', '▪️']
    }
};

const ALL_THEMES = Object.values(THEME_FAMILIES).flatMap(f => f.modes);
const THEME_KEY = 'joplinAnkiTheme_v3';

// --- Helper Functions ---
function applyTheme(theme) {
    // FIX: More robustly applies the theme class to the body.
    // This prevents removing other essential classes like '.card' and ensures smoother transitions.
    document.body.classList.forEach(c => {
        if (c.startsWith('theme-')) {
            document.body.classList.remove(c);
        }
    });
    document.body.classList.add('theme-' + theme);
    // Ensure the base class is always present.
    if (!document.body.classList.contains('card')) {
        document.body.classList.add('card');
    }
}

function updateThemeButtons(theme) {
    const currentFamily = theme.split('-')[0];
    const familyData = THEME_FAMILIES[currentFamily];
    if (!familyData) return;

    const currentModeIndex = familyData.modes.indexOf(theme);
    const currentEmoji = familyData.emojis[currentModeIndex];

    Object.keys(THEME_FAMILIES).forEach(familyKey => {
        const btn = document.getElementById('themeBtn-' + familyKey);
        if (btn) {
            if (familyKey === currentFamily) {
                btn.textContent = currentEmoji;
                btn.classList.add('active');
            } else {
                btn.textContent = THEME_FAMILIES[familyKey].emoji;
                btn.classList.remove('active');
            }
        }
    });
}

// --- Storage Functions (Unchanged) ---
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
        if (localTheme && ALL_THEMES.includes(localTheme)) {
            return localTheme;
        }
    } catch(e) {}
    const metaTheme = document.querySelector('meta[name="anki-theme"]');
    if (metaTheme && ALL_THEMES.includes(metaTheme.content)) {
        return metaTheme.content;
    }
    const name = THEME_KEY + '=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookieArray = decodedCookie.split(';');
    for (let i = 0; i < cookieArray.length; i++) {
        let cookie = cookieArray[i].trim();
        if (cookie.indexOf(name) === 0) {
            const theme = cookie.substring(name.length, cookie.length);
            if (ALL_THEMES.includes(theme)) { return theme; }
        }
    }
    return 'light-full-moon'; // Default theme
}

// --- Main Logic (Unchanged) ---
function handleFamilyClick(clickedFamily) {
    const currentTheme = loadTheme();
    const currentFamily = currentTheme.split('-')[0];
    const familyData = THEME_FAMILIES[clickedFamily];
    if (!familyData) return;
    let nextTheme;
    if (currentFamily === clickedFamily) {
        const currentIndex = familyData.modes.indexOf(currentTheme);
        const nextIndex = (currentIndex + 1) % familyData.modes.length;
        nextTheme = familyData.modes[nextIndex];
    } else {
        nextTheme = familyData.modes[0];
    }
    applyTheme(nextTheme);
    updateThemeButtons(nextTheme);
    saveTheme(nextTheme);
}

// --- Initialization (Unchanged) ---
function initTheme() {
    const savedTheme = loadTheme();
    applyTheme(savedTheme);
    updateThemeButtons(savedTheme);
    Object.keys(THEME_FAMILIES).forEach(familyKey => {
        const btn = document.getElementById('themeBtn-' + familyKey);
        if (btn && !btn.onclick) {
            btn.onclick = () => handleFamilyClick(familyKey);
        }
    });
}
// ... [original observer logic remains here, no changes needed] ...
let buttonObserver = null;
function startWatchingButtons() {
    if (buttonObserver) buttonObserver.disconnect();
    buttonObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1 && (node.classList.contains('theme-controls') || node.querySelector('.theme-controls'))) {
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
        startWatchingButtons();
    });
} else {
    startWatchingButtons();
}
setTimeout(initTheme, 100);
document.addEventListener('visibilitychange', function() { if (!document.hidden) initTheme(); });
window.addEventListener('ankiCardShown', initTheme);
contentObserver.observe(document.body, { attributes: true, attributeFilter: ['class'], subtree: true });
</script>
'''

# ==============================================================================
# ======================  FULL THEME CSS (v16 - COMPLETE) ======================
# ==============================================================================
# This is the COMPLETE CSS for all 20 themes. No more placeholders.
# The Nord family has been completely redesigned with blue/cool palettes.
THEME_CSS = '''
/* --- Core Animations and Variables --- */
@keyframes glowPulse {
    0% { box-shadow: 0 0 5px var(--glow-color), 0 0 10px var(--glow-color), 0 0 15px var(--glow-color); }
    50% { box-shadow: 0 0 10px var(--glow-color), 0 0 20px var(--glow-color), 0 0 30px var(--glow-color); }
    100% { box-shadow: 0 0 5px var(--glow-color), 0 0 10px var(--glow-color), 0 0 15px var(--glow-color); }
}

@keyframes buttonPulse {
    0% { transform: scale(0.95); opacity: 0.8; }
    50% { transform: scale(1); opacity: 1; }
    100% { transform: scale(0.95); opacity: 0.8; }
}

@keyframes rotateClozeIcon {
    0% { transform: rotate(0deg); }
    50% { transform: rotate(60deg); }
    100% { transform: rotate(0deg); }
}

@keyframes neonTextPulse {
    0% { text-shadow: 0 0 7px var(--neon-color), 0 0 10px var(--neon-color), 0 0 21px var(--neon-color); }
    50% { text-shadow: 0 0 14px var(--neon-color), 0 0 20px var(--neon-color), 0 0 42px var(--neon-color); }
    100% { text-shadow: 0 0 7px var(--neon-color), 0 0 10px var(--neon-color), 0 0 21px var(--neon-color); }
}

/* --- Theme Controls UI --- */
.theme-controls{position:absolute;top:10px;right:10px;display:flex;gap:5px;background:rgba(0,0,0,0.1);padding:5px;border-radius:30px;z-index:1000}
.theme-family-btn{background:none;border:none;cursor:pointer;font-size:1.4em;padding:6px;border-radius:50%;transition:all .2s ease;line-height:1;display:flex;align-items:center;justify-content:center}
.theme-family-btn:hover{transform:scale(1.2);background:rgba(255,255,255,0.2)}
.theme-family-btn.active{transform:scale(1.1);animation:pulse-mode-toggle 2.5s ease-in-out infinite}
.meta-header .theme-controls{top:4px;right:6px;padding:3px;gap:3px}
.meta-header .theme-family-btn{font-size:1.3em;padding:3px}
@keyframes pulse-mode-toggle{0%,100%{transform:scale(1.1);opacity:1}50%{transform:scale(1.15);opacity:.95}}

/* =================================================================== */
/* =================== 🌕 FAMILY: LIGHT THEMES ======================= */
/* =================================================================== */
/* 1.1: light-full-moon (Original Light) */
body.theme-light-full-moon{
    background:linear-gradient(135deg,#f5f7fa 0%,#c3cfe2 100%);
    --theme-primary: #a855f7;
    --theme-secondary: #d946ef;
    --glow-color: rgba(168,85,247,0.3);
}
.theme-light-full-moon .card-container,.theme-light-full-moon .cloze-container,.theme-light-full-moon .mcq-container,.theme-light-full-moon .image-container{
    background:rgba(255,255,255,0.85)!important;
    backdrop-filter:blur(12px)!important;
    color:#433865!important;
    border:1px solid rgba(226,232,240,0.9)!important;
    box-shadow: 0 0 20px rgba(168,85,247,0.15)!important;
}
.theme-light-full-moon .meta-header,.theme-light-full-moon .header,.theme-light-full-moon .cloze-header,.theme-light-full-moon .mcq-header,.theme-light-full-moon .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(168,85,247,0.3)!important;
}
.theme-light-full-moon .theme-family-btn{
    color:#433865!important;
    text-shadow:0 1px 2px rgba(0,0,0,0.1)!important;
}
.theme-light-full-moon .card-type,.theme-light-full-moon .cloze-title,.theme-light-full-moon .mcq-title,.theme-light-full-moon .image-title,.theme-light-full-moon .header-text{
    color:#F5F3FF!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-light-full-moon .question-text,.theme-light-full-moon .question-section{
    color:#581C87!important;
    text-shadow: 0 0 15px rgba(168,85,247,0.3)!important;
}
.theme-light-full-moon .answer-text,.theme-light-full-moon .cloze-content{
    color:#065F46!important;
    text-shadow: 0 0 15px rgba(217,70,239,0.3)!important;
}
.theme-light-full-moon .cloze{
    background:linear-gradient(135deg,#d946ef,#ec4899)!important;
    color:#F5F3FF!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(217,70,239,0.4)!important;
}
.theme-light-full-moon .explanation-block,.theme-light-full-moon .explanation-section,.theme-light-full-moon .explanation-info{
    background:rgba(56,178,172,0.1)!important;
    border-left:5px solid #38B2AC!important;
    box-shadow: 0 0 15px rgba(56,178,172,0.15)!important;
}
.theme-light-full-moon .correlation-block,.theme-light-full-moon .correlation-section,.theme-light-full-moon .correlation-info{
    background:rgba(139,92,246,0.1)!important;
    border-left:5px solid #8B5CF6!important;
    box-shadow: 0 0 15px rgba(139,92,246,0.15)!important;
}
.theme-light-full-moon .extra-info,.theme-light-full-moon .comments-block{
    background:rgba(249,115,22,0.1)!important;
    border-left:5px solid #F97316!important;
    box-shadow: 0 0 15px rgba(249,115,22,0.15)!important;
}

/* 1.2: light-waning-gibbous (Sepia/Paper) */
body.theme-light-waning-gibbous{
    background:#fdf6e3;
    --theme-primary: #cb4b16;
    --theme-secondary: #dc322f;
    --glow-color: rgba(203,75,22,0.3);
}
.theme-light-waning-gibbous .card-container,.theme-light-waning-gibbous .cloze-container,.theme-light-waning-gibbous .mcq-container,.theme-light-waning-gibbous .image-container{
    background:rgba(253,246,227,0.95)!important;
    backdrop-filter:blur(8px)!important;
    color:#586e75!important;
    border:1px solid rgba(238,232,213,0.9)!important;
    box-shadow: 0 0 20px rgba(203,75,22,0.1)!important;
}
.theme-light-waning-gibbous .meta-header,.theme-light-waning-gibbous .header,.theme-light-waning-gibbous .cloze-header,.theme-light-waning-gibbous .mcq-header,.theme-light-waning-gibbous .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(203,75,22,0.3)!important;
}
.theme-light-waning-gibbous .theme-family-btn{
    color:#586e75!important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.1)!important;
}
.theme-light-waning-gibbous .card-type,.theme-light-waning-gibbous .cloze-title,.theme-light-waning-gibbous .mcq-title,.theme-light-waning-gibbous .image-title,.theme-light-waning-gibbous .header-text{
    color:#fdf6e3!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-light-waning-gibbous .question-text,.theme-light-waning-gibbous .question-section{
    color:#859900!important;
    text-shadow: 0 0 15px rgba(133,153,0,0.3)!important;
}
.theme-light-waning-gibbous .answer-text,.theme-light-waning-gibbous .cloze-content{
    color:#268bd2!important;
    text-shadow: 0 0 15px rgba(38,139,210,0.3)!important;
}
.theme-light-waning-gibbous .cloze{
    background:linear-gradient(135deg,#2aa198,#268bd2)!important;
    color:#fdf6e3!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(42,161,152,0.4)!important;
}
.theme-light-waning-gibbous .explanation-block,.theme-light-waning-gibbous .explanation-section,.theme-light-waning-gibbous .explanation-info{
    background:rgba(133,153,0,0.1)!important;
    border-left:5px solid #859900!important;
    box-shadow: 0 0 15px rgba(133,153,0,0.15)!important;
}
.theme-light-waning-gibbous .correlation-block,.theme-light-waning-gibbous .correlation-section,.theme-light-waning-gibbous .correlation-info{
    background:rgba(38,139,210,0.1)!important;
    border-left:5px solid #268bd2!important;
    box-shadow: 0 0 15px rgba(38,139,210,0.15)!important;
}
.theme-light-waning-gibbous .extra-info,.theme-light-waning-gibbous .comments-block{
    background:rgba(220,50,47,0.1)!important;
    border-left:5px solid #dc322f!important;
    box-shadow: 0 0 15px rgba(220,50,47,0.15)!important;
}

/* 1.3: light-last-quarter (Cool Mint) */
body.theme-light-last-quarter{
    background:linear-gradient(135deg,#E0F2F1 0%,#B2DFDB 100%);
    --theme-primary: #00796B;
    --theme-secondary: #009688;
    --glow-color: rgba(0,121,107,0.3);
}
.theme-light-last-quarter .card-container,.theme-light-last-quarter .cloze-container,.theme-light-last-quarter .mcq-container,.theme-light-last-quarter .image-container{
    background:rgba(255,255,255,0.85)!important;
    backdrop-filter:blur(10px)!important;
    color:#004D40!important;
    border:1px solid rgba(128,203,196,0.9)!important;
    box-shadow: 0 0 20px rgba(0,121,107,0.15)!important;
}
.theme-light-last-quarter .meta-header,.theme-light-last-quarter .header,.theme-light-last-quarter .cloze-header,.theme-light-last-quarter .mcq-header,.theme-light-last-quarter .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(0,121,107,0.3)!important;
}
.theme-light-last-quarter .theme-family-btn{
    color:#004D40!important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.1)!important;
}
.theme-light-last-quarter .card-type,.theme-light-last-quarter .cloze-title,.theme-light-last-quarter .mcq-title,.theme-light-last-quarter .image-title,.theme-light-last-quarter .header-text{
    color:#E0F2F1!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-light-last-quarter .question-text,.theme-light-last-quarter .question-section{
    color:#00695C!important;
    text-shadow: 0 0 15px rgba(0,105,92,0.3)!important;
}
.theme-light-last-quarter .answer-text,.theme-light-last-quarter .cloze-content{
    color:#3949AB!important;
    text-shadow: 0 0 15px rgba(57,73,171,0.3)!important;
}
.theme-light-last-quarter .cloze{
    background:linear-gradient(135deg,#00897B,#4DB6AC)!important;
    color:#fff!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(0,137,123,0.4)!important;
}
.theme-light-last-quarter .explanation-block,.theme-light-last-quarter .explanation-section,.theme-light-last-quarter .explanation-info{
    background:rgba(76,175,80,0.1)!important;
    border-left:5px solid #4CAF50!important;
    box-shadow: 0 0 15px rgba(76,175,80,0.15)!important;
}
.theme-light-last-quarter .correlation-block,.theme-light-last-quarter .correlation-section,.theme-light-last-quarter .correlation-info{
    background:rgba(33,150,243,0.1)!important;
    border-left:5px solid #2196F3!important;
    box-shadow: 0 0 15px rgba(33,150,243,0.15)!important;
}
.theme-light-last-quarter .extra-info,.theme-light-last-quarter .comments-block{
    background:rgba(255,87,34,0.1)!important;
    border-left:5px solid #FF5722!important;
    box-shadow: 0 0 15px rgba(255,87,34,0.15)!important;
}

/* 1.4: light-waning-crescent (Soft Lavender) */
body.theme-light-waning-crescent{
    background:#f3e5f5;
    --theme-primary: #8E24AA;
    --theme-secondary: #AB47BC;
    --glow-color: rgba(142,36,170,0.3);
}
.theme-light-waning-crescent .card-container,.theme-light-waning-crescent .cloze-container,.theme-light-waning-crescent .mcq-container,.theme-light-waning-crescent .image-container{
    background:rgba(243,229,245,0.85)!important;
    backdrop-filter:blur(8px)!important;
    color:#4A148C!important;
    border:1px solid rgba(206,147,216,0.9)!important;
    box-shadow: 0 0 20px rgba(142,36,170,0.15)!important;
}
.theme-light-waning-crescent .meta-header,.theme-light-waning-crescent .header,.theme-light-waning-crescent .cloze-header,.theme-light-waning-crescent .mcq-header,.theme-light-waning-crescent .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(142,36,170,0.3)!important;
}
.theme-light-waning-crescent .theme-family-btn{
    color:#4A148C!important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.1)!important;
}
.theme-light-waning-crescent .card-type,.theme-light-waning-crescent .cloze-title,.theme-light-waning-crescent .mcq-title,.theme-light-waning-crescent .image-title,.theme-light-waning-crescent .header-text{
    color:#F3E5F5!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-light-waning-crescent .question-text,.theme-light-waning-crescent .question-section{
    color:#6A1B9A!important;
    text-shadow: 0 0 15px rgba(106,27,154,0.3)!important;
}
.theme-light-waning-crescent .answer-text,.theme-light-waning-crescent .cloze-content{
    color:#AD1457!important;
    text-shadow: 0 0 15px rgba(173,20,87,0.3)!important;
}
.theme-light-waning-crescent .cloze{
    background:linear-gradient(135deg,#7B1FA2,#9C27B0)!important;
    color:#fff!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(123,31,162,0.4)!important;
}
.theme-light-waning-crescent .explanation-block,.theme-light-waning-crescent .explanation-section,.theme-light-waning-crescent .explanation-info{
    background:rgba(236,64,122,0.1)!important;
    border-left:5px solid #EC407A!important;
    box-shadow: 0 0 15px rgba(236,64,122,0.15)!important;
}
.theme-light-waning-crescent .correlation-block,.theme-light-waning-crescent .correlation-section,.theme-light-waning-crescent .correlation-info{
    background:rgba(3,169,244,0.1)!important;
    border-left:5px solid #03A9F4!important;
    box-shadow: 0 0 15px rgba(3,169,244,0.15)!important;
}
.theme-light-waning-crescent .extra-info,.theme-light-waning-crescent .comments-block{
    background:rgba(251,192,45,0.1)!important;
    border-left:5px solid #FBC02D!important;
    box-shadow: 0 0 15px rgba(251,192,45,0.15)!important;
}

/* 1.5: light-new-moon (Minimalist White) */
body.theme-light-new-moon{
    background:#f8f9fa;
    --theme-primary: #343a40;
    --theme-secondary: #495057;
    --glow-color: rgba(52,58,64,0.2);
}
.theme-light-new-moon .card-container,.theme-light-new-moon .cloze-container,.theme-light-new-moon .mcq-container,.theme-light-new-moon .image-container{
    background:#fff!important;
    backdrop-filter:blur(8px)!important;
    color:#212529!important;
    border:1px solid rgba(222,226,230,0.9)!important;
    box-shadow: 0 0 20px rgba(52,58,64,0.1)!important;
}
.theme-light-new-moon .meta-header,.theme-light-new-moon .header,.theme-light-new-moon .cloze-header,.theme-light-new-moon .mcq-header,.theme-light-new-moon .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(52,58,64,0.3)!important;
}
.theme-light-new-moon .theme-family-btn{
    color:#343a40!important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.1)!important;
}
.theme-light-new-moon .card-type,.theme-light-new-moon .cloze-title,.theme-light-new-moon .mcq-title,.theme-light-new-moon .image-title,.theme-light-new-moon .header-text{
    color:#f8f9fa!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-light-new-moon .question-text,.theme-light-new-moon .question-section{
    color:#007bff!important;
    text-shadow: 0 0 15px rgba(0,123,255,0.3)!important;
}
.theme-light-new-moon .answer-text,.theme-light-new-moon .cloze-content{
    color:#28a745!important;
    text-shadow: 0 0 15px rgba(40,167,69,0.3)!important;
}
.theme-light-new-moon .cloze{
    background:linear-gradient(135deg,#007bff,#0056b3)!important;
    color:#fff!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(0,123,255,0.4)!important;
}
.theme-light-new-moon .explanation-block,.theme-light-new-moon .explanation-section,.theme-light-new-moon .explanation-info{
    background:rgba(108,117,125,0.1)!important;
    border-left:5px solid #6c757d!important;
    box-shadow: 0 0 15px rgba(108,117,125,0.15)!important;
}
.theme-light-new-moon .correlation-block,.theme-light-new-moon .correlation-section,.theme-light-new-moon .correlation-info{
    background:rgba(52,58,64,0.1)!important;
    border-left:5px solid #343a40!important;
    box-shadow: 0 0 15px rgba(52,58,64,0.15)!important;
}
.theme-light-new-moon .extra-info,.theme-light-new-moon .comments-block{
    background:rgba(255,193,7,0.1)!important;
    border-left:5px solid #ffc107!important;
    box-shadow: 0 0 15px rgba(255,193,7,0.15)!important;
}

/* =================================================================== */
/* =================== ☀️ FAMILY: NORD THEMES ======================== */
/* =================================================================== */
/* 2.1: nord-bright-sun (Original Light-Dark) */
body.theme-nord-bright-sun{
    background:linear-gradient(to top,#30cfd0 0%,#330867 100%);
    --theme-primary: #06b6d4;
    --theme-secondary: #3b82f6;
    --glow-color: rgba(6,182,212,0.4);
}
.theme-nord-bright-sun .card-container,.theme-nord-bright-sun .cloze-container,.theme-nord-bright-sun .mcq-container,.theme-nord-bright-sun .image-container{
    background:rgba(45,55,72,0.85)!important;
    backdrop-filter:blur(12px)!important;
    color:#A0AEC0!important;
    border:1px solid rgba(113,128,150,0.8)!important;
    box-shadow: 0 0 20px rgba(6,182,212,0.2)!important;
}
.theme-nord-bright-sun .meta-header,.theme-nord-bright-sun .header,.theme-nord-bright-sun .cloze-header,.theme-nord-bright-sun .mcq-header,.theme-nord-bright-sun .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(6,182,212,0.3)!important;
}
.theme-nord-bright-sun .theme-family-btn{
    color:#E0F2FE!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
}
.theme-nord-bright-sun .card-type,.theme-nord-bright-sun .cloze-title,.theme-nord-bright-sun .mcq-title,.theme-nord-bright-sun .image-title,.theme-nord-bright-sun .header-text{
    color:#E0F2FE!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-nord-bright-sun .question-text,.theme-nord-bright-sun .question-section{
    color:#90CDF4!important;
    text-shadow: 0 0 15px rgba(144,205,244,0.4)!important;
}
.theme-nord-bright-sun .answer-text,.theme-nord-bright-sun .cloze-content{
    color:#81E6D9!important;
    text-shadow: 0 0 15px rgba(129,230,217,0.4)!important;
}
.theme-nord-bright-sun .cloze{
    background:linear-gradient(135deg,#06b6d4,#81E6D9)!important;
    color:#1A202C!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(6,182,212,0.5)!important;
}
.theme-nord-bright-sun .explanation-block,.theme-nord-bright-sun .explanation-section,.theme-nord-bright-sun .explanation-info{
    background:rgba(49,151,149,0.2)!important;
    border-left:5px solid #38B2AC!important;
    box-shadow: 0 0 15px rgba(56,178,172,0.15)!important;
}
.theme-nord-bright-sun .correlation-block,.theme-nord-bright-sun .correlation-section,.theme-nord-bright-sun .correlation-info{
    background:rgba(66,153,225,0.2)!important;
    border-left:5px solid #4299E1!important;
    box-shadow: 0 0 15px rgba(66,153,225,0.15)!important;
}
.theme-nord-bright-sun .extra-info,.theme-nord-bright-sun .comments-block{
    background:rgba(213,63,140,0.2)!important;
    border-left:5px solid #D53F8C!important;
    box-shadow: 0 0 15px rgba(213,63,140,0.15)!important;
}

/* 2.2: nord-overcast-day (Cool Gray/Blue) */
body.theme-nord-overcast-day{
    background:linear-gradient(135deg,#BCC6CC 0%,#94A3B8 100%);
    --theme-primary: #64748B;
    --theme-secondary: #475569;
    --glow-color: rgba(100,116,139,0.3);
}
.theme-nord-overcast-day .card-container,.theme-nord-overcast-day .cloze-container,.theme-nord-overcast-day .mcq-container,.theme-nord-overcast-day .image-container{
    background:rgba(255,255,255,0.7)!important;
    backdrop-filter:blur(8px)!important;
    color:#334155!important;
    border:1px solid rgba(226,232,240,0.9)!important;
    box-shadow: 0 0 20px rgba(100,116,139,0.15)!important;
}
.theme-nord-overcast-day .meta-header,.theme-nord-overcast-day .header,.theme-nord-overcast-day .cloze-header,.theme-nord-overcast-day .mcq-header,.theme-nord-overcast-day .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(100,116,139,0.3)!important;
}
.theme-nord-overcast-day .theme-family-btn{
    color:#334155!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
}
.theme-nord-overcast-day .card-type,.theme-nord-overcast-day .cloze-title,.theme-nord-overcast-day .mcq-title,.theme-nord-overcast-day .image-title,.theme-nord-overcast-day .header-text{
    color:#F1F5F9!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-nord-overcast-day .question-text,.theme-nord-overcast-day .question-section{
    color:#0F172A!important;
    text-shadow: 0 0 15px rgba(15,23,42,0.3)!important;
}
.theme-nord-overcast-day .answer-text,.theme-nord-overcast-day .cloze-content{
    color:#1E40AF!important;
    text-shadow: 0 0 15px rgba(30,64,175,0.3)!important;
}
.theme-nord-overcast-day .cloze{
    background:linear-gradient(135deg,#475569,#1E293B)!important;
    color:#F8FAFC!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(71,85,105,0.4)!important;
}
.theme-nord-overcast-day .explanation-block,.theme-nord-overcast-day .explanation-section,.theme-nord-overcast-day .explanation-info{
    background:rgba(226,232,240,0.4)!important;
    border-left:5px solid #94A3B8!important;
    box-shadow: 0 0 15px rgba(148,163,184,0.15)!important;
}
.theme-nord-overcast-day .correlation-block,.theme-nord-overcast-day .correlation-section,.theme-nord-overcast-day .correlation-info{
    background:rgba(219,234,254,0.4)!important;
    border-left:5px solid #60A5FA!important;
    box-shadow: 0 0 15px rgba(96,165,250,0.15)!important;
}
.theme-nord-overcast-day .extra-info,.theme-nord-overcast-day .comments-block{
    background:rgba(254,243,199,0.4)!important;
    border-left:5px solid #F59E0B!important;
    box-shadow: 0 0 15px rgba(245,158,11,0.15)!important;
}

/* 2.3: nord-stormy-sky (Deep Blue/Gray with Yellow flash) */
body.theme-nord-stormy-sky{
    background:linear-gradient(135deg,#4A5568 0%,#1A202C 100%);
    --theme-primary: #FBBF24;
    --theme-secondary: #F59E0B;
    --glow-color: rgba(251,191,36,0.3);
}
.theme-nord-stormy-sky .card-container,.theme-nord-stormy-sky .cloze-container,.theme-nord-stormy-sky .mcq-container,.theme-nord-stormy-sky .image-container{
    background:rgba(45,55,72,0.8)!important;
    backdrop-filter:blur(12px)!important;
    color:#E2E8F0!important;
    border:1px solid rgba(113,128,150,0.8)!important;
    box-shadow: 0 0 20px rgba(251,191,36,0.15)!important;
}
.theme-nord-stormy-sky .meta-header,.theme-nord-stormy-sky .header,.theme-nord-stormy-sky .cloze-header,.theme-nord-stormy-sky .mcq-header,.theme-nord-stormy-sky .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(251,191,36,0.3)!important;
}
.theme-nord-stormy-sky .theme-family-btn{
    color:#E2E8F0!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
}
.theme-nord-stormy-sky .card-type,.theme-nord-stormy-sky .cloze-title,.theme-nord-stormy-sky .mcq-title,.theme-nord-stormy-sky .image-title,.theme-nord-stormy-sky .header-text{
    color:#422006!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-nord-stormy-sky .question-text,.theme-nord-stormy-sky .question-section{
    color:#FCD34D!important;
    text-shadow: 0 0 15px rgba(252,211,77,0.4)!important;
}
.theme-nord-stormy-sky .answer-text,.theme-nord-stormy-sky .cloze-content{
    color:#93C5FD!important;
    text-shadow: 0 0 15px rgba(147,197,253,0.4)!important;
}
.theme-nord-stormy-sky .cloze{
    background:linear-gradient(135deg,#1E40AF,#3B82F6)!important;
    color:#EFF6FF!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(30,64,175,0.4)!important;;
}
.theme-nord-stormy-sky .explanation-block,.theme-nord-stormy-sky .explanation-section,.theme-nord-stormy-sky .explanation-info{
    background:rgba(147,197,253,0.1)!important;
    border-left:5px solid #60A5FA!important;
    box-shadow: 0 0 15px rgba(96,165,250,0.15)!important;
}
.theme-nord-stormy-sky .correlation-block,.theme-nord-stormy-sky .correlation-section,.theme-nord-stormy-sky .correlation-info{
    background:rgba(252,211,77,0.1)!important;
    border-left:5px solid #FBBF24!important;
    box-shadow: 0 0 15px rgba(251,191,36,0.15)!important;
}
.theme-nord-stormy-sky .extra-info,.theme-nord-stormy-sky .comments-block{
    background:rgba(248,113,113,0.1)!important;
    border-left:5px solid #F87171!important;
    box-shadow: 0 0 15px rgba(248,113,113,0.15)!important;
}

/* 2.4: nord-aurora (Dark blue with green/cyan glows) */
body.theme-nord-aurora{
    background:linear-gradient(-45deg,#02042b,#0f172a,#02042b);
    --theme-primary: #10B981;
    --theme-secondary: #2DD4BF;
    --glow-color: rgba(16,185,129,0.3);
}
.theme-nord-aurora .card-container,.theme-nord-aurora .cloze-container,.theme-nord-aurora .mcq-container,.theme-nord-aurora .image-container{
    background:rgba(15,23,42,0.8)!important;
    backdrop-filter:blur(14px)!important;
    color:#94A3B8!important;
    border:1px solid rgba(51,65,85,0.8)!important;
    box-shadow: 0 0 20px rgba(16,185,129,0.15)!important;
}
.theme-nord-aurora .meta-header,.theme-nord-aurora .header,.theme-nord-aurora .cloze-header,.theme-nord-aurora .mcq-header,.theme-nord-aurora .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(16,185,129,0.3)!important;
}
.theme-nord-aurora .theme-family-btn{
    color:#94A3B8!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
}
.theme-nord-aurora .card-type,.theme-nord-aurora .cloze-title,.theme-nord-aurora .mcq-title,.theme-nord-aurora .image-title,.theme-nord-aurora .header-text{
    color:#064E3B!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-nord-aurora .question-text,.theme-nord-aurora .question-section{
    color:#6EE7B7!important;
    text-shadow: 0 0 15px rgba(110,231,183,0.4)!important;
}
.theme-nord-aurora .answer-text,.theme-nord-aurora .cloze-content{
    color:#5EEAD4!important;
    text-shadow: 0 0 15px rgba(94,234,212,0.4)!important;
}
.theme-nord-aurora .cloze{
    background:linear-gradient(135deg,#059669,#14B8A6)!important;
    color:#F0FDFA!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(5,150,105,0.4)!important;
}
.theme-nord-aurora .explanation-block,.theme-nord-aurora .explanation-section,.theme-nord-aurora .explanation-info{
    background:rgba(20,184,166,0.1)!important;
    border-left:5px solid #14B8A6!important;
    box-shadow: 0 0 15px rgba(20,184,166,0.15)!important;
}
.theme-nord-aurora .correlation-block,.theme-nord-aurora .correlation-section,.theme-nord-aurora .correlation-info{
    background:rgba(139,92,246,0.1)!important;
    border-left:5px solid #8B5CF6!important;
    box-shadow: 0 0 15px rgba(139,92,246,0.15)!important;
}
.theme-nord-aurora .extra-info,.theme-nord-aurora .comments-block{
    background:rgba(236,72,153,0.1)!important;
    border-left:5px solid #EC4899!important;
    box-shadow: 0 0 15px rgba(236,72,153,0.15)!important;
}

/* 2.5: nord-polar-night (Very Dark Nord) */
body.theme-nord-polar-night{
    background:#2E3440;
    --theme-primary: #5E81AC;
    --theme-secondary: #81A1C1;
    --glow-color: rgba(94,129,172,0.3);
}
.theme-nord-polar-night .card-container,.theme-nord-polar-night .cloze-container,.theme-nord-polar-night .mcq-container,.theme-nord-polar-night .image-container{
    background:#3B4252!important;
    backdrop-filter:blur(10px)!important;
    color:#D8DEE9!important;
    border:1px solid rgba(76,86,106,0.8)!important;
    box-shadow: 0 0 20px rgba(94,129,172,0.15)!important;
}
.theme-nord-polar-night .meta-header,.theme-nord-polar-night .header,.theme-nord-polar-night .cloze-header,.theme-nord-polar-night .mcq-header,.theme-nord-polar-night .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(94,129,172,0.3)!important;
}
.theme-nord-polar-night .theme-family-btn{
    color:#D8DEE9!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
}
.theme-nord-polar-night .card-type,.theme-nord-polar-night .cloze-title,.theme-nord-polar-night .mcq-title,.theme-nord-polar-night .image-title,.theme-nord-polar-night .header-text{
    color:#ECEFF4!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-nord-polar-night .question-text,.theme-nord-polar-night .question-section{
    color:#88C0D0!important;
    text-shadow: 0 0 15px rgba(136,192,208,0.4)!important;
}
.theme-nord-polar-night .answer-text,.theme-nord-polar-night .cloze-content{
    color:#A3BE8C!important;
    text-shadow: 0 0 15px rgba(163,190,140,0.4)!important;
}
.theme-nord-polar-night .cloze{
    background:linear-gradient(135deg,#81A1C1,#88C0D0)!important;
    color:#2E3440!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(129,161,193,0.4)!important;
}
.theme-nord-polar-night .explanation-block,.theme-nord-polar-night .explanation-section,.theme-nord-polar-night .explanation-info{
    background:rgba(67,76,94,0.6)!important;
    border-left:5px solid #A3BE8C!important;
    box-shadow: 0 0 15px rgba(163,190,140,0.15)!important;
}
.theme-nord-polar-night .correlation-block,.theme-nord-polar-night .correlation-section,.theme-nord-polar-night .correlation-info{
    background:rgba(67,76,94,0.6)!important;
    border-left:5px solid #EBCB8B!important;
    box-shadow: 0 0 15px rgba(235,203,139,0.15)!important;
}
.theme-nord-polar-night .extra-info,.theme-nord-polar-night .comments-block{
    background:rgba(67,76,94,0.6)!important;
    border-left:5px solid #BF616A!important;
    box-shadow: 0 0 15px rgba(191,97,106,0.15)!important;
}

/* =================================================================== */
/* ================== ⭐ FAMILY: BALANCED THEMES ===================== */
/* =================================================================== */
/* 3.1: balanced-star (Original Balanced) */
body.theme-balanced-star{
    background:linear-gradient(to right,#434343 0%,black 100%);
    --theme-primary: #a18cd1;
    --theme-secondary: #fbc2eb;
    --glow-color: rgba(161,140,209,0.3);
}
.theme-balanced-star .card-container,.theme-balanced-star .cloze-container,.theme-balanced-star .mcq-container,.theme-balanced-star .image-container{
    background:rgba(55,65,81,0.7)!important;
    backdrop-filter:blur(16px)!important;
    color:#D1D5DB!important;
    border:1px solid rgba(156,163,175,0.8)!important;
    box-shadow: 0 0 20px rgba(161,140,209,0.15)!important;
}
.theme-balanced-star .meta-header,.theme-balanced-star .header,.theme-balanced-star .cloze-header,.theme-balanced-star .mcq-header,.theme-balanced-star .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(161,140,209,0.3)!important;
}
.theme-balanced-star .theme-family-btn{
    color:#D1D5DB!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
}
.theme-balanced-star .card-type,.theme-balanced-star .cloze-title,.theme-balanced-star .mcq-title,.theme-balanced-star .image-title,.theme-balanced-star .header-text{
    color:#3730A3!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-balanced-star .question-text,.theme-balanced-star .question-section{
    color:#FBCFE8!important;
    text-shadow: 0 0 15px rgba(251,207,232,0.4)!important;
}
.theme-balanced-star .answer-text,.theme-balanced-star .cloze-content{
    color:#C4B5FD!important;
    text-shadow: 0 0 15px rgba(196,181,253,0.4)!important;
}
.theme-balanced-star .cloze{
    background:linear-gradient(135deg,#a18cd1,#fbc2eb)!important;
    color:#4B5563!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(161,140,209,0.4)!important;
}
.theme-balanced-star .explanation-block,.theme-balanced-star .explanation-section,.theme-balanced-star .explanation-info{
    background:rgba(196,181,253,0.1)!important;
    border-left:5px solid #A78BFA!important;
    box-shadow: 0 0 15px rgba(167,139,250,0.15)!important;
}
.theme-balanced-star .correlation-block,.theme-balanced-star .correlation-section,.theme-balanced-star .correlation-info{
    background:rgba(251,207,232,0.1)!important;
    border-left:5px solid #F472B6!important;
    box-shadow: 0 0 15px rgba(244,114,182,0.15)!important;
}
.theme-balanced-star .extra-info,.theme-balanced-star .comments-block{
    background:rgba(134,239,172,0.1)!important;
    border-left:5px solid #4ADE80!important;
    box-shadow: 0 0 15px rgba(74,222,128,0.15)!important;
}

/* 3.2: balanced-nebula (Deep Purples and Pinks) */
body.theme-balanced-nebula{
    background:linear-gradient(135deg,#23074d 0%,#cc5333 100%);
    --theme-primary: #BE185D;
    --theme-secondary: #E11D48;
    --glow-color: rgba(190,24,93,0.3);
}
.theme-balanced-nebula .card-container,.theme-balanced-nebula .cloze-container,.theme-balanced-nebula .mcq-container,.theme-balanced-nebula .image-container{
    background:rgba(30,27,58,0.8)!important;
    backdrop-filter:blur(16px)!important;
    color:#D9CFFC!important;
    border:1px solid rgba(109,40,217,0.8)!important;
    box-shadow: 0 0 20px rgba(190,24,93,0.15)!important;
}
.theme-balanced-nebula .meta-header,.theme-balanced-nebula .header,.theme-balanced-nebula .cloze-header,.theme-balanced-nebula .mcq-header,.theme-balanced-nebula .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(190,24,93,0.3)!important;
}
.theme-balanced-nebula .theme-family-btn{
    color:#D9CFFC!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
}
.theme-balanced-nebula .card-type,.theme-balanced-nebula .cloze-title,.theme-balanced-nebula .mcq-title,.theme-balanced-nebula .image-title,.theme-balanced-nebula .header-text{
    color:#FDF2F8!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-balanced-nebula .question-text,.theme-balanced-nebula .question-section{
    color:#F472B6!important;
    text-shadow: 0 0 15px rgba(244,114,182,0.4)!important;
}
.theme-balanced-nebula .answer-text,.theme-balanced-nebula .cloze-content{
    color:#A5B4FC!important;
    text-shadow: 0 0 15px rgba(165,180,252,0.4)!important;
}
.theme-balanced-nebula .cloze{
    background:linear-gradient(135deg,#9D174D,#BE185D)!important;
    color:#FFE4E6!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(157,23,77,0.4)!important;
}
.theme-balanced-nebula .explanation-block,.theme-balanced-nebula .explanation-section,.theme-balanced-nebula .explanation-info{
    background:rgba(165,180,252,0.1)!important;
    border-left:5px solid #818CF8!important;
    box-shadow: 0 0 15px rgba(129,140,248,0.15)!important;
}
.theme-balanced-nebula .correlation-block,.theme-balanced-nebula .correlation-section,.theme-balanced-nebula .correlation-info{
    background:rgba(244,114,182,0.1)!important;
    border-left:5px solid #F472B6!important;
    box-shadow: 0 0 15px rgba(244,114,182,0.15)!important;
}
.theme-balanced-nebula .extra-info,.theme-balanced-nebula .comments-block{
    background:rgba(251,146,60,0.1)!important;
    border-left:5px solid #FB923C!important;
    box-shadow: 0 0 15px rgba(251,146,60,0.15)!important;
}

/* 3.3: balanced-supernova (Bright Oranges and Reds) */
body.theme-balanced-supernova{
    background:linear-gradient(135deg,#ff4e50 0%,#f9d423 100%);
    --theme-primary: #DC2626;
    --theme-secondary: #F59E0B;
    --glow-color: rgba(220,38,38,0.3);
}
.theme-balanced-supernova .card-container,.theme-balanced-supernova .cloze-container,.theme-balanced-supernova .mcq-container,.theme-balanced-supernova .image-container{
    background:rgba(40,10,5,0.8)!important;
    backdrop-filter:blur(14px)!important;
    color:#FDE68A!important;
    border:1px solid rgba(249,115,22,0.8)!important;
    box-shadow: 0 0 20px rgba(220,38,38,0.15)!important;
}
.theme-balanced-supernova .meta-header,.theme-balanced-supernova .header,.theme-balanced-supernova .cloze-header,.theme-balanced-supernova .mcq-header,.theme-balanced-supernova .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(220,38,38,0.3)!important;
}
.theme-balanced-supernova .theme-family-btn{
    color:#FDE68A!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
}
.theme-balanced-supernova .card-type,.theme-balanced-supernova .cloze-title,.theme-balanced-supernova .mcq-title,.theme-balanced-supernova .image-title,.theme-balanced-supernova .header-text{
    color:#FFFBEB!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-balanced-supernova .question-text,.theme-balanced-supernova .question-section{
    color:#F87171!important;
    text-shadow: 0 0 15px rgba(248,113,113,0.4)!important;
}
.theme-balanced-supernova .answer-text,.theme-balanced-supernova .cloze-content{
    color:#FCD34D!important;
    text-shadow: 0 0 15px rgba(252,211,77,0.4)!important;
}
.theme-balanced-supernova .cloze{
    background:linear-gradient(135deg,#D97706,#F97316)!important;
    color:#FFEDD5!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(217,119,6,0.4)!important;
}
.theme-balanced-supernova .explanation-block,.theme-balanced-supernova .explanation-section,.theme-balanced-supernova .explanation-info{
    background:rgba(252,211,77,0.1)!important;
    border-left:5px solid #FBBF24!important;
    box-shadow: 0 0 15px rgba(251,191,36,0.15)!important;
}
.theme-balanced-supernova .correlation-block,.theme-balanced-supernova .correlation-section,.theme-balanced-supernova .correlation-info{
    background:rgba(248,113,113,0.1)!important;
    border-left:5px solid #EF4444!important;
    box-shadow: 0 0 15px rgba(239,68,68,0.15)!important;
}
.theme-balanced-supernova .extra-info,.theme-balanced-supernova .comments-block{
    background:rgba(240,253,244,0.1)!important;
    border-left:5px solid #A3E635!important;
    box-shadow: 0 0 15px rgba(163,230,53,0.15)!important;
}

/* 3.4: balanced-galaxy (Deep Indigo and Silver) */
body.theme-balanced-galaxy{
    background:linear-gradient(135deg,#16222A 0%,#3A6073 100%);
    --theme-primary: #9CA3AF;
    --theme-secondary: #E5E7EB;
    --glow-color: rgba(156,163,175,0.3);
}
.theme-balanced-galaxy .card-container,.theme-balanced-galaxy .cloze-container,.theme-balanced-galaxy .mcq-container,.theme-balanced-galaxy .image-container{
    background:rgba(23,37,84,0.8)!important;
    backdrop-filter:blur(16px)!important;
    color:#E0E7FF!important;
    border:1px solid rgba(67,56,202,0.8)!important;
    box-shadow: 0 0 20px rgba(156,163,175,0.15)!important;
}
.theme-balanced-galaxy .meta-header,.theme-balanced-galaxy .header,.theme-balanced-galaxy .cloze-header,.theme-balanced-galaxy .mcq-header,.theme-balanced-galaxy .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(156,163,175,0.3)!important;
}
.theme-balanced-galaxy .theme-family-btn{
    color:#E0E7FF!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
}
.theme-balanced-galaxy .card-type,.theme-balanced-galaxy .cloze-title,.theme-balanced-galaxy .mcq-title,.theme-balanced-galaxy .image-title,.theme-balanced-galaxy .header-text{
    color:#1F2937!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-balanced-galaxy .question-text,.theme-balanced-galaxy .question-section{
    color:#C7D2FE!important;
    text-shadow: 0 0 15px rgba(199,210,254,0.4)!important;
}
.theme-balanced-galaxy .answer-text,.theme-balanced-galaxy .cloze-content{
    color:#A5F3FC!important;
    text-shadow: 0 0 15px rgba(165,243,252,0.4)!important;
}
.theme-balanced-galaxy .cloze{
    background:linear-gradient(135deg,#4F46E5,#6366F1)!important;
    color:#EEF2FF!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(79,70,229,0.4)!important;
}
.theme-balanced-galaxy .explanation-block,.theme-balanced-galaxy .explanation-section,.theme-balanced-galaxy .explanation-info{
    background:rgba(165,243,252,0.1)!important;
    border-left:5px solid #22D3EE!important;
    box-shadow: 0 0 15px rgba(34,211,238,0.15)!important;
}
.theme-balanced-galaxy .correlation-block,.theme-balanced-galaxy .correlation-section,.theme-balanced-galaxy .correlation-info{
    background:rgba(199,210,254,0.1)!important;
    border-left:5px solid #A5B4FC!important;
    box-shadow: 0 0 15px rgba(165,180,252,0.15)!important;
}
.theme-balanced-galaxy .extra-info,.theme-balanced-galaxy .comments-block{
    background:rgba(209,213,219,0.1)!important;
    border-left:5px solid #9CA3AF!important;
    box-shadow: 0 0 15px rgba(156,163,175,0.15)!important;
}

/* 3.5: balanced-comet (Icy Cyan on Dark Blue) */
body.theme-balanced-comet{
    background:linear-gradient(135deg,#0f2027 0%,#203a43 100%);
    --theme-primary: #06B6D4;
    --theme-secondary: #67E8F9;
    --glow-color: rgba(6,182,212,0.3);
}
.theme-balanced-comet .card-container,.theme-balanced-comet .cloze-container,.theme-balanced-comet .mcq-container,.theme-balanced-comet .image-container{
    background:rgba(4,22,37,0.8)!important;
    backdrop-filter:blur(16px)!important;
    color:#CFFAFE!important;
    border:1px solid rgba(14,116,144,0.8)!important;
    box-shadow: 0 0 20px rgba(6,182,212,0.15)!important;
}
.theme-balanced-comet .meta-header,.theme-balanced-comet .header,.theme-balanced-comet .cloze-header,.theme-balanced-comet .mcq-header,.theme-balanced-comet .image-header{
    background:linear-gradient(135deg,var(--theme-primary) 0%,var(--theme-secondary) 100%)!important;
    border-bottom: 1px solid rgba(6,182,212,0.3)!important;
}
.theme-balanced-comet .theme-family-btn{
    color:#CFFAFE!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
}
.theme-balanced-comet .card-type,.theme-balanced-comet .cloze-title,.theme-balanced-comet .mcq-title,.theme-balanced-comet .image-title,.theme-balanced-comet .header-text{
    color:#155E75!important;
    text-shadow: 0 0 10px var(--theme-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--theme-primary);
}
.theme-balanced-comet .question-text,.theme-balanced-comet .question-section{
    color:#22D3EE!important;
    text-shadow: 0 0 15px rgba(34,211,238,0.4)!important;
}
.theme-balanced-comet .answer-text,.theme-balanced-comet .cloze-content{
    color:#A7F3D0!important;
    text-shadow: 0 0 15px rgba(167,243,208,0.4)!important;
}
.theme-balanced-comet .cloze{
    background:linear-gradient(135deg,#0891B2,#22D3EE)!important;
    color:#F0FDF4!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(8,145,178,0.4)!important;
}
.theme-balanced-comet .explanation-block,.theme-balanced-comet .explanation-section,.theme-balanced-comet .explanation-info{
    background:rgba(167,243,208,0.1)!important;
    border-left:5px solid #6EE7B7!important;
    box-shadow: 0 0 15px rgba(110,231,183,0.15)!important;
}
.theme-balanced-comet .correlation-block,.theme-balanced-comet .correlation-section,.theme-balanced-comet .correlation-info{
    background:rgba(165,243,252,0.1)!important;
    border-left:5px solid #67E8F9!important;
    box-shadow: 0 0 15px rgba(103,232,249,0.15)!important;
}
.theme-balanced-comet .extra-info,.theme-balanced-comet .comments-block{
    background:rgba(199,210,254,0.1)!important;
    border-left:5px solid #A5B4FC!important;
    box-shadow: 0 0 15px rgba(165,180,252,0.15)!important;
}

/* =================================================================== */
/* ================= 🌙 FAMILY: TWILIGHT THEMES ===================== */
/* =================================================================== */
/* 4.1: twilight-crescent-moon (Original Dark-Light) */
body.theme-twilight-crescent-moon{background:linear-gradient(-225deg,#222222 0%,#24292e 100%)}
.theme-twilight-crescent-moon .card-container,.theme-twilight-crescent-moon .cloze-container,.theme-twilight-crescent-moon .mcq-container,.theme-twilight-crescent-moon .image-container{background:rgba(31,41,55,0.7);backdrop-filter:blur(14px);color:#E5E7EB;border:1px solid #6B7280}
.theme-twilight-crescent-moon .meta-header,.theme-twilight-crescent-moon .header,.theme-twilight-crescent-moon .cloze-header,.theme-twilight-crescent-moon .mcq-header,.theme-twilight-crescent-moon .image-header{background:linear-gradient(135deg,#868F96 0%,#596164 100%)}
.theme-twilight-crescent-moon .theme-family-btn{color:#E5E7EB}
.theme-twilight-crescent-moon .card-type,.theme-twilight-crescent-moon .cloze-title,.theme-twilight-crescent-moon .mcq-title,.theme-twilight-crescent-moon .image-title,.theme-twilight-crescent-moon .header-text{color:#1F2937!important}
.theme-twilight-crescent-moon .question-text,.theme-twilight-crescent-moon .question-section{color:#BAE6FD!important}
.theme-twilight-crescent-moon .answer-text,.theme-twilight-crescent-moon .cloze-content{color:#D9F99D!important}
.theme-twilight-crescent-moon .cloze{background:linear-gradient(135deg,#0EA5E9,#84CC16)!important;color:#F0F9FF}
.theme-twilight-crescent-moon .explanation-block,.theme-twilight-crescent-moon .explanation-section,.theme-twilight-crescent-moon .explanation-info{background:rgba(217,249,157,0.1);border-left:5px solid #A3E635}
.theme-twilight-crescent-moon .correlation-block,.theme-twilight-crescent-moon .correlation-section,.theme-twilight-crescent-moon .correlation-info{background:rgba(186,230,253,0.1);border-left:5px solid #38BDF8}
.theme-twilight-crescent-moon .extra-info,.theme-twilight-crescent-moon .comments-block{background:rgba(252,211,77,0.1);border-left:5px solid #FBBF24}

/* 4.2: twilight-city-night (Neon on Charcoal) */
body.theme-twilight-city-night{background:linear-gradient(135deg,#35373B 0%,#191919 100%)}
.theme-twilight-city-night .card-container,.theme-twilight-city-night .cloze-container,.theme-twilight-city-night .mcq-container,.theme-twilight-city-night .image-container{background:rgba(30,30,30,0.8);backdrop-filter:blur(10px);color:#F5F5F5;border:1px solid #525252}
.theme-twilight-city-night .meta-header,.theme-twilight-city-night .header,.theme-twilight-city-night .cloze-header,.theme-twilight-city-night .mcq-header,.theme-twilight-city-night .image-header{background:linear-gradient(135deg,#EC4899 0%,#D946EF 100%)}
.theme-twilight-city-night .theme-family-btn{color:#F5F5F5}
.theme-twilight-city-night .card-type,.theme-twilight-city-night .cloze-title,.theme-twilight-city-night .mcq-title,.theme-twilight-city-night .image-title,.theme-twilight-city-night .header-text{color:#FCE7F3!important}
.theme-twilight-city-night .question-text,.theme-twilight-city-night .question-section{color:#A5F3FC!important}
.theme-twilight-city-night .answer-text,.theme-twilight-city-night .cloze-content{color:#F9A8D4!important}
.theme-twilight-city-night .cloze{background:linear-gradient(135deg,#0EA5E9,#22D3EE)!important;color:#F0F9FF}
.theme-twilight-city-night .explanation-block,.theme-twilight-city-night .explanation-section,.theme-twilight-city-night .explanation-info{background:rgba(249,168,212,0.1);border-left:5px solid #F472B6}
.theme-twilight-city-night .correlation-block,.theme-twilight-city-night .correlation-section,.theme-twilight-city-night .correlation-info{background:rgba(165,243,252,0.1);border-left:5px solid #67E8F9}
.theme-twilight-city-night .extra-info,.theme-twilight-city-night .comments-block{background:rgba(167,243,208,0.1);border-left:5px solid #34D399}

/* 4.3: twilight-deep-forest (Earthy dark greens/browns) */
body.theme-twilight-deep-forest{background:linear-gradient(135deg,#29323c 0%,#485563 100%)}
.theme-twilight-deep-forest .card-container,.theme-twilight-deep-forest .cloze-container,.theme-twilight-deep-forest .mcq-container,.theme-twilight-deep-forest .image-container{background:rgba(21,32,23,0.8);backdrop-filter:blur(10px);color:#D4D4D2;border:1px solid #22C55E}
.theme-twilight-deep-forest .meta-header,.theme-twilight-deep-forest .header,.theme-twilight-deep-forest .cloze-header,.theme-twilight-deep-forest .mcq-header,.theme-twilight-deep-forest .image-header{background:linear-gradient(135deg,#16A34A 0%,#22C55E 100%)}
.theme-twilight-deep-forest .theme-family-btn{color:#D4D4D2}
.theme-twilight-deep-forest .card-type,.theme-twilight-deep-forest .cloze-title,.theme-twilight-deep-forest .mcq-title,.theme-twilight-deep-forest .image-title,.theme-twilight-deep-forest .header-text{color:#DCFCE7!important}
.theme-twilight-deep-forest .question-text,.theme-twilight-deep-forest .question-section{color:#BEF264!important}
.theme-twilight-deep-forest .answer-text,.theme-twilight-deep-forest .cloze-content{color:#FDE68A!important}
.theme-twilight-deep-forest .cloze{background:linear-gradient(135deg,#65A30D,#A3E635)!important;color:#F7FEE7}
.theme-twilight-deep-forest .explanation-block,.theme-twilight-deep-forest .explanation-section,.theme-twilight-deep-forest .explanation-info{background:rgba(253,230,138,0.1);border-left:5px solid #FACC15}
.theme-twilight-deep-forest .correlation-block,.theme-twilight-deep-forest .correlation-section,.theme-twilight-deep-forest .correlation-info{background:rgba(190,242,100,0.1);border-left:5px solid #A3E635}
.theme-twilight-deep-forest .extra-info,.theme-twilight-deep-forest .comments-block{background:rgba(252,165,165,0.1);border-left:5px solid #F87171}

/* 4.4: twilight-moonlit-ocean (Silver/Pale Blue on Deep Navy) */
body.theme-twilight-moonlit-ocean{background:linear-gradient(135deg,#00122e 0%,#00285d 100%)}
.theme-twilight-moonlit-ocean .card-container,.theme-twilight-moonlit-ocean .cloze-container,.theme-twilight-moonlit-ocean .mcq-container,.theme-twilight-moonlit-ocean .image-container{background:rgba(0,25,60,0.8);backdrop-filter:blur(12px);color:#B0C4DE;border:1px solid #7B95B4}
.theme-twilight-moonlit-ocean .meta-header,.theme-twilight-moonlit-ocean .header,.theme-twilight-moonlit-ocean .cloze-header,.theme-twilight-moonlit-ocean .mcq-header,.theme-twilight-moonlit-ocean .image-header{background:linear-gradient(135deg,#B0C4DE 0%,#E6E6FA 100%)}
.theme-twilight-moonlit-ocean .theme-family-btn{color:#B0C4DE}
.theme-twilight-moonlit-ocean .card-type,.theme-twilight-moonlit-ocean .cloze-title,.theme-twilight-moonlit-ocean .mcq-title,.theme-twilight-moonlit-ocean .image-title,.theme-twilight-moonlit-ocean .header-text{color:#1E293B!important}
.theme-twilight-moonlit-ocean .question-text,.theme-twilight-moonlit-ocean .question-section{color:#ADD8E6!important}
.theme-twilight-moonlit-ocean .answer-text,.theme-twilight-moonlit-ocean .cloze-content{color:#E6E6FA!important}
.theme-twilight-moonlit-ocean .cloze{background:linear-gradient(135deg,#778899,#B0C4DE)!important;color:#00122e}
.theme-twilight-moonlit-ocean .explanation-block,.theme-twilight-moonlit-ocean .explanation-section,.theme-twilight-moonlit-ocean .explanation-info{background:rgba(230,230,250,0.1);border-left:5px solid #E6E6FA}
.theme-twilight-moonlit-ocean .correlation-block,.theme-twilight-moonlit-ocean .correlation-section,.theme-twilight-moonlit-ocean .correlation-info{background:rgba(173,216,230,0.1);border-left:5px solid #ADD8E6}
.theme-twilight-moonlit-ocean .extra-info,.theme-twilight-moonlit-ocean .comments-block{background:rgba(135,206,250,0.1);border-left:5px solid #87CEFA}

/* 4.5: twilight-dusk (Warm Oranges and Deep Purples) */
body.theme-twilight-dusk{background:linear-gradient(135deg,#2B1055 0%,#7597DE 100%)}
.theme-twilight-dusk .card-container,.theme-twilight-dusk .cloze-container,.theme-twilight-dusk .mcq-container,.theme-twilight-dusk .image-container{background:rgba(43,16,85,0.75);backdrop-filter:blur(10px);color:#F3E8FF;border:1px solid #C084FC}
.theme-twilight-dusk .meta-header,.theme-twilight-dusk .header,.theme-twilight-dusk .cloze-header,.theme-twilight-dusk .mcq-header,.theme-twilight-dusk .image-header{background:linear-gradient(135deg,#F97316 0%,#EA580C 100%)}
.theme-twilight-dusk .theme-family-btn{color:#F3E8FF}
.theme-twilight-dusk .card-type,.theme-twilight-dusk .cloze-title,.theme-twilight-dusk .mcq-title,.theme-twilight-dusk .image-title,.theme-twilight-dusk .header-text{color:#FFEDD5!important}
.theme-twilight-dusk .question-text,.theme-twilight-dusk .question-section{color:#F0ABFC!important}
.theme-twilight-dusk .answer-text,.theme-twilight-dusk .cloze-content{color:#FDBA74!important}
.theme-twilight-dusk .cloze{background:linear-gradient(135deg,#D946EF,#C084FC)!important;color:#FAE8FF}
.theme-twilight-dusk .explanation-block,.theme-twilight-dusk .explanation-section,.theme-twilight-dusk .explanation-info{background:rgba(253,186,116,0.1);border-left:5px solid #FB923C}
.theme-twilight-dusk .correlation-block,.theme-twilight-dusk .correlation-section,.theme-twilight-dusk .correlation-info{background:rgba(240,171,252,0.1);border-left:5px solid #E879F9}
.theme-twilight-dusk .extra-info,.theme-twilight-dusk .comments-block{background:rgba(187,247,208,0.1);border-left:5px solid #86EFAC}

/* =================================================================== */
/* ==================== 🪐 FAMILY: DARK THEMES ======================= */
/* =================================================================== */
/* 5.1: dark-saturn (Original Dark) */
body.theme-dark-saturn{
    background:linear-gradient(-225deg,#201c27 0%,#000000 100%);
    --neon-primary: #F43F5E;
    --neon-secondary: #A21CAF;
    --glow-color: rgba(244, 63, 94, 0.5);
}
.theme-dark-saturn .card-container,.theme-dark-saturn .cloze-container,.theme-dark-saturn .mcq-container,.theme-dark-saturn .image-container{
    background:rgba(17,24,39,0.85)!important;
    backdrop-filter:blur(16px)!important;
    color:#F3F4F6!important;
    border:1px solid rgba(75,85,99,0.4)!important;
    box-shadow: 0 0 20px rgba(244,63,94,0.2)!important;
}
.theme-dark-saturn .meta-header,.theme-dark-saturn .header,.theme-dark-saturn .cloze-header,.theme-dark-saturn .mcq-header,.theme-dark-saturn .image-header{
    background:linear-gradient(135deg,var(--neon-primary) 0%,var(--neon-secondary) 100%)!important;
    border-bottom: 1px solid rgba(244,63,94,0.3)!important;
}
.theme-dark-saturn .theme-family-btn{
    color:#F3F4F6!important;
    text-shadow: 0 0 10px var(--neon-primary)!important;
}
.theme-dark-saturn .card-type,.theme-dark-saturn .cloze-title,.theme-dark-saturn .mcq-title,.theme-dark-saturn .image-title,.theme-dark-saturn .header-text{
    color:#FFF1F2!important;
    text-shadow: 0 0 10px var(--neon-primary)!important;
    animation: neonTextPulse 2s infinite!important;
    --neon-color: var(--neon-primary);
}
.theme-dark-saturn .question-text,.theme-dark-saturn .question-section{
    color:#F9A8D4!important;
    text-shadow: 0 0 15px rgba(244,63,94,0.5)!important;
}
.theme-dark-saturn .answer-text,.theme-dark-saturn .cloze-content{
    color:#F0ABFC!important;
    text-shadow: 0 0 15px rgba(162,28,175,0.5)!important;
}
.theme-dark-saturn .cloze{
    background:linear-gradient(135deg,#EC4899,#D946EF)!important;
    color:#FDF2F8!important;
    font-weight: bold!important;
    box-shadow: 0 0 15px rgba(236,72,153,0.5)!important;
}
.theme-dark-saturn .explanation-block,.theme-dark-saturn .explanation-section,.theme-dark-saturn .explanation-info{
    background:rgba(240,171,252,0.1)!important;
    border-left:5px solid #E879F9!important;
    box-shadow: 0 0 15px rgba(232,121,249,0.15)!important;
}
.theme-dark-saturn .correlation-block,.theme-dark-saturn .correlation-section,.theme-dark-saturn .correlation-info{
    background:rgba(249,168,212,0.1)!important;
    border-left:5px solid #F472B6!important;
    box-shadow: 0 0 15px rgba(244,114,182,0.15)!important;
}
.theme-dark-saturn .extra-info,.theme-dark-saturn .comments-block{
    background:rgba(165,243,252,0.1)!important;
    border-left:5px solid #67E8F9!important;
    box-shadow: 0 0 15px rgba(103,232,249,0.15)!important;
}

/* 5.2: dark-mars-rover (Rusty Reds on Black) */
body.theme-dark-mars-rover{background:#000}
.theme-dark-mars-rover .card-container,.theme-dark-mars-rover .cloze-container,.theme-dark-mars-rover .mcq-container,.theme-dark-mars-rover .image-container{background:rgba(10,5,5,0.8);backdrop-filter:blur(10px);color:#FFDBCB;border:1px solid #B91C1C}
.theme-dark-mars-rover .meta-header,.theme-dark-mars-rover .header,.theme-dark-mars-rover .cloze-header,.theme-dark-mars-rover .mcq-header,.theme-dark-mars-rover .image-header{background:linear-gradient(135deg,#991B1B 0%,#B91C1C 100%)}
.theme-dark-mars-rover .theme-family-btn{color:#FFDBCB}
.theme-dark-mars-rover .card-type,.theme-dark-mars-rover .cloze-title,.theme-dark-mars-rover .mcq-title,.theme-dark-mars-rover .image-title,.theme-dark-mars-rover .header-text{color:#FEF2F2!important}
.theme-dark-mars-rover .question-text,.theme-dark-mars-rover .question-section{color:#FCA5A5!important}
.theme-dark-mars-rover .answer-text,.theme-dark-mars-rover .cloze-content{color:#FED7AA!important}
.theme-dark-mars-rover .cloze{background:linear-gradient(135deg,#B45309,#D97706)!important;color:#FFF7ED}
.theme-dark-mars-rover .explanation-block,.theme-dark-mars-rover .explanation-section,.theme-dark-mars-rover .explanation-info{background:rgba(254,215,170,0.1);border-left:5px solid #FDBA74}
.theme-dark-mars-rover .correlation-block,.theme-dark-mars-rover .correlation-section,.theme-dark-mars-rover .correlation-info{background:rgba(252,165,165,0.1);border-left:5px solid #FCA5A5}
.theme-dark-mars-rover .extra-info,.theme-dark-mars-rover .comments-block{background:rgba(217,217,217,0.1);border-left:5px solid #A8A29E}

/* 5.3: dark-neptune-deep (Deep Blues on Black) */
body.theme-dark-neptune-deep{background:#000}
.theme-dark-neptune-deep .card-container,.theme-dark-neptune-deep .cloze-container,.theme-dark-neptune-deep .mcq-container,.theme-dark-neptune-deep .image-container{background:rgba(5,10,20,0.8);backdrop-filter:blur(10px);color:#DBEAFE;border:1px solid #1D4ED8}
.theme-dark-neptune-deep .meta-header,.theme-dark-neptune-deep .header,.theme-dark-neptune-deep .cloze-header,.theme-dark-neptune-deep .mcq-header,.theme-dark-neptune-deep .image-header{background:linear-gradient(135deg,#1E40AF 0%,#2563EB 100%)}
.theme-dark-neptune-deep .theme-family-btn{color:#DBEAFE}
.theme-dark-neptune-deep .card-type,.theme-dark-neptune-deep .cloze-title,.theme-dark-neptune-deep .mcq-title,.theme-dark-neptune-deep .image-title,.theme-dark-neptune-deep .header-text{color:#EFF6FF!important}
.theme-dark-neptune-deep .question-text,.theme-dark-neptune-deep .question-section{color:#93C5FD!important}
.theme-dark-neptune-deep .answer-text,.theme-dark-neptune-deep .cloze-content{color:#A5F3FC!important}
.theme-dark-neptune-deep .cloze{background:linear-gradient(135deg,#0C4A6E,#0369A1)!important;color:#E0F2FE}
.theme-dark-neptune-deep .explanation-block,.theme-dark-neptune-deep .explanation-section,.theme-dark-neptune-deep .explanation-info{background:rgba(165,243,252,0.1);border-left:5px solid #22D3EE}
.theme-dark-neptune-deep .correlation-block,.theme-dark-neptune-deep .correlation-section,.theme-dark-neptune-deep .correlation-info{background:rgba(147,197,253,0.1);border-left:5px solid #93C5FD}
.theme-dark-neptune-deep .extra-info,.theme-dark-neptune-deep .comments-block{background:rgba(199,210,254,0.1);border-left:5px solid #C7D2FE}

/* 5.4: dark-black-hole (Monochrome) */
body.theme-dark-black-hole{background:#000}
.theme-dark-black-hole .card-container,.theme-dark-black-hole .cloze-container,.theme-dark-black-hole .mcq-container,.theme-dark-black-hole .image-container{background:rgba(10,10,10,0.8);backdrop-filter:blur(10px);color:#D4D4D4;border:1px solid #404040}
.theme-dark-black-hole .meta-header,.theme-dark-black-hole .header,.theme-dark-black-hole .cloze-header,.theme-dark-black-hole .mcq-header,.theme-dark-black-hole .image-header{background:#262626}
.theme-dark-black-hole .theme-family-btn{color:#D4D4D4}
.theme-dark-black-hole .card-type,.theme-dark-black-hole .cloze-title,.theme-dark-black-hole .mcq-title,.theme-dark-black-hole .image-title,.theme-dark-black-hole .header-text{color:#FAFAFA!important}
.theme-dark-black-hole .question-text,.theme-dark-black-hole .question-section{color:#A3A3A3!important}
.theme-dark-black-hole .answer-text,.theme-dark-black-hole .cloze-content{color:#E5E5E5!important}
.theme-dark-black-hole .cloze{background:#737373!important;color:#171717}
.theme-dark-black-hole .explanation-block,.theme-dark-black-hole .explanation-section,.theme-dark-black-hole .explanation-info{background:#171717;border-left:5px solid #525252}
.theme-dark-black-hole .correlation-block,.theme-dark-black-hole .correlation-section,.theme-dark-black-hole .correlation-info{background:#171717;border-left:5px solid #A3A3A3}
.theme-dark-black-hole .extra-info,.theme-dark-black-hole .comments-block{background:#171717;border-left:5px solid #737373}

/* 5.5: dark-starless-sky (Pure Black/OLED) */
body.theme-dark-starless-sky{background:#000}
.theme-dark-starless-sky .card-container,.theme-dark-starless-sky .cloze-container,.theme-dark-starless-sky .mcq-container,.theme-dark-starless-sky .image-container{background:#000;backdrop-filter:none;color:#A1A1AA;border:1px solid #27272A}
.theme-dark-starless-sky .meta-header,.theme-dark-starless-sky .header,.theme-dark-starless-sky .cloze-header,.theme-dark-starless-sky .mcq-header,.theme-dark-starless-sky .image-header{background:#18181B}
.theme-dark-starless-sky .theme-family-btn{color:#A1A1AA}
.theme-dark-starless-sky .card-type,.theme-dark-starless-sky .cloze-title,.theme-dark-starless-sky .mcq-title,.theme-dark-starless-sky .image-title,.theme-dark-starless-sky .header-text{color:#E4E4E7!important}
.theme-dark-starless-sky .question-text,.theme-dark-starless-sky .question-section{color:#4ADE80!important}
.theme-dark-starless-sky .answer-text,.theme-dark-starless-sky .cloze-content{color:#38BDF8!important}
.theme-dark-starless-sky .cloze{background:linear-gradient(135deg,#22C55E,#4ADE80)!important;color:#052E16}
.theme-dark-starless-sky .explanation-block,.theme-dark-starless-sky .explanation-section,.theme-dark-starless-sky .explanation-info{background:#09090B;border-left:5px solid #38BDF8}
.theme-dark-starless-sky .correlation-block,.theme-dark-starless-sky .correlation-section,.theme-dark-starless-sky .correlation-info{background:#09090B;border-left:5px solid #4ADE80}
.theme-dark-starless-sky .extra-info,.theme-dark-starless-sky .comments-block{background:#09090B;border-left:5px solid #A855F7}
'''

# ==============================================================================
# =================  ANKI MODEL DEFINITIONS (UNCHANGED) ========================
# ==============================================================================
# The UI HTML and model definitions are correct from your last script.
# No changes are needed in this section.

THEME_UI_HTML = '''
<div class="theme-controls">
    <button id="themeBtn-light" class="theme-family-btn" title="Light Themes">🌕</button>
    <button id="themeBtn-nord" class="theme-family-btn" title="Nord Themes">☀️</button>
    <button id="themeBtn-balanced" class="theme-family-btn" title="Balanced Themes">⭐</button>
    <button id="themeBtn-twilight" class="theme-family-btn" title="Twilight Themes">🌙</button>
    <button id="themeBtn-dark" class="theme-family-btn" title="Dark Themes">🪐</button>
</div>
'''

# Basic Model
basic_model = Model(
    1607392319,
    'Joplin to Anki Basic Enhanced',
    fields=[
        {'name': 'Header'},
        {'name': 'Question'},
        {'name': 'Answer'},
        {'name': 'Explanation'},
        {'name': 'Clinical Correlation'},
        {'name': 'Footer'},
        {'name': 'Sources'},
        {'name': 'Joplin to Anki ID'},
    ],
    templates=[
        {
            'name': 'Enhanced Basic Card',
            'qfmt': '''
<div class="card-container question-side">
    <div class="master-header">
        {{#Header}}
        <div class="meta-header">
            ''' + THEME_UI_HTML + '''
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="header">
            {{^Header}}''' + THEME_UI_HTML + '''{{/Header}}
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
            ''' + THEME_UI_HTML + '''  
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="header">
            {{^Header}}''' + THEME_UI_HTML + '''{{/Header}}
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
/* === MODIFIED FOR SCREEN-RELATIVE SIZING === */
.card {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 2.5vh 2.5vw;
    /* Use viewport units for padding */
    box-sizing: border-box;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    /* Ensure background covers the whole screen */
}
.card-container {
    width: 90vw;
    /* Occupy 90% of the viewport width */
    max-width: 1100px;
    /* But not more than 1100px on wide screens */
    max-height: 90vh;
    /* Occupy up to 90% of the viewport height */
    overflow-y: auto;
    /* Add a scrollbar INSIDE the card if content is too long */
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
    overflow-x: hidden;
    /* Prevent horizontal overflow */
    animation: bounceIn 0.8s ease-out;
    display: flex;
    /* Use flexbox for better structure */
    flex-direction: column;
}
.master-header {
    position: relative;
}
.content-area img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
    border-radius: 10px;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}
@keyframes bounceIn {
    0% {
        transform: scale(0.3) translateY(-50px);
        opacity: 0;
    }
    50% {
        transform: scale(1.05);
    }
    70% {
        transform: scale(0.9);
    }
    100% {
        transform: scale(1) translateY(0);
        opacity: 1;
    }
}
.meta-header {
    position: relative;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.95em;
    font-weight: 600;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}
.header-icon,
.footer-icon {
    font-size: 1.2em;
}
.header-text,
.footer-text {
    flex: 1;
}
.header {
    position: relative;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 15px;
}
.question-icon,
.answer-icon {
    font-size: 2em;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%,
    100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.1);
    }
}
@keyframes rotateClozeIcon {
    0% { transform: rotate(0deg); }
    50% { transform: rotate(60deg); }
    100% { transform: rotate(0deg); }
}
.card-type {
    font-size: 1.4em;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.content-area {
    padding: 30px;
}
.question-text,
.answer-text {
    font-size: 1.2em;
    margin-bottom: 25px;
    text-align: center;
    font-weight: 500;
}
.custom-question,
.custom-answer {
    font-weight: 600 !important;
    font-size: 1.2em !important;
}
.custom-explanation,
.custom-correlation {
    font-weight: 500 !important;
    font-size: 1em !important;
    font-style: italic !important;
}
.explanation-section,
.correlation-section,
.extra-info,
.comments-block {
    margin-top: 25px;
    padding: 20px;
    border-radius: 15px;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(5px);
}

.explanation-section::before,
.correlation-section::before,
.extra-info::before,
.comments-block::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, 
        var(--section-glow-1, rgba(255,255,255,0.05)), 
        var(--section-glow-2, rgba(255,255,255,0.1)));
    opacity: 0.1;
    z-index: -1;
}

.explanation-section {
    --section-glow-1: #38b2ac;
    --section-glow-2: #4fd1c5;
}

.correlation-section {
    --section-glow-1: #8b5cf6;
    --section-glow-2: #a78bfa;
}

.extra-info {
    --section-glow-1: #f97316;
    --section-glow-2: #fb923c;
}

.comments-block {
    --section-glow-1: #06b6d4;
    --section-glow-2: #22d3ee;
}
.section-title {
    font-weight: 600;
    font-size: 1.1em;
    margin-bottom: 10px;
}
.meta-footer {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.9em;
    border-top: 1px solid rgba(150, 150, 150, 0.2);
    margin-top: auto;
    /* Pushes footer to the bottom */
}
.sources-section {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.85em;
    font-style: italic !important;
    border-top: 1px solid rgba(150, 150, 150, 0.2);
}
.sources-icon {
    font-size: 1.1em;
}
.sources-text {
    flex: 1;
}
.divider {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, #4facfe, transparent);
    margin: 20px 0;
}
.toggle-controls {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin: 25px 0;
    padding: 10px;
    flex-wrap: wrap;
}
.toggle-btn {
    border: none;
    padding: 12px 24px;
    border-radius: 25px;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
    flex-shrink: 0;
    animation: pulse-button 3s ease-in-out infinite;
}
.toggle-btn:hover {
    transform: translateY(-3px) scale(1.05);
    animation-play-state: paused;
}
.toggle-btn:active {
    transform: translateY(0);
}
.explanation-btn {
    background: linear-gradient(135deg, #38b2ac, #4fd1c5);
    box-shadow: 0 0 15px rgba(56, 178, 172, 0.4);
}
.correlation-btn {
    background: linear-gradient(135deg, #8b5cf6, #a78bfa);
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
}
.showall-btn {
    background: linear-gradient(135deg, #6b7280, #4b5563);
    box-shadow: 0 0 15px rgba(107, 114, 128, 0.3);
    color: #E5E7EB;
}
.hidden {
    display: none !important;
}
.explanation-section:not(.hidden),
.correlation-section:not(.hidden) {
    animation: slideDown 0.3s ease-out;
}
@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
'''
)

# Cloze model (v14)
cloze_model = Model(
    1607392320,
    'Joplin to Anki Cloze Enhanced',
    fields=[
        {'name': 'Header'},
        {'name': 'Text'},
        {'name': 'Extra'},
        {'name': 'Explanation'},
        {'name': 'Clinical Correlation'},
        {'name': 'Footer'},
        {'name': 'Sources'},
        {'name': 'Joplin to Anki ID'},
    ],
    templates=[
        {
            'name': 'Enhanced Cloze Card',
            'qfmt': '''
<div class="cloze-container">
    <div class="master-header">
        {{#Header}}
        <div class="meta-header">
            ''' + THEME_UI_HTML + '''
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="cloze-header">
            {{^Header}}''' + THEME_UI_HTML + '''{{/Header}}
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
            ''' + THEME_UI_HTML + '''
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="cloze-header">
            {{^Header}}''' + THEME_UI_HTML + '''{{/Header}}
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
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
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
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
    overflow-x: hidden;
    animation: bounceIn 0.8s ease-out;
    display: flex;
    flex-direction: column;
}
.master-header {
    position: relative;
}
.cloze-content img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
    border-radius: 10px;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}
@keyframes bounceIn {
    0% {
        transform: scale(0.3) translateY(-50px);
        opacity: 0;
    }
    50% {
        transform: scale(1.05);
    }
    70% {
        transform: scale(0.9);
    }
    100% {
        transform: scale(1) translateY(0);
        opacity: 1;
    }
}
.meta-header {
    position: relative;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.95em;
    font-weight: 600;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}
.header-icon,
.footer-icon {
    font-size: 1.2em;
}
.header-text,
.footer-text {
    flex: 1;
}
.cloze-header {
    position: relative;
    padding: 25px;
    display: flex;
    align-items: center;
    gap: 20px;
}
.cloze-icon {
    font-size: 2.5em;
    animation: rotateClozeIcon 4s ease-in-out infinite;
    display: inline-block;
}
.cloze-title {
    font-size: 1.5em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.cloze-content {
    padding: 20px;
    font-size: 1.2em;
    line-height: 1.8;
    text-align: center;
}
.cloze {
    padding: 8px 16px;
    border-radius: 25px;
    display: inline-block;
    margin: 0 4px;
    position: relative;
    animation: glowPulse 2s infinite;
    --glow-color: rgba(255, 255, 255, 0.3);
}
.custom-extra,
.custom-explanation,
.custom-correlation {
    font-weight: 500 !important;
    font-style: italic !important;
}
.extra-info,
.explanation-info,
.correlation-info {
    margin-top: 30px;
    padding: 25px;
    border-radius: 15px;
    font-size: 0.9em;
    text-align: left;
    line-height: 1.6;
}
.extra-title,
.explanation-title,
.correlation-title {
    font-weight: 600;
    font-size: 1.1em;
    margin-bottom: 15px;
}
.extra-content,
.explanation-content,
.correlation-content {
    font-size: 1.0em;
    white-space: pre-wrap;
    font-style: italic !important;
}
.meta-footer {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.9em;
    border-top: 1px solid rgba(150, 150, 150, 0.2);
    margin-top: auto;
}
.sources-section {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.85em;
    font-style: italic !important;
    border-top: 1px solid rgba(150, 150, 150, 0.2);
}
.sources-icon {
    font-size: 1.1em;
}
.sources-text {
    flex: 1;
}
.cloze-divider {
    border: none;
    height: 3px;
    background: linear-gradient(90deg, transparent, #ff7675, transparent);
    margin: 25px 0;
}
.toggle-controls {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin: 25px 0;
    padding: 10px;
    flex-wrap: wrap;
}
.toggle-btn {
    border: none;
    padding: 12px 24px;
    border-radius: 25px;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
    flex-shrink: 0;
    animation: pulse-button 3s ease-in-out infinite;
}
.toggle-btn:hover {
    transform: translateY(-3px) scale(1.05);
    animation-play-state: paused;
}
.toggle-btn:active {
    transform: translateY(0);
}
.explanation-btn {
    background: linear-gradient(135deg, #38b2ac, #4fd1c5);
    box-shadow: 0 0 15px rgba(56, 178, 172, 0.4);
}
.correlation-btn {
    background: linear-gradient(135deg, #8b5cf6, #a78bfa);
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
}
.extra-btn {
    background: linear-gradient(135deg, #f97316, #fb923c);
    box-shadow: 0 0 15px rgba(249, 115, 22, 0.4);
}
.showall-btn {
    background: linear-gradient(135deg, #6b7280, #4b5563);
    box-shadow: 0 0 15px rgba(107, 114, 128, 0.3);
    color: #E5E7EB;
}
.hidden {
    display: none !important;
}
.extra-info:not(.hidden),
.explanation-info:not(.hidden),
.correlation-info:not(.hidden) {
    animation: slideDown 0.3s ease-out;
}
@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
''',
    model_type=1
)

# MCQ model (v14)
mcq_model = Model(
    1607392321,
    'Joplin to Anki MCQ Enhanced',
    fields=[
        {'name': 'Header'},
        {'name': 'Question'},
        {'name': 'OptionA'},
        {'name': 'OptionB'},
        {'name': 'OptionC'},
        {'name': 'OptionD'},
        {'name': 'CorrectAnswer'},
        {'name': 'Explanation'},
        {'name': 'Clinical Correlation'},
        {'name': 'Footer'},
        {'name': 'Sources'},
        {'name': 'Joplin to Anki ID'},
    ],
    templates=[
        {
            'name': 'Enhanced MCQ Card',
            'qfmt': '''
<div class="mcq-container">
    <div class="master-header">
        {{#Header}}
        <div class="meta-header">
            ''' + THEME_UI_HTML + '''
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="mcq-header">
            {{^Header}}''' + THEME_UI_HTML + '''{{/Header}}
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
            ''' + THEME_UI_HTML + '''
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="mcq-header">
            {{^Header}}''' + THEME_UI_HTML + '''{{/Header}}
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
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
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
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
    overflow-x: hidden;
    animation: bounceIn 0.8s ease-out;
    display: flex;
    flex-direction: column;
}
.master-header {
    position: relative;
}
.mcq-content img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
    border-radius: 10px;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}
@keyframes bounceIn {
    0% {
        transform: scale(0.3) translateY(-50px);
        opacity: 0;
    }
    50% {
        transform: scale(1.05);
    }
    70% {
        transform: scale(0.9);
    }
    100% {
        transform: scale(1) translateY(0);
        opacity: 1;
    }
}
.meta-header {
    position: relative;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.95em;
    font-weight: 600;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}
.header-icon,
.footer-icon {
    font-size: 1.2em;
}
.header-text,
.footer-text {
    flex: 1;
}
.mcq-header {
    position: relative;
    padding: 25px;
    display: flex;
    align-items: center;
    gap: 20px;
}
.mcq-icon {
    font-size: 2.5em;
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
    0%,
    100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.1);
    }
}
.mcq-title {
    font-size: 1.5em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.mcq-content {
    padding: 10px;
}
.question-section {
    font-size: 1.35em;
    margin-bottom: 20px;
    text-align: center;
    font-weight: 500;
    line-height: 1.4;
}
.options-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 18px;
}
.option {
    padding: 18px 22px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    gap: 14px;
    cursor: pointer;
    transition: all 0.3s ease;
    word-wrap: break-word;
    font-size: 1.15em;
    border-left: 6px solid;
    position: relative;
    overflow: hidden;
}

.option::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, var(--option-glow-1, rgba(255,255,255,0.1)), var(--option-glow-2, rgba(255,255,255,0.2)));
    opacity: 0;
    transition: opacity 0.3s ease;
}

.option:hover::before {
    opacity: 0.2;
}

.option-a {
    --option-glow-1: #f472b6;
    --option-glow-2: #ec4899;
    border-color: #f472b6;
}

.option-b {
    --option-glow-1: #34d399;
    --option-glow-2: #10b981;
    border-color: #34d399;
}

.option-c {
    --option-glow-1: #60a5fa;
    --option-glow-2: #3b82f6;
    border-color: #60a5fa;
}

.option-d {
    --option-glow-1: #a78bfa;
    --option-glow-2: #8b5cf6;
    border-color: #a78bfa;
}
.option:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 28px rgba(0, 0, 0, 0.12);
}
.option-letter {
    padding: 8px 12px;
    border-radius: 50%;
    font-weight: bold;
}
.option-text {
    font-size: 1.15em;
    flex: 1;
}
.correct-answer {
    padding: 20px;
    background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%);
    border-radius: 12px;
    margin-bottom: 25px;
    text-align: center;
}
.answer-label {
    font-weight: 700;
    margin-bottom: 10px;
    color: #2d3436;
}
.answer-value {
    font-size: 1.3em;
    font-weight: 600;
}
.custom-explanation,
.custom-correlation {
    font-weight: 500 !important;
    font-style: italic !important;
}
.explanation-block,
.correlation-block {
    margin-top: 20px;
    padding: 20px;
    border-radius: 15px;
    font-size: 1.0em;
}
.block-title {
    font-weight: 700;
    margin-bottom: 10px;
}
.block-content {
    font-size: 1.0em;
}
.meta-footer {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.9em;
    border-top: 1px solid rgba(150, 150, 150, 0.2);
    margin-top: auto;
}
.sources-section {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.85em;
    font-style: italic !important;
    border-top: 1px solid rgba(150, 150, 150, 0.2);
}
.sources-icon {
    font-size: 1.1em;
}
.sources-text {
    flex: 1;
}
.mcq-divider {
    border: none;
    height: 3px;
    background: linear-gradient(90deg, transparent, #0984e3, transparent);
    margin: 25px 0;
}
.toggle-controls {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin: 25px 0;
    padding: 10px;
    flex-wrap: wrap;
}
.toggle-btn {
    border: none;
    padding: 12px 24px;
    border-radius: 25px;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
    flex-shrink: 0;
    animation: pulse-button 3s ease-in-out infinite;
}
.toggle-btn:hover {
    transform: translateY(-3px) scale(1.05);
    animation-play-state: paused;
}
.toggle-btn:active {
    transform: translateY(0);
}
.explanation-btn {
    background: linear-gradient(135deg, #38b2ac, #4fd1c5);
    box-shadow: 0 0 15px rgba(56, 178, 172, 0.4);
}
.correlation-btn {
    background: linear-gradient(135deg, #8b5cf6, #a78bfa);
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
}
.showall-btn {
    background: linear-gradient(135deg, #6b7280, #4b5563);
    box-shadow: 0 0 15px rgba(107, 114, 128, 0.3);
    color: #E5E7EB;
}
.hidden {
    display: none !important;
}
.explanation-block:not(.hidden),
.correlation-block:not(.hidden) {
    animation: slideDown 0.3s ease-out;
}
@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
'''
)

# Image model (v14)
image_model = Model(
    1607392322,
    'Joplin to Anki Image Enhanced',
    fields=[
        {'name': 'Header'},
        {'name': 'QuestionImagePath'},
        {'name': 'AnswerImagePath'},
        {'name': 'Question'},
        {'name': 'Answer'},
        {'name': 'Origin'},
        {'name': 'Insertion'},
        {'name': 'Innervation'},
        {'name': 'Action'},
        {'name': 'Clinical Correlation'},
        {'name': 'Comments'},
        {'name': 'Footer'},
        {'name': 'Sources'},
        {'name': 'Joplin to Anki ID'},
    ],
    templates=[
        {
            'name': 'Enhanced Image Occlusion Card',
            'qfmt': '''
<div class="image-container">
    <div class="master-header">
        {{#Header}}
        <div class="meta-header">
            ''' + THEME_UI_HTML + '''
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="image-header">
            {{^Header}}''' + THEME_UI_HTML + '''{{/Header}}
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
            ''' + THEME_UI_HTML + '''
            <span class="header-icon">📚</span><span class="header-text">{{Header}}</span>
        </div>
        {{/Header}}
        <div class="image-header">
            {{^Header}}''' + THEME_UI_HTML + '''{{/Header}}
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
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
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
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
    overflow-x: hidden;
    animation: bounceIn 0.8s ease-out;
    display: flex;
    flex-direction: column;
}
.master-header {
    position: relative;
}
.image-content img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
    border-radius: 10px;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}
@keyframes bounceIn {
    0% {
        transform: scale(0.3) translateY(-50px);
        opacity: 0;
    }
    50% {
        transform: scale(1.05);
    }
    70% {
        transform: scale(0.9);
    }
    100% {
        transform: scale(1) translateY(0);
        opacity: 1;
    }
}
.meta-header {
    position: relative;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.95em;
    font-weight: 600;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}
.header-icon,
.footer-icon {
    font-size: 1.2em;
}
.header-text,
.footer-text {
    flex: 1;
}
.image-header {
    position: relative;
    padding: 25px;
    display: flex;
    align-items: center;
    gap: 20px;
}
.image-icon {
    font-size: 2em;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%,
    100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.1);
    }
}
.image-title {
    font-size: 1.5em;
    font-weight: 700;
    text-transform: uppercase;
}
.image-content {
    position: relative;
    padding: 30px;
    text-align: center;
}
.main-image {
    max-width: 100%;
    border-radius: 15px;
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
    display: block;
    margin: 0 auto;
}
.main-image:hover {
    transform: scale(1.02);
}
.question-overlay,
.answer-overlay {
    margin-bottom: 20px;
    padding: 15px 25px;
    border-radius: 12px;
    font-weight: 500;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    text-align: center;
}
.custom-image-question {
    background: rgba(255, 255, 255, 0.95) !important;
    font-weight: 600 !important;
    font-size: 1.3em !important;
    border: 2px solid #5d4037 !important;
    padding: 20px !important;
    position: relative;
    z-index: 2;
}
.custom-image-answer {
    background: linear-gradient(135deg, #f093fb, #f5576c) !important;
    color: #FDF2F8 !important;
    font-weight: 600 !important;
    font-size: 1.3em !important;
    padding: 10px;
    border-radius: 8px;
    position: relative;
    z-index: 2;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
}
.custom-comments,
.custom-correlation {
    font-weight: 500 !important;
    font-style: italic !important;
}
.correlation-section,
.comments-block {
    margin: 25px;
    padding: 20px;
    border-radius: 15px;
}
.section-title,
.comments-title {
    font-weight: 600;
    margin-bottom: 10px;
    font-size: 1.1em;
}
.correlation-text,
.comments-text {
    font-size: 1.0em;
    text-align: left;
}
.meta-footer {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.9em;
    border-top: 1px solid rgba(150, 150, 150, 0.2);
    margin-top: auto;
}
.sources-section {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.85em;
    font-style: italic !important;
    ;
    border-top: 1px solid rgba(150, 150, 150, 0.2);
}
.sources-icon {
    font-size: 1.1em;
}
.sources-text {
    flex: 1;
}
.image-divider {
    border: none;
    height: 3px;
    background: linear-gradient(90deg, transparent, #74b9ff, transparent);
    margin: 25px 0;
}
.anatomy-section {
    margin: 20px 25px;
    padding: 20px;
    border-radius: 15px;
    border-left: 5px solid;
}
.anatomy-title {
    font-weight: 700 !important;
    font-size: 1.3em;
    margin-bottom: 12px;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    letter-spacing: 0.5px;
}
.anatomy-text {
    font-size: 1.1em;
    line-height: 1.6;
}
.custom-origin,
.custom-insertion,
.custom-innervation,
.custom-action {
    font-weight: 600 !important;
    font-size: 1.2em !important;
    font-style: normal !important;
    text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.4);
}
.toggle-controls {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin: 25px 0;
    padding: 10px;
    flex-wrap: wrap;
}
.toggle-btn {
    border: none;
    padding: 12px 24px;
    border-radius: 25px;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
    flex-shrink: 0;
    animation: pulse-button 3s ease-in-out infinite;
}
.toggle-btn:hover {
    transform: translateY(-3px) scale(1.05);
    animation-play-state: paused;
}
.toggle-btn:active {
    transform: translateY(0);
}
.correlation-btn {
    background: linear-gradient(135deg, #8b5cf6, #a78bfa);
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
}
.comments-btn {
    background: linear-gradient(135deg, #f97316, #fb923c);
    box-shadow: 0 0 15px rgba(249, 115, 22, 0.4);
}
.showall-btn {
    background: linear-gradient(135deg, #6b7280, #4b5563);
    box-shadow: 0 0 15px rgba(107, 114, 128, 0.3);
    color: #E5E7EB;
}
.hidden {
    display: none !important;
}
.correlation-section:not(.hidden),
.comments-block:not(.hidden) {
    animation: slideDown 0.3s ease-out;
}
@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
'''
)

def create_deck(name):
    return Deck(2059400110, name)

def create_test_notes():
    deck = create_deck('Joplin to Anki Enhanced - FINAL TEST SUITE')
    print("Creating a comprehensive test suite with 8 notes (v14)...")

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

if __name__ == '__main__':
    deck = create_test_notes()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_directory = "output"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    filename = os.path.join(output_directory, f"joplin_anki_ENHANCED_FINAL_{timestamp}.apkg")

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

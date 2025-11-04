# -- coding: utf-8 --
from genanki import Model, Deck, Note, Package
import datetime
import glob
import os

# ==============================================================================
# =====================  OPTIMIZED THEME SCRIPT (v18 - FOUC FIXED) ===========
# ==============================================================================
# Changes from v17:
# - Split into TWO scripts: INLINE (instant) + MAIN (debounced)
# - INLINE script applies theme IMMEDIATELY (no FOUC)
# - MAIN script handles interactions/observers (crash-safe)
# - Both scripts work together seamlessly
# ==============================================================================

# ============ SCRIPT 1: INLINE FOUC FIX (Goes in <head>, runs FIRST) =========
THEME_JS_FOUC_FIX = '''
<script>
// FOUC Prevention: Ultra-minimal, synchronous, IMMEDIATE theme application
// This runs BEFORE any content renders, preventing flash
(function() {
    'use strict';
    
    const THEME_KEY = 'joplinAnkiTheme_v3';
    const DEFAULT_THEME = 'light-full-moon';
    
    // Valid themes (minimal check)
    const VALID_THEMES = [
        'light-full-moon', 'light-waning-gibbous', 'light-last-quarter', 'light-waning-crescent', 'light-new-moon',
        'nord-bright-sun', 'nord-overcast-day', 'nord-stormy-sky', 'nord-aurora', 'nord-polar-night',
        'balanced-star', 'balanced-nebula', 'balanced-supernova', 'balanced-galaxy', 'balanced-comet',
        'twilight-crescent-moon', 'twilight-city-night', 'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk',
        'dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 'dark-black-hole', 'dark-starless-sky'
    ];
    
    function getStoredTheme() {
        // Priority 1: Meta tag (most reliable)
        try {
            const meta = document.querySelector('meta[name="anki-theme"]');
            if (meta && VALID_THEMES.indexOf(meta.content) !== -1) {
                return meta.content;
            }
        } catch(e) {}
        
        // Priority 2: localStorage
        try {
            const stored = localStorage.getItem(THEME_KEY);
            if (stored && VALID_THEMES.indexOf(stored) !== -1) {
                return stored;
            }
        } catch(e) {}
        
        // Priority 3: Cookie
        try {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.indexOf(THEME_KEY + '=') === 0) {
                    const theme = cookie.substring(THEME_KEY.length + 1);
                    if (VALID_THEMES.indexOf(theme) !== -1) {
                        return theme;
                    }
                }
            }
        } catch(e) {}
        
        return DEFAULT_THEME;
    }
    
    // IMMEDIATE application (no delays, no debouncing)
    const theme = getStoredTheme();
    
    // Remove any existing theme classes
    if (document.body) {
        const classes = document.body.className.split(' ');
        const filtered = classes.filter(function(c) { return !c.startsWith('theme-'); });
        document.body.className = filtered.join(' ');
        
        // Add theme class
        document.body.classList.add('theme-' + theme);
        document.body.classList.add('card'); // Ensure card class is present
    } else {
        // Body doesn't exist yet - add to html temporarily, move to body when ready
        document.documentElement.classList.add('theme-' + theme);
        
        // Transfer to body when it exists
        const observer = new MutationObserver(function(mutations, obs) {
            if (document.body) {
                document.body.classList.add('theme-' + theme);
                document.body.classList.add('card');
                document.documentElement.classList.remove('theme-' + theme);
                obs.disconnect();
            }
        });
        
        if (document.documentElement) {
            observer.observe(document.documentElement, { childList: true });
        }
    }
})();
</script>
'''

# ============ SCRIPT 2: MAIN INTERACTIVE SCRIPT (Goes after content) =========
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

// --- NEW: Environment Detection ---
const IS_DESKTOP = (function() {
    // Desktop Anki has specific identifiers
    return typeof py !== 'undefined' || 
           (navigator.userAgent.indexOf('Anki') !== -1 && typeof Android === 'undefined');
})();

// --- NEW: Debounce Helper (Prevents excessive function calls) ---
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// --- Helper Functions ---
function applyTheme(theme) {
    // More robust theme application
    try {
        document.body.classList.forEach(c => {
            if (c.startsWith('theme-')) {
                document.body.classList.remove(c);
            }
        });
        document.body.classList.add('theme-' + theme);
        
        // Ensure base class is present
        if (!document.body.classList.contains('card')) {
            document.body.classList.add('card');
        }
    } catch (e) {
        console.warn('Theme application error:', e);
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

// --- NEW: Improved Storage Functions ---
function saveTheme(theme) {
    // Save to localStorage (works on both platforms)
    try { 
        localStorage.setItem(THEME_KEY, theme); 
    } catch(e) {
        console.warn('localStorage save failed:', e);
    }
    
    // Save to cookie (fallback)
    try {
        const expires = new Date();
        expires.setFullYear(expires.getFullYear() + 1);
        document.cookie = THEME_KEY + '=' + theme + '; expires=' + expires.toUTCString() + '; path=/; SameSite=Lax';
    } catch(e) {
        console.warn('Cookie save failed:', e);
    }
    
    // NEW: Update meta tag for Desktop persistence
    let metaTheme = document.querySelector('meta[name="anki-theme"]');
    if (!metaTheme) {
        metaTheme = document.createElement('meta');
        metaTheme.setAttribute('name', 'anki-theme');
        document.head.appendChild(metaTheme);
    }
    metaTheme.setAttribute('content', theme);
    
    // Send to Anki bridge (both platforms)
    const message = 'ankiconfig:' + THEME_KEY + ':' + theme;
    if (typeof pyBridge !== 'undefined') {
        try { pyBridge.send(message); } catch(e) {}
    } else if (typeof pycmd !== 'undefined') {
        try { pycmd(message); } catch(e) {}
    }
}

function loadTheme() {
    // NEW: Priority order optimized for Desktop
    // 1. Check meta tag first (most reliable for Desktop across sessions)
    const metaTheme = document.querySelector('meta[name="anki-theme"]');
    if (metaTheme && ALL_THEMES.includes(metaTheme.content)) {
        return metaTheme.content;
    }
    
    // 2. Check localStorage (works in-session on both)
    try {
        const localTheme = localStorage.getItem(THEME_KEY);
        if (localTheme && ALL_THEMES.includes(localTheme)) {
            return localTheme;
        }
    } catch(e) {}
    
    // 3. Check cookies (fallback)
    try {
        const name = THEME_KEY + '=';
        const decodedCookie = decodeURIComponent(document.cookie);
        const cookieArray = decodedCookie.split(';');
        for (let i = 0; i < cookieArray.length; i++) {
            let cookie = cookieArray[i].trim();
            if (cookie.indexOf(name) === 0) {
                const theme = cookie.substring(name.length, cookie.length);
                if (ALL_THEMES.includes(theme)) { 
                    return theme; 
                }
            }
        }
    } catch(e) {}
    
    // 4. Default fallback
    return 'light-full-moon';
}

// --- Main Logic (MODIFIED: Instant theme application) ---
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
    
    // INSTANT application (no debounce on user clicks)
    applyTheme(nextTheme);
    updateThemeButtons(nextTheme);
    saveTheme(nextTheme);
}

// --- MODIFIED: Split Initialization (Instant + Debounced) ---
// Instant version - for immediate updates (no FOUC)
function initThemeInstant() {
    const savedTheme = loadTheme();
    applyTheme(savedTheme);
    updateThemeButtons(savedTheme);
}

// Debounced version - for observer callbacks only (prevents crashes)
const debouncedInitTheme = debounce(function() {
    initThemeInstant();
    
    // Attach button handlers only if not already attached
    Object.keys(THEME_FAMILIES).forEach(familyKey => {
        const btn = document.getElementById('themeBtn-' + familyKey);
        if (btn && !btn.hasAttribute('data-handler-attached')) {
            btn.onclick = () => handleFamilyClick(familyKey);
            btn.setAttribute('data-handler-attached', 'true');
        }
    });
}, 100); // 100ms debounce - only for observers, not direct calls

// --- NEW: Observer Cleanup System ---
let activeObservers = [];

function cleanupObservers() {
    activeObservers.forEach(observer => {
        try {
            observer.disconnect();
        } catch(e) {}
    });
    activeObservers = [];
}

// --- NEW: Optimized Button Observer ---
function startWatchingButtons() {
    // Clean up any existing observers first
    cleanupObservers();
    
    const buttonObserver = new MutationObserver(debounce(function(mutations) {
        let shouldInit = false;
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1 && 
                    (node.classList && node.classList.contains('theme-controls') || 
                     node.querySelector && node.querySelector('.theme-controls'))) {
                    shouldInit = true;
                }
            });
        });
        if (shouldInit) {
            debouncedInitTheme();
        }
    }, 150)); // Debounced to prevent excessive triggering
    
    buttonObserver.observe(document.body, { 
        childList: true, 
        subtree: true 
    });
    activeObservers.push(buttonObserver);
}

// --- NEW: Optimized Content Observer ---
const contentObserver = new MutationObserver(debounce(function(mutations) {
    let contentChanged = mutations.some(function(mutation) {
        return mutation.target.className && 
               (mutation.target.className.includes('card') || 
                mutation.target.className.includes('content'));
    });
    if (contentChanged) {
        debouncedInitTheme();
    }
}, 150)); // Debounced

// --- Initialization Sequence (MODIFIED: Instant initial load) ---
// CRITICAL: Initial theme application is INSTANT (no debounce)
// The FOUC fix script already applied the theme, but we re-apply to ensure buttons sync
initThemeInstant();

// Setup for DOM ready state
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initThemeInstant(); // Instant on DOM ready
        startWatchingButtons();
    });
} else {
    // DOM already ready
    startWatchingButtons();
}

// Start content observer
contentObserver.observe(document.body, { 
    attributes: true, 
    attributeFilter: ['class'], 
    subtree: true 
});
activeObservers.push(contentObserver);

// Visibility change handler (INSTANT for immediate visibility, no FOUC)
document.addEventListener('visibilitychange', function() { 
    if (!document.hidden) {
        initThemeInstant(); // Instant when tab becomes visible
    }
});

// Anki card shown event (INSTANT for card transitions)
if (typeof window !== 'undefined') {
    window.addEventListener('ankiCardShown', initThemeInstant);
}

// --- NEW: Cleanup on card transition (Desktop-specific) ---
if (IS_DESKTOP) {
    // Listen for beforeunload to cleanup observers
    window.addEventListener('beforeunload', cleanupObservers);
}

// --- NEW: Emergency fallback initialization (Desktop only, INSTANT) ---
// This ensures theme loads even if other mechanisms fail
if (IS_DESKTOP) {
    setTimeout(function() {
        const currentTheme = loadTheme();
        // Only apply if no theme is currently active
        const hasTheme = Array.from(document.body.classList).some(c => c.startsWith('theme-'));
        if (!hasTheme) {
            applyTheme(currentTheme);
            updateThemeButtons(currentTheme);
        }
    }, 300);
}
</script>
'''

THEME_CSS = '''
/* ==============================================================================
# ======================  FULL THEME CSS (v19 - FINAL) =======================
# ==============================================================================
/* =============================================== */
/* Core Animations and Variables (Unified Final) */
/* =============================================== */

@keyframes glowPulse {
  0% {
    box-shadow: 0 0 8px var(--glow-color),
                0 0 16px var(--glow-color),
                0 0 24px var(--glow-color);
  }
  50% {
    box-shadow: 0 0 16px var(--glow-color),
                0 0 32px var(--glow-color),
                0 0 48px var(--glow-color);
  }
  100% {
    box-shadow: 0 0 8px var(--glow-color),
                0 0 16px var(--glow-color),
                0 0 24px var(--glow-color);
  }
}

@keyframes buttonPulse {
  0% { transform: scale(0.98); box-shadow: 0 0 4px var(--glow-color); }
  70% { transform: scale(1.02); box-shadow: 0 0 8px var(--glow-color); }
  100% { transform: scale(0.98); box-shadow: 0 0 4px var(--glow-color); }
}

@keyframes rotateClozeIcon {
  0% { transform: rotate(0deg); }
  50% { transform: rotate(60deg); }
  100% { transform: rotate(0deg); }
}

@keyframes neonTextPulse {
  0% { text-shadow: 0 0 5px var(--neon-color), 0 0 10px var(--neon-color); }
  50% { text-shadow: 0 0 10px var(--neon-color), 0 0 20px var(--neon-color); }
  100% { text-shadow: 0 0 5px var(--neon-color), 0 0 10px var(--neon-color); }
}

/* =============================================== */
/* 🌈 Rainbow Scrollbar (Global) */
/* =============================================== */
.card-container::-webkit-scrollbar-thumb,
.cloze-container::-webkit-scrollbar-thumb,
.mcq-container::-webkit-scrollbar-thumb,
.image-container::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, #60a5fa, #a78bfa, #ec4899, #f43f5e) !important;
  border-radius: 10px !important;
}

.card-container::-webkit-scrollbar-thumb:hover,
.cloze-container::-webkit-scrollbar-thumb:hover,
.mcq-container::-webkit-scrollbar-thumb:hover,
.image-container::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(to bottom, #3b82f6, #8b5cf6, #db2777, #e11d48) !important;
}

/* =============================================== */
/* 🎛️ Theme Controls UI (Keep Intact) */
/* =============================================== */
.theme-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 5px;
  background: rgba(0, 0, 0, 0.1);
  padding: 5px;
  border-radius: 30px;
  z-index: 1000;
}
.theme-family-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.4em;
  padding: 6px;
  border-radius: 50%;
  transition: all 0.2s ease;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 8px var(--glow-color);
}
.theme-family-btn:hover {
  transform: scale(1.2);
  background: rgba(255, 255, 255, 0.2);
}
.theme-family-btn.active {
  transform: scale(1.1);
  animation: pulse-mode-toggle 2.5s ease-in-out infinite;
}
.meta-header .theme-controls {
  top: 4px;
  right: 6px;
  padding: 3px;
  gap: 3px;
}
.meta-header .theme-family-btn {
  font-size: 1.3em;
  padding: 3px;
}
@keyframes pulse-mode-toggle {
  0%, 100% { transform: scale(1.1); opacity: 1; }
  50% { transform: scale(1.15); opacity: 0.95; }
}

/* =============================================== */
/* ⚡ Action Toggles ("Show..." Buttons) */
/* =============================================== */
.toggle-btn { /* <-- FIX: Changed from .action-toggle */
  animation: buttonPulse 3s infinite !important;
  border-radius: 25px !important;
  padding: 8px 12px !important;
  color: black !important;
  font-weight: bold !important;
}

/* =================================================================== */
/* =================== 🌕 FAMILY: LIGHT THEMES (FIXED v20) =========== */
/* =================================================================== */

/* 1.1: light-full-moon (Original Light – vivid purple theme) */
body.theme-light-full-moon {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
  --theme-primary: #a855f7;
  --theme-secondary: #d946ef;
  --glow-color: rgba(168, 85, 247, 0.6);
  --cloze-glow-color: #ec4899;
  --button-glow-color: #a855f7;
}

.theme-light-full-moon .card-container,
.theme-light-full-moon .mcq-container,
.theme-light-full-moon .cloze-container,
.theme-light-full-moon .image-container {
  background: #ffffff !important;
  color: #433865 !important;
  border: 2px solid rgba(226, 232, 240, 0.9) !important;
  box-shadow: 0 0 25px var(--glow-color) !important;
}

.theme-light-full-moon .cloze-container {
  background: #ffffff !important;
  color: #433865 !important;
  border: 2px solid rgba(226, 232, 240, 0.9) !important;
  box-shadow: 0 0 25px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-light-full-moon .meta-header,
.theme-light-full-moon .header,
.theme-light-full-moon .cloze-header,
.theme-light-full-moon .mcq-header,
.theme-light-full-moon .image-header {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%) !important;
  color: #ffffff !important;
}

.theme-light-full-moon .theme-family-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ffffff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-light-full-moon .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ffffff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-light-full-moon .card-type,
.theme-light-full-moon .cloze-title,
.theme-light-full-moon .mcq-title,
.theme-light-full-moon .image-title,
.theme-light-full-moon .header-text {
  color: #F5F3FF !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-light-full-moon .question-text,
.theme-light-full-moon .question-section {
  color: #581c87 !important;
  text-shadow: 0 0 1px rgba(88, 28, 135, 0.2);
}

.theme-light-full-moon .answer-text,
.theme-light-full-moon .cloze-content {
  color: #065f46 !important;
  text-shadow: 0 0 1px rgba(6, 95, 70, 0.2);
}

.theme-light-full-moon .mcq-correct-answer {
  color: #047857 !important;
  font-weight: bold !important;
  text-shadow: 0 0 5px rgba(4, 120, 87, 0.5);
}

.theme-light-full-moon .cloze {
  background: linear-gradient(135deg, #d946ef, #ec4899) !important;
  color: #F5F3FF !important;
}

/* SAFE FALLBACK: Target both -section AND -block variants */
.theme-light-full-moon .explanation-section,
.theme-light-full-moon .explanation-block {
  background: #d1fae5 !important;
  border-left: 5px solid #10b981 !important;
  color: #064e3b !important;
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.5) !important;
}

.theme-light-full-moon .correlation-section,
.theme-light-full-moon .correlation-block {
  background: #ede9fe !important;
  border-left: 5px solid #8b5cf6 !important;
  color: #4c1d95 !important;
  box-shadow: 0 0 15px rgba(139, 92, 246, 0.5) !important;
}

.theme-light-full-moon .extra-info,
.theme-light-full-moon .extra-block {
  background: #fff7ed !important;
  border-left: 5px solid #f97316 !important;
  color: #7c2d12 !important;
  box-shadow: 0 0 15px rgba(249, 115, 22, 0.5) !important;
}

.theme-light-full-moon .comments-block,
.theme-light-full-moon .comments-section {
  background: #fff7ed !important;
  border-left: 5px solid #f97316 !important;
  color: #7c2d12 !important;
  box-shadow: 0 0 15px rgba(249, 115, 22, 0.5) !important;
}

/* 1.2: light-waning-gibbous (Sepia / Paper) */
body.theme-light-waning-gibbous {
  background: #fdf6e3 !important;
  --theme-primary: #cb4b16;
  --theme-secondary: #dc322f;
  --glow-color: rgba(203, 75, 22, 0.5);
  --cloze-glow-color: #2aa198;
  --button-glow-color: #cb4b16;
}

.theme-light-waning-gibbous .card-container,
.theme-light-waning-gibbous .mcq-container,
.theme-light-waning-gibbous .cloze-container,
.theme-light-waning-gibbous .image-container {
  background: #fefcf7 !important;
  color: #586e75 !important;
  border: 2px solid rgba(238, 232, 213, 0.9) !important;
  box-shadow: 0 0 25px var(--glow-color) !important;
}

.theme-light-waning-gibbous .cloze-container {
  background: #fefcf7 !important;
  color: #586e75 !important;
  border: 2px solid rgba(238, 232, 213, 0.9) !important;
  box-shadow: 0 0 25px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-light-waning-gibbous .meta-header,
.theme-light-waning-gibbous .header,
.theme-light-waning-gibbous .cloze-header,
.theme-light-waning-gibbous .mcq-header,
.theme-light-waning-gibbous .image-header {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%) !important;
  color: #fff !important;
}

.theme-light-waning-gibbous .theme-family-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #fff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-light-waning-gibbous .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #fff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-light-waning-gibbous .card-type,
.theme-light-waning-gibbous .cloze-title,
.theme-light-waning-gibbous .mcq-title,
.theme-light-waning-gibbous .image-title,
.theme-light-waning-gibbous .header-text {
  color: #fdf6e3 !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-light-waning-gibbous .question-text,
.theme-light-waning-gibbous .question-section {
  color: #6c6f00 !important;
  text-shadow: 0 0 1px rgba(108, 111, 0, 0.2);
}

.theme-light-waning-gibbous .answer-text,
.theme-light-waning-gibbous .cloze-content {
  color: #1d6998 !important;
  text-shadow: 0 0 1px rgba(29, 105, 152, 0.2);
}

.theme-light-waning-gibbous .mcq-correct-answer {
  color: #145374 !important;
  font-weight: bold !important;
  text-shadow: 0 0 5px rgba(20, 83, 116, 0.5);
}

.theme-light-waning-gibbous .cloze {
  background: linear-gradient(135deg, #2aa198, #268bd2) !important;
  color: #fdf6e3 !important;
}

.theme-light-waning-gibbous .explanation-section,
.theme-light-waning-gibbous .explanation-block {
  background: #fefae0 !important;
  border-left: 5px solid #859900 !important;
  color: #556b2f !important;
  box-shadow: 0 0 15px rgba(133, 153, 0, 0.4) !important;
}

.theme-light-waning-gibbous .correlation-section,
.theme-light-waning-gibbous .correlation-block {
  background: #e3f2fd !important;
  border-left: 5px solid #268bd2 !important;
  color: #0f4c81 !important;
  box-shadow: 0 0 15px rgba(38, 139, 210, 0.4) !important;
}

.theme-light-waning-gibbous .extra-info,
.theme-light-waning-gibbous .extra-block {
  background: #fdecea !important;
  border-left: 5px solid #dc322f !important;
  color: #7b1f1b !important;
  box-shadow: 0 0 15px rgba(220, 50, 47, 0.5) !important;
}

.theme-light-waning-gibbous .comments-block,
.theme-light-waning-gibbous .comments-section {
  background: #fdecea !important;
  border-left: 5px solid #dc322f !important;
  color: #7b1f1b !important;
  box-shadow: 0 0 15px rgba(220, 50, 47, 0.5) !important;
}

/* 1.3: light-last-quarter (Cool Mint) */
body.theme-light-last-quarter {
  background: linear-gradient(135deg, #e0f2f1, #b2dfdb) !important;
  --theme-primary: #00796b;
  --theme-secondary: #009688;
  --glow-color: rgba(0, 121, 107, 0.6);
  --cloze-glow-color: #00897b;
  --button-glow-color: #00796b;
}

.theme-light-last-quarter .card-container,
.theme-light-last-quarter .mcq-container,
.theme-light-last-quarter .cloze-container,
.theme-light-last-quarter .image-container {
  background: #ffffff !important;
  color: #004d40 !important;
  border: 2px solid rgba(128, 203, 196, 0.9) !important;
  box-shadow: 0 0 25px var(--glow-color) !important;
}

.theme-light-last-quarter .cloze-container {
  background: #ffffff !important;
  color: #004d40 !important;
  border: 2px solid rgba(128, 203, 196, 0.9) !important;
  box-shadow: 0 0 25px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-light-last-quarter .meta-header,
.theme-light-last-quarter .header,
.theme-light-last-quarter .cloze-header,
.theme-light-last-quarter .mcq-header,
.theme-light-last-quarter .image-header {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%) !important;
  color: #fff !important;
}

.theme-light-last-quarter .theme-family-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #fff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-light-last-quarter .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #fff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-light-last-quarter .card-type,
.theme-light-last-quarter .cloze-title,
.theme-light-last-quarter .mcq-title,
.theme-light-last-quarter .image-title,
.theme-light-last-quarter .header-text {
  color: #E0F2F1 !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-light-last-quarter .question-text,
.theme-light-last-quarter .question-section {
  color: #00695c !important;
  text-shadow: 0 0 1px rgba(0, 105, 92, 0.2);
}

.theme-light-last-quarter .answer-text,
.theme-light-last-quarter .cloze-content {
  color: #1a237e !important;
  text-shadow: 0 0 1px rgba(26, 35, 126, 0.2);
}

.theme-light-last-quarter .mcq-correct-answer {
  color: #2a3686 !important;
  font-weight: bold !important;
  text-shadow: 0 0 5px rgba(42, 54, 134, 0.5);
}

.theme-light-last-quarter .cloze {
  background: linear-gradient(135deg, #00897b, #4db6ac) !important;
  color: #fff !important;
}

.theme-light-last-quarter .explanation-section,
.theme-light-last-quarter .explanation-block {
  background: #e8f5e9 !important;
  border-left: 5px solid #4caf50 !important;
  color: #1e4620 !important;
  box-shadow: 0 0 15px rgba(76, 175, 80, 0.5) !important;
}

.theme-light-last-quarter .correlation-section,
.theme-light-last-quarter .correlation-block {
  background: #e3f2fd !important;
  border-left: 5px solid #2196f3 !important;
  color: #0d47a1 !important;
  box-shadow: 0 0 15px rgba(33, 150, 243, 0.5) !important;
}

.theme-light-last-quarter .extra-info,
.theme-light-last-quarter .extra-block {
  background: #fbe9e7 !important;
  border-left: 5px solid #ff5722 !important;
  color: #c33b0e !important;
  box-shadow: 0 0 15px rgba(255, 87, 34, 0.5) !important;
}

.theme-light-last-quarter .comments-block,
.theme-light-last-quarter .comments-section {
  background: #fbe9e7 !important;
  border-left: 5px solid #ff5722 !important;
  color: #c33b0e !important;
  box-shadow: 0 0 15px rgba(255, 87, 34, 0.5) !important;
}

/* 1.4: light-waning-crescent (Soft Lavender) */
body.theme-light-waning-crescent {
  background: #f3e5f5 !important;
  --theme-primary: #8e24aa;
  --theme-secondary: #ab47bc;
  --glow-color: rgba(142, 36, 170, 0.6);
  --cloze-glow-color: #7b1fa2;
  --button-glow-color: #8e24aa;
}

.theme-light-waning-crescent .card-container,
.theme-light-waning-crescent .mcq-container,
.theme-light-waning-crescent .cloze-container,
.theme-light-waning-crescent .image-container {
  background: #faf5fb !important;
  color: #4a148c !important;
  border: 2px solid rgba(206, 147, 216, 0.9) !important;
  box-shadow: 0 0 25px var(--glow-color) !important;
}

.theme-light-waning-crescent .cloze-container {
  background: #faf5fb !important;
  color: #4a148c !important;
  border: 2px solid rgba(206, 147, 216, 0.9) !important;
  box-shadow: 0 0 25px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-light-waning-crescent .meta-header,
.theme-light-waning-crescent .header,
.theme-light-waning-crescent .cloze-header,
.theme-light-waning-crescent .mcq-header,
.theme-light-waning-crescent .image-header {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%) !important;
  color: #fff !important;
}

.theme-light-waning-crescent .theme-family-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #fff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-light-waning-crescent .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #fff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-light-waning-crescent .card-type,
.theme-light-waning-crescent .cloze-title,
.theme-light-waning-crescent .mcq-title,
.theme-light-waning-crescent .image-title,
.theme-light-waning-crescent .header-text {
  color: #F3E5F5 !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-light-waning-crescent .question-text,
.theme-light-waning-crescent .question-section {
  color: #6a1b9a !important;
  text-shadow: 0 0 1px rgba(106, 27, 154, 0.2);
}

.theme-light-waning-crescent .answer-text,
.theme-light-waning-crescent .cloze-content {
  color: #ad1457 !important;
  text-shadow: 0 0 1px rgba(173, 20, 87, 0.2);
}

.theme-light-waning-crescent .mcq-correct-answer {
  color: #880e4f !important;
  font-weight: bold !important;
  text-shadow: 0 0 5px rgba(136, 14, 79, 0.5);
}

.theme-light-waning-crescent .cloze {
  background: linear-gradient(135deg, #7b1fa2, #9c27b0) !important;
  color: #fff !important;
}

.theme-light-waning-crescent .explanation-section,
.theme-light-waning-crescent .explanation-block {
  background: #fce4ec !important;
  border-left: 5px solid #ec407a !important;
  color: #880e4f !important;
  box-shadow: 0 0 15px rgba(236, 64, 122, 0.5) !important;
}

.theme-light-waning-crescent .correlation-section,
.theme-light-waning-crescent .correlation-block {
  background: #e3f2fd !important;
  border-left: 5px solid #03a9f4 !important;
  color: #01579b !important;
  box-shadow: 0 0 15px rgba(3, 169, 244, 0.5) !important;
}

.theme-light-waning-crescent .extra-info,
.theme-light-waning-crescent .extra-block {
  background: #fff8e1 !important;
  border-left: 5px solid #fbc02d !important;
  color: #f57f17 !important;
  box-shadow: 0 0 15px rgba(251, 192, 45, 0.5) !important;
}

.theme-light-waning-crescent .comments-block,
.theme-light-waning-crescent .comments-section {
  background: #fff8e1 !important;
  border-left: 5px solid #fbc02d !important;
  color: #f57f17 !important;
  box-shadow: 0 0 15px rgba(251, 192, 45, 0.5) !important;
}

/* 1.5: light-new-moon (Minimalist White) */
body.theme-light-new-moon {
  background: #f8f9fa !important;
  --theme-primary: #343a40;
  --theme-secondary: #495057;
  --glow-color: rgba(52, 58, 64, 0.5);
  --cloze-glow-color: #007bff;
  --button-glow-color: #343a40;
}

.theme-light-new-moon .card-container,
.theme-light-new-moon .mcq-container,
.theme-light-new-moon .cloze-container,
.theme-light-new-moon .image-container {
  background: #ffffff !important;
  color: #212529 !important;
  border: 2px solid rgba(222, 226, 230, 0.9) !important;
  box-shadow: 0 0 25px var(--glow-color) !important;
}

.theme-light-new-moon .cloze-container {
  background: #ffffff !important;
  color: #212529 !important;
  border: 2px solid rgba(222, 226, 230, 0.9) !important;
  box-shadow: 0 0 25px var(--glow-color) !important;
  animation: glowPulse 2s infinite !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-light-new-moon .meta-header,
.theme-light-new-moon .header,
.theme-light-new-moon .cloze-header,
.theme-light-new-moon .mcq-header,
.theme-light-new-moon .image-header {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%) !important;
  color: #fff !important;
}

.theme-light-new-moon .theme-family-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #fff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-light-new-moon .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #fff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-light-new-moon .card-type,
.theme-light-new-moon .cloze-title,
.theme-light-new-moon .mcq-title,
.theme-light-new-moon .image-title,
.theme-light-new-moon .header-text {
  color: #f8f9fa !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-light-new-moon .question-text,
.theme-light-new-moon .question-section {
  color: #0056b3 !important;
  text-shadow: 0 0 1px rgba(0, 86, 179, 0.2);
}

.theme-light-new-moon .answer-text,
.theme-light-new-moon .cloze-content {
  color: #155724 !important;
  text-shadow: 0 0 1px rgba(21, 87, 36, 0.2);
}

.theme-light-new-moon .mcq-correct-answer {
  color: #0c4128 !important;
  font-weight: bold !important;
  text-shadow: 0 0 5px rgba(12, 65, 40, 0.5);
}

.theme-light-new-moon .cloze {
  background: linear-gradient(135deg, #007bff, #0056b3) !important;
  color: #fff !important;
}

.theme-light-new-moon .explanation-section,
.theme-light-new-moon .explanation-block {
  background: #e9ecef !important;
  border-left: 5px solid #6c757d !important;
  color: #383d41 !important;
  box-shadow: 0 0 15px rgba(108, 117, 125, 0.5) !important;
}

.theme-light-new-moon .correlation-section,
.theme-light-new-moon .correlation-block {
  background: #f1f3f5 !important;
  border-left: 5px solid #343a40 !important;
  color: #212529 !important;
  box-shadow: 0 0 15px rgba(52, 58, 64, 0.5) !important;
}

.theme-light-new-moon .extra-info,
.theme-light-new-moon .extra-block {
  background: #fff3cd !important;
  border-left: 5px solid #f97316 !important;
  color: #856404 !important;
  box-shadow: 0 0 15px rgba(249, 115, 22, 0.5) !important;
}

.theme-light-new-moon .comments-block,
.theme-light-new-moon .comments-section {
  background: #fff3cd !important;
  border-left: 5px solid #f97316 !important;
  color: #856404 !important;
  box-shadow: 0 0 15px rgba(249, 115, 22, 0.5) !important;
}

.theme-light-new-moon .theme-family-btn,
.theme-light-new-moon .toggle-button {
  color: #fff !important;
  background: linear-gradient(135deg, #343a40, #495057) !important;
  box-shadow: 0 0 18px rgba(52, 58, 64, 0.8) !important;
}

/* =================================================================== */
/* =================== ☀️ FAMILY: NORD THEMES (FIXED v21) =========== */
/* =================================================================== */

.theme-nord-bright-sun .correct-answer,
.theme-nord-overcast-day .correct-answer,
.theme-nord-stormy-sky .correct-answer,
.theme-nord-aurora .correct-answer,
.theme-nord-polar-night .correct-answer,
.theme-balanced-star .correct-answer,
.theme-balanced-nebula .correct-answer,
.theme-balanced-supernova .correct-answer,
.theme-balanced-galaxy .correct-answer,
.theme-balanced-comet .correct-answer,
.theme-twilight-crescent-moon .correct-answer,
.theme-twilight-city-night .correct-answer,
.theme-twilight-deep-forest .correct-answer,
.theme-twilight-moonlit-ocean .correct-answer,
.theme-twilight-dusk .correct-answer,
.theme-dark-saturn .correct-answer,
.theme-dark-mars-rover .correct-answer,
.theme-dark-neptune-deep .correct-answer,
.theme-dark-black-hole .correct-answer,
.theme-dark-starless-sky .correct-answer {
  background: linear-gradient(135deg, #064e3b 0%, #134e4a 100%) !important;
  border: 1px solid #14b8a6;
  box-shadow: 0 0 15px rgba(20, 184, 166, 0.3);
}

.theme-nord-bright-sun .custom-image-question,
.theme-nord-overcast-day .custom-image-question,
.theme-nord-stormy-sky .custom-image-question,
.theme-nord-aurora .custom-image-question,
.theme-nord-polar-night .custom-image-question {
  background: #2E3440 !important;
  border-color: #5E81AC !important;
  color: #ECEFF4 !important;
}

/* 2.1: nord-bright-sun (Vibrant Nord) */
body.theme-nord-bright-sun {
  background: linear-gradient(to top, #5eead4 0%, #1e3a8a 100%) !important;
  --theme-primary: #5eead4;
  --theme-secondary: #3b82f6;
  --glow-color: rgba(94, 234, 212, 0.4);
  --cloze-glow-color: #3b82f6;
  --button-glow-color: #5eead4;
}

.theme-nord-bright-sun .card-container,
.theme-nord-bright-sun .mcq-container,
.theme-nord-bright-sun .cloze-container,
.theme-nord-bright-sun .image-container {
  background: #1e293b !important;
  color: #e0f2fe !important;
  border: 2px solid rgba(148, 163, 184, 0.8) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-nord-bright-sun .cloze-container {
  background: #1e293b !important;
  color: #e0f2fe !important;
  border: 2px solid rgba(148, 163, 184, 0.8) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-nord-bright-sun .meta-header,
.theme-nord-bright-sun .header,
.theme-nord-bright-sun .cloze-header,
.theme-nord-bright-sun .mcq-header,
.theme-nord-bright-sun .image-header {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%) !important;
  color: #0f172a !important;
  border-bottom: 1px solid rgba(94, 234, 212, 0.3) !important;
}

.theme-nord-bright-sun .theme-family-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #0f172a !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-nord-bright-sun .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #0f172a !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-nord-bright-sun .card-type,
.theme-nord-bright-sun .cloze-title,
.theme-nord-bright-sun .mcq-title,
.theme-nord-bright-sun .image-title,
.theme-nord-bright-sun .header-text {
  color: #e0f2fe !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-nord-bright-sun .question-text,
.theme-nord-bright-sun .question-section {
  color: #93c5fd !important;
  text-shadow: 0 0 2px rgba(147, 197, 253, 0.3);
}

.theme-nord-bright-sun .answer-text,
.theme-nord-bright-sun .cloze-content {
  color: #99f6e4 !important;
  text-shadow: 0 0 2px rgba(153, 246, 228, 0.3);
}

.theme-nord-bright-sun .mcq-correct-answer {
  color: #0A3D39 !important;
  font-weight: bold !important;
  text-shadow: 0 0 5px rgba(167, 243, 208, 0.7);
}

.theme-nord-bright-sun .cloze {
  background: linear-gradient(135deg, #3b82f6, #5eead4) !important;
  color: #0f172a !important;
}

.theme-nord-bright-sun .explanation-section,
.theme-nord-bright-sun .explanation-block {
  background: rgba(14, 165, 233, 0.15) !important;
  border-left: 5px solid #3b82f6 !important;
  color: #bfdbfe !important;
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.4) !important;
}

.theme-nord-bright-sun .correlation-section,
.theme-nord-bright-sun .correlation-block {
  background: rgba(56, 189, 248, 0.15) !important;
  border-left: 5px solid #38bdf8 !important;
  color: #bae6fd !important;
  box-shadow: 0 0 15px rgba(56, 189, 248, 0.4) !important;
}

.theme-nord-bright-sun .extra-info,
.theme-nord-bright-sun .extra-block,
.theme-nord-bright-sun .comments-block,
.theme-nord-bright-sun .comments-section {
  background: rgba(6, 182, 212, 0.15) !important;
  border-left: 5px solid #06b6d4 !important;
  color: #99f6e4 !important;
  box-shadow: 0 0 15px rgba(6, 182, 212, 0.4) !important;
}

/* 2.2: nord-overcast-day (Softer Nord) */
body.theme-nord-overcast-day {
  background: linear-gradient(135deg, #c7d2fe 0%, #94a3b8 100%) !important;
  --theme-primary: #60a5fa;
  --theme-secondary: #3b82f6;
  --glow-color: rgba(96, 165, 250, 0.3);
  --cloze-glow-color: #3b82f6;
  --button-glow-color: #60a5fa;
}

.theme-nord-overcast-day .card-container,
.theme-nord-overcast-day .mcq-container,
.theme-nord-overcast-day .cloze-container,
.theme-nord-overcast-day .image-container {
  background: #f1f5f9 !important;
  color: #0f172a !important;
  border: 2px solid rgba(148, 163, 184, 0.8) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-nord-overcast-day .cloze-container {
  background: #f1f5f9 !important;
  color: #0f172a !important;
  border: 2px solid rgba(148, 163, 184, 0.8) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-nord-overcast-day .meta-header,
.theme-nord-overcast-day .header,
.theme-nord-overcast-day .cloze-header,
.theme-nord-overcast-day .mcq-header,
.theme-nord-overcast-day .image-header {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%) !important;
  color: #ffffff !important;
  border-bottom: 1px solid rgba(96, 165, 250, 0.3) !important;
}

.theme-nord-overcast-day .theme-family-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ffffff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-nord-overcast-day .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ffffff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-nord-overcast-day .card-type,
.theme-nord-overcast-day .cloze-title,
.theme-nord-overcast-day .mcq-title,
.theme-nord-overcast-day .image-title,
.theme-nord-overcast-day .header-text {
  color: #1e3a8a !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-nord-overcast-day .question-text,
.theme-nord-overcast-day .question-section {
  color: #1e40af !important;
  text-shadow: 0 0 1px rgba(30, 64, 175, 0.2);
}

.theme-nord-overcast-day .answer-text,
.theme-nord-overcast-day .cloze-content {
  color: #2563eb !important;
  text-shadow: 0 0 1px rgba(37, 99, 235, 0.2);
}

.theme-nord-overcast-day .mcq-correct-answer {
  color: #1d4ed8 !important;
  font-weight: bold !important;
  text-shadow: 0 0 5px rgba(29, 78, 216, 0.5);
}

.theme-nord-overcast-day .cloze {
  background: linear-gradient(135deg, #3b82f6, #1e3a8a) !important;
  color: #f8fafc !important;
}

.theme-nord-overcast-day .explanation-section,
.theme-nord-overcast-day .explanation-block {
  background: rgba(191, 219, 254, 0.4) !important;
  border-left: 5px solid #60a5fa !important;
  color: #1e40af !important;
  box-shadow: 0 0 15px rgba(96, 165, 250, 0.4) !important;
}

.theme-nord-overcast-day .correlation-section,
.theme-nord-overcast-day .correlation-block {
  background: rgba(219, 234, 254, 0.4) !important;
  border-left: 5px solid #3b82f6 !important;
  color: #1e3a8a !important;
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.4) !important;
}

.theme-nord-overcast-day .extra-info,
.theme-nord-overcast-day .extra-block,
.theme-nord-overcast-day .comments-block,
.theme-nord-overcast-day .comments-section {
  background: rgba(147, 197, 253, 0.4) !important;
  border-left: 5px solid #2563eb !important;
  color: #1e3a8a !important;
  box-shadow: 0 0 15px rgba(37, 99, 235, 0.4) !important;
}

/* 2.3: nord-stormy-sky (Gold on Navy) */
body.theme-nord-stormy-sky {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
  --theme-primary: #fbbf24;
  --theme-secondary: #f59e0b;
  --glow-color: rgba(251, 191, 36, 0.3);
  --cloze-glow-color: #1e3a8a;
  --button-glow-color: #fbbf24;
}

.theme-nord-stormy-sky .card-container,
.theme-nord-stormy-sky .mcq-container,
.theme-nord-stormy-sky .cloze-container,
.theme-nord-stormy-sky .image-container {
  background: #1e293b !important;
  color: #fef9c3 !important;
  border: 2px solid rgba(71, 85, 105, 0.8) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-nord-stormy-sky .cloze-container {
  background: #1e293b !important;
  color: #fef9c3 !important;
  border: 2px solid rgba(71, 85, 105, 0.8) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-nord-stormy-sky .meta-header,
.theme-nord-stormy-sky .header,
.theme-nord-stormy-sky .cloze-header,
.theme-nord-stormy-sky .mcq-header,
.theme-nord-stormy-sky .image-header {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%) !important;
  color: #422006 !important;
  border-bottom: 1px solid rgba(251, 191, 36, 0.3) !important;
}

.theme-nord-stormy-sky .theme-family-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #422006 !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-nord-stormy-sky .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #422006 !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-nord-stormy-sky .card-type,
.theme-nord-stormy-sky .cloze-title,
.theme-nord-stormy-sky .mcq-title,
.theme-nord-stormy-sky .image-title,
.theme-nord-stormy-sky .header-text {
  color: #fef9c3 !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-nord-stormy-sky .question-text,
.theme-nord-stormy-sky .question-section {
  color: #fcd34d !important;
  text-shadow: 0 0 2px rgba(252, 211, 77, 0.3);
}

.theme-nord-stormy-sky .answer-text,
.theme-nord-stormy-sky .cloze-content {
  color: #93c5fd !important;
  text-shadow: 0 0 2px rgba(147, 197, 253, 0.3);
}

.theme-nord-stormy-sky .mcq-correct-answer {
  color: #012E46 !important;
  font-weight: bold !important;
  text-shadow: 0 0 5px rgba(186, 230, 253, 0.7);
}

.theme-nord-stormy-sky .cloze {
  background: linear-gradient(135deg, #1e3a8a, #3b82f6) !important;
  color: #eff6ff !important;
}

.theme-nord-stormy-sky .explanation-section,
.theme-nord-stormy-sky .explanation-block {
  background: rgba(147, 197, 253, 0.1) !important;
  border-left: 5px solid #60a5fa !important;
  color: #bfdbfe !important;
  box-shadow: 0 0 15px rgba(96, 165, 250, 0.3) !important;
}

.theme-nord-stormy-sky .correlation-section,
.theme-nord-stormy-sky .correlation-block {
  background: rgba(251, 191, 36, 0.1) !important;
  border-left: 5px solid #fbbf24 !important;
  color: #fef08a !important;
  box-shadow: 0 0 15px rgba(251, 191, 36, 0.3) !important;
}

.theme-nord-stormy-sky .extra-info,
.theme-nord-stormy-sky .extra-block,
.theme-nord-stormy-sky .comments-block,
.theme-nord-stormy-sky .comments-section {
  background: rgba(248, 113, 113, 0.1) !important;
  border-left: 5px solid #f87171 !important;
  color: #fecaca !important;
  box-shadow: 0 0 15px rgba(248, 113, 113, 0.3) !important;
}

/* 2.4: nord-aurora (Teal on Charcoal) */
body.theme-nord-aurora {
  background: linear-gradient(-45deg, #0f172a, #020617, #0f172a) !important;
  --theme-primary: #10b981;
  --theme-secondary: #14b8a6;
  --glow-color: rgba(16, 185, 129, 0.3);
  --cloze-glow-color: #0d9488;
  --button-glow-color: #10b981;
}

.theme-nord-aurora .card-container,
.theme-nord-aurora .mcq-container,
.theme-nord-aurora .cloze-container,
.theme-nord-aurora .image-container {
  background: #0f172a !important;
  color: #a5f3fc !important;
  border: 2px solid rgba(45, 55, 72, 0.8) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-nord-aurora .cloze-container {
  background: #0f172a !important;
  color: #a5f3fc !important;
  border: 2px solid rgba(45, 55, 72, 0.8) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-nord-aurora .meta-header,
.theme-nord-aurora .header,
.theme-nord-aurora .cloze-header,
.theme-nord-aurora .mcq-header,
.theme-nord-aurora .image-header {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%) !important;
  color: #ffffff !important;
  border-bottom: 1px solid rgba(16, 185, 129, 0.3) !important;
}

.theme-nord-aurora .theme-family-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ffffff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-nord-aurora .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ffffff !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-nord-aurora .card-type,
.theme-nord-aurora .cloze-title,
.theme-nord-aurora .mcq-title,
.theme-nord-aurora .image-title,
.theme-nord-aurora .header-text {
  color: #a5f3fc !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-nord-aurora .question-text,
.theme-nord-aurora .question-section {
  color: #6ee7b7 !important;
  text-shadow: 0 0 2px rgba(110, 231, 183, 0.3);
}

.theme-nord-aurora .answer-text,
.theme-nord-aurora .cloze-content {
  color: #5eead4 !important;
  text-shadow: 0 0 2px rgba(94, 234, 212, 0.3);
}

.theme-nord-aurora .mcq-correct-answer {
  color: #07403A !important;
  font-weight: bold !important;
  text-shadow: 0 0 5px rgba(167, 243, 208, 0.7);
}

.theme-nord-aurora .cloze {
  background: linear-gradient(135deg, #0d9488, #10b981) !important;
  color: #f0fdfa !important;
}

.theme-nord-aurora .explanation-section,
.theme-nord-aurora .explanation-block {
  background: rgba(16, 185, 129, 0.1) !important;
  border-left: 5px solid #10b981 !important;
  color: #99f6e4 !important;
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.3) !important;
}

.theme-nord-aurora .correlation-section,
.theme-nord-aurora .correlation-block {
  background: rgba(139, 92, 246, 0.1) !important;
  border-left: 5px solid #8b5cf6 !important;
  color: #ddd6fe !important;
  box-shadow: 0 0 15px rgba(139, 92, 246, 0.3) !important;
}

.theme-nord-aurora .extra-info,
.theme-nord-aurora .extra-block,
.theme-nord-aurora .comments-block,
.theme-nord-aurora .comments-section {
  background: rgba(236, 72, 153, 0.1) !important;
  border-left: 5px solid #ec4899 !important;
  color: #fbcfe8 !important;
  box-shadow: 0 0 15px rgba(236, 72, 153, 0.3) !important;
}

/* 2.5: nord-polar-night (True Nord) */
body.theme-nord-polar-night {
  background: #2e3440 !important;
  --theme-primary: #5e81ac;
  --theme-secondary: #81a1c1;
  --glow-color: rgba(94, 129, 172, 0.3);
  --cloze-glow-color: #81a1c1;
  --button-glow-color: #5e81ac;
}

.theme-nord-polar-night .card-container,
.theme-nord-polar-night .mcq-container,
.theme-nord-polar-night .cloze-container,
.theme-nord-polar-night .image-container {
  background: #3b4252 !important;
  color: #eceff4 !important;
  border: 2px solid rgba(67, 76, 94, 0.8) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-nord-polar-night .cloze-container {
  background: #3b4252 !important;
  color: #eceff4 !important;
  border: 2px solid rgba(67, 76, 94, 0.8) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-nord-polar-night .meta-header,
.theme-nord-polar-night .header,
.theme-nord-polar-night .cloze-header,
.theme-nord-polar-night .mcq-header,
.theme-nord-polar-night .image-header {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%) !important;
  color: #eceff4 !important;
  border-bottom: 1px solid rgba(94, 129, 172, 0.3) !important;
}

.theme-nord-polar-night .theme-family-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #eceff4 !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-nord-polar-night .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #eceff4 !important;
  box-shadow: 0 0 18px var(--button-glow-color) !important;
}

.theme-nord-polar-night .card-type,
.theme-nord-polar-night .cloze-title,
.theme-nord-polar-night .mcq-title,
.theme-nord-polar-night .image-title,
.theme-nord-polar-night .header-text {
  color: #eceff4 !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-nord-polar-night .question-text,
.theme-nord-polar-night .question-section {
  color: #81a1c1 !important;
  text-shadow: 0 0 2px rgba(129, 161, 193, 0.3);
}

.theme-nord-polar-night .answer-text,
.theme-nord-polar-night .cloze-content {
  color: #88c0d0 !important;
  text-shadow: 0 0 2px rgba(136, 192, 208, 0.3);
}

.theme-nord-polar-night .mcq-correct-answer {
  color: #274008 !important;
  font-weight: bold !important;
  text-shadow: 0 0 5px rgba(163, 190, 140, 0.7);
}

.theme-nord-polar-night .cloze {
  background: linear-gradient(135deg, #5e81ac, #81a1c1) !important;
  color: #2e3440 !important;
}

.theme-nord-polar-night .explanation-section,
.theme-nord-polar-night .explanation-block {
  background: rgba(94, 129, 172, 0.1) !important;
  border-left: 5px solid #5e81ac !important;
  color: #eceff4 !important;
  box-shadow: 0 0 15px rgba(94, 129, 172, 0.3) !important;
}

.theme-nord-polar-night .correlation-section,
.theme-nord-polar-night .correlation-block {
  background: rgba(163, 190, 140, 0.1) !important;
  border-left: 5px solid #a3be8c !important;
  color: #d8dee9 !important;
  box-shadow: 0 0 15px rgba(163, 190, 140, 0.3) !important;
}

.theme-nord-polar-night .extra-info,
.theme-nord-polar-night .extra-block,
.theme-nord-polar-night .comments-block,
.theme-nord-polar-night .comments-section {
  background: rgba(180, 142, 173, 0.1) !important;
  border-left: 5px solid #b48ead !important;
  color: #eceff4 !important;
  box-shadow: 0 0 15px rgba(180, 142, 173, 0.3) !important;
}

/* =================================================================== */
/* ================== ⭐ FAMILY: BALANCED THEMES (FIXED v22) ========== */
/* =================================================================== */

.theme-balanced-star .custom-image-question,
.theme-balanced-nebula .custom-image-question,
.theme-balanced-supernova .custom-image-question,
.theme-balanced-galaxy .custom-image-question,
.theme-balanced-comet .custom-image-question {
  background: #111827 !important;
  border-color: #4F46E5 !important;
  color: #D1D5DB !important;
}

/* 3.1: balanced-star (Original Balanced) */
body.theme-balanced-star {
  background: linear-gradient(to right, #434343 0%, #000000 100%) !important;
  --theme-primary: #a18cd1;
  --theme-secondary: #fbc2eb;
  --glow-color: rgba(161, 140, 209, 0.33);
  --cloze-glow-color: #a18cd1;
  --button-glow-color: #a18cd1;
}

.theme-balanced-star .card-container,
.theme-balanced-star .mcq-container,
.theme-balanced-star .cloze-container,
.theme-balanced-star .image-container {
  background: #374151 !important;
  color: #D1D5DB !important;
  border: 2px solid rgba(156, 163, 175, 0.9) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-balanced-star .cloze-container {
  background: #374151 !important;
  color: #D1D5DB !important;
  border: 2px solid rgba(156, 163, 175, 0.9) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-balanced-star .meta-header,
.theme-balanced-star .header,
.theme-balanced-star .cloze-header,
.theme-balanced-star .mcq-header,
.theme-balanced-star .image-header {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%) !important;
  border-bottom: 1px solid rgba(161, 140, 209, 0.25) !important;
  color: #fff !important;
}

.theme-balanced-star .theme-family-btn,
.theme-balanced-star .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #fff !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-balanced-star .card-type,
.theme-balanced-star .cloze-title,
.theme-balanced-star .mcq-title,
.theme-balanced-star .image-title,
.theme-balanced-star .header-text {
  color: #3730A3 !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-balanced-star .question-text,
.theme-balanced-star .question-section {
  color: #FBCFE8 !important;
  text-shadow: 0 0 2px rgba(251, 207, 232, 0.25);
}

.theme-balanced-star .answer-text,
.theme-balanced-star .cloze-content {
  color: #C4B5FD !important;
  text-shadow: 0 0 2px rgba(196, 181, 253, 0.2);
}

.theme-balanced-star .mcq-correct-answer {
  color: #5834F9 !important;
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(221, 214, 254, 0.45);
}

.theme-balanced-star .cloze {
  background: linear-gradient(135deg, #a18cd1, #fbc2eb) !important;
  color: #4B5563 !important;
}

.theme-balanced-star .explanation-section,
.theme-balanced-star .explanation-block {
  background: rgba(196, 181, 253, 0.08) !important;
  border-left: 5px solid #A78BFA !important;
  color: #DDD6FE !important;
  box-shadow: 0 0 15px rgba(167, 139, 250, 0.3) !important;
}

.theme-balanced-star .correlation-section,
.theme-balanced-star .correlation-block {
  background: rgba(251, 207, 232, 0.06) !important;
  border-left: 5px solid #F472B6 !important;
  color: #FBCFE8 !important;
  box-shadow: 0 0 15px rgba(244, 114, 182, 0.3) !important;
}

.theme-balanced-star .extra-info,
.theme-balanced-star .extra-block,
.theme-balanced-star .comments-block {
  background: rgba(134, 239, 172, 0.06) !important;
  border-left: 5px solid #4ADE80 !important;
  color: #BBF7D0 !important;
  box-shadow: 0 0 15px rgba(74, 222, 128, 0.3) !important;
}

/* 3.2: balanced-nebula (Deep Purples and Pinks) */
body.theme-balanced-nebula {
  background: linear-gradient(135deg, #23074d 0%, #cc5333 100%) !important;
  --theme-primary: #BE185D;
  --theme-secondary: #E11D48;
  --glow-color: rgba(190, 24, 93, 0.32);
  --cloze-glow-color: #9D174D;
  --button-glow-color: #BE185D;
}

.theme-balanced-nebula .card-container,
.theme-balanced-nebula .mcq-container,
.theme-balanced-nebula .cloze-container,
.theme-balanced-nebula .image-container {
  background: #1e1838 !important;
  color: #D9CFFC !important;
  border: 2px solid rgba(109, 40, 217, 0.85) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-balanced-nebula .cloze-container {
  background: #1e1838 !important;
  color: #D9CFFC !important;
  border: 2px solid rgba(109, 40, 217, 0.85) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-balanced-nebula .meta-header,
.theme-balanced-nebula .header,
.theme-balanced-nebula .cloze-header,
.theme-balanced-nebula .mcq-header,
.theme-balanced-nebula .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  border-bottom: 1px solid rgba(190, 24, 93, 0.25) !important;
  color: #fff !important;
}

.theme-balanced-nebula .theme-family-btn,
.theme-balanced-nebula .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #fff !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-balanced-nebula .card-type,
.theme-balanced-nebula .cloze-title,
.theme-balanced-nebula .mcq-title,
.theme-balanced-nebula .image-title,
.theme-balanced-nebula .header-text {
  color: #FDF2F8 !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-balanced-nebula .question-text,
.theme-balanced-nebula .question-section {
  color: #F472B6 !important;
  text-shadow: 0 0 2px rgba(244, 114, 182, 0.25);
}

.theme-balanced-nebula .answer-text,
.theme-balanced-nebula .cloze-content {
  color: #A5B4FC !important;
  text-shadow: 0 0 2px rgba(165, 180, 252, 0.18);
}

.theme-balanced-nebula .mcq-correct-answer {
  color: #325AFB !important;
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(199, 210, 254, 0.45);
}

.theme-balanced-nebula .cloze {
  background: linear-gradient(135deg, #9D174D, #BE185D) !important;
  color: #FFE4E6 !important;
}

.theme-balanced-nebula .explanation-section,
.theme-balanced-nebula .explanation-block {
  background: rgba(165, 180, 252, 0.06) !important;
  border-left: 5px solid #818CF8 !important;
  color: #C7D2FE !important;
  box-shadow: 0 0 15px rgba(129, 140, 248, 0.3) !important;
}

.theme-balanced-nebula .correlation-section,
.theme-balanced-nebula .correlation-block {
  background: rgba(244, 114, 182, 0.06) !important;
  border-left: 5px solid #F472B6 !important;
  color: #F9A8D4 !important;
  box-shadow: 0 0 15px rgba(244, 114, 182, 0.3) !important;
}

.theme-balanced-nebula .extra-info,
.theme-balanced-nebula .extra-block,
.theme-balanced-nebula .comments-block {
  background: rgba(251, 146, 60, 0.06) !important;
  border-left: 5px solid #FB923C !important;
  color: #FDBA74 !important;
  box-shadow: 0 0 15px rgba(251, 146, 60, 0.3) !important;
}

/* 3.3: balanced-supernova (Bright Oranges and Reds) */
body.theme-balanced-supernova {
  background: linear-gradient(135deg, #ff4e50 0%, #f9d423 100%) !important;
  --theme-primary: #DC2626;
  --theme-secondary: #F59E0B;
  --glow-color: rgba(220, 38, 38, 0.32);
  --cloze-glow-color: #D97706;
  --button-glow-color: #DC2626;
}

.theme-balanced-supernova .card-container,
.theme-balanced-supernova .mcq-container,
.theme-balanced-supernova .cloze-container,
.theme-balanced-supernova .image-container {
  background: #2d0b09 !important;
  color: #FDE68A !important;
  border: 2px solid rgba(249, 115, 22, 0.85) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-balanced-supernova .cloze-container {
  background: #2d0b09 !important;
  color: #FDE68A !important;
  border: 2px solid rgba(249, 115, 22, 0.85) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-balanced-supernova .meta-header,
.theme-balanced-supernova .header,
.theme-balanced-supernova .cloze-header,
.theme-balanced-supernova .mcq-header,
.theme-balanced-supernova .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  border-bottom: 1px solid rgba(220, 38, 38, 0.25) !important;
  color: #fff !important;
}

.theme-balanced-supernova .theme-family-btn,
.theme-balanced-supernova .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #fff !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-balanced-supernova .card-type,
.theme-balanced-supernova .cloze-title,
.theme-balanced-supernova .mcq-title,
.theme-balanced-supernova .image-title,
.theme-balanced-supernova .header-text {
  color: #FFFBEB !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: var(--theme-primary);
}

.theme-balanced-supernova .question-text,
.theme-balanced-supernova .question-section {
  color: #F87171 !important;
  text-shadow: 0 0 2px rgba(248, 113, 113, 0.25);
}

.theme-balanced-supernova .answer-text,
.theme-balanced-supernova .cloze-content {
  color: #FCD34D !important;
  text-shadow: 0 0 2px rgba(252, 211, 77, 0.18);
}

.theme-balanced-supernova .mcq-correct-answer {
  color: #FCDF03 !important;
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(254, 240, 138, 0.45);
}

.theme-balanced-supernova .cloze {
  background: linear-gradient(135deg, #D97706, #F97316) !important;
  color: #FFEDD5 !important;
}

.theme-balanced-supernova .explanation-section,
.theme-balanced-supernova .explanation-block {
  background: rgba(252, 211, 77, 0.06) !important;
  border-left: 5px solid #FBBF24 !important;
  color: #FEF9C3 !important;
  box-shadow: 0 0 15px rgba(251, 191, 36, 0.3) !important;
}

.theme-balanced-supernova .correlation-section,
.theme-balanced-supernova .correlation-block {
  background: rgba(248, 113, 113, 0.06) !important;
  border-left: 5px solid #EF4444 !important;
  color: #FEE2E2 !important;
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.3) !important;
}

.theme-balanced-supernova .extra-info,
.theme-balanced-supernova .extra-block,
.theme-balanced-supernova .comments-block {
  background: rgba(240, 253, 244, 0.06) !important;
  border-left: 5px solid #A3E635 !important;
  color: #ECFCCB !important;
  box-shadow: 0 0 15px rgba(163, 230, 53, 0.3) !important;
}

/* 3.4: balanced-galaxy (Deep Indigo and Silver) */
body.theme-balanced-galaxy {
  background: linear-gradient(135deg, #16222A 0%, #3A6073 100%) !important;
  --theme-primary: #9CA3AF;
  --theme-secondary: #E5E7EB;
  --glow-color: rgba(156, 163, 175, 0.28);
  --cloze-glow-color: #4F46E5;
  --button-glow-color: #9CA3AF;
}

.theme-balanced-galaxy .card-container,
.theme-balanced-galaxy .mcq-container,
.theme-balanced-galaxy .cloze-container,
.theme-balanced-galaxy .image-container {
  background: #172554 !important;
  color: #E0E7FF !important;
  border: 2px solid rgba(67, 56, 202, 0.85) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-balanced-galaxy .cloze-container {
  background: #172554 !important;
  color: #E0E7FF !important;
  border: 2px solid rgba(67, 56, 202, 0.85) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-balanced-galaxy .meta-header,
.theme-balanced-galaxy .header,
.theme-balanced-galaxy .cloze-header,
.theme-balanced-galaxy .mcq-header,
.theme-balanced-galaxy .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  border-bottom: 1px solid rgba(156, 163, 175, 0.22) !important;
  color: #1F2937 !important;
}

.theme-balanced-galaxy .theme-family-btn,
.theme-balanced-galaxy .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #1F2937 !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-balanced-galaxy .card-type,
.theme-balanced-galaxy .cloze-title,
.theme-balanced-galaxy .mcq-title,
.theme-balanced-galaxy .image-title,
.theme-balanced-galaxy .header-text {
  color: #1F2937 !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: #9CA3AF;
}

.theme-balanced-galaxy .question-text,
.theme-balanced-galaxy .question-section {
  color: #C7D2FE !important;
  text-shadow: 0 0 2px rgba(199, 210, 254, 0.25);
}

.theme-balanced-galaxy .answer-text,
.theme-balanced-galaxy .cloze-content {
  color: #A5F3FC !important;
  text-shadow: 0 0 2px rgba(165, 243, 252, 0.18);
}

.theme-balanced-galaxy .mcq-correct-answer {
  color: #5B33FA !important;
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(196, 181, 253, 0.45);
}

.theme-balanced-galaxy .cloze {
  background: linear-gradient(135deg, #4F46E5, #6366F1) !important;
  color: #EEF2FF !important;
}

.theme-balanced-galaxy .explanation-section,
.theme-balanced-galaxy .explanation-block {
  background: rgba(165, 243, 252, 0.06) !important;
  border-left: 5px solid #22D3EE !important;
  color: #CFFAFE !important;
  box-shadow: 0 0 15px rgba(34, 211, 238, 0.3) !important;
}

.theme-balanced-galaxy .correlation-section,
.theme-balanced-galaxy .correlation-block {
  background: rgba(199, 210, 254, 0.06) !important;
  border-left: 5px solid #A5B4FC !important;
  color: #E0E7FF !important;
  box-shadow: 0 0 15px rgba(165, 180, 252, 0.3) !important;
}

.theme-balanced-galaxy .extra-info,
.theme-balanced-galaxy .extra-block,
.theme-balanced-galaxy .comments-block {
  background: rgba(209, 213, 219, 0.06) !important;
  border-left: 5px solid #9CA3AF !important;
  color: #E5E7EB !important;
  box-shadow: 0 0 15px rgba(156, 163, 175, 0.3) !important;
}

/* 3.5: balanced-comet (Icy Cyan on Dark Blue) */
body.theme-balanced-comet {
  background: linear-gradient(135deg, #0f2027 0%, #203a43 100%) !important;
  --theme-primary: #06B6D4;
  --theme-secondary: #67E8F9;
  --glow-color: rgba(6, 182, 212, 0.32);
  --cloze-glow-color: #0891B2;
  --button-glow-color: #06B6D4;
}

.theme-balanced-comet .card-container,
.theme-balanced-comet .mcq-container,
.theme-balanced-comet .cloze-container,
.theme-balanced-comet .image-container {
  background: #041625 !important;
  color: #CFFAFE !important;
  border: 2px solid rgba(14, 116, 144, 0.85) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-balanced-comet .cloze-container {
  background: #041625 !important;
  color: #CFFAFE !important;
  border: 2px solid rgba(14, 116, 144, 0.85) !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-balanced-comet .meta-header,
.theme-balanced-comet .header,
.theme-balanced-comet .cloze-header,
.theme-balanced-comet .mcq-header,
.theme-balanced-comet .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  border-bottom: 1px solid rgba(6, 182, 212, 0.25) !important;
  color: #164e63 !important;
}

.theme-balanced-comet .theme-family-btn,
.theme-balanced-comet .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #164e63 !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-balanced-comet .card-type,
.theme-balanced-comet .cloze-title,
.theme-balanced-comet .mcq-title,
.theme-balanced-comet .image-title,
.theme-balanced-comet .header-text {
  color: #155E75 !important;
  animation: neonTextPulse 2s infinite !important;
  --neon-color: #67E8F9;
}

.theme-balanced-comet .question-text,
.theme-balanced-comet .question-section {
  color: #22D3EE !important;
  text-shadow: 0 0 2px rgba(34, 211, 238, 0.25);
}

.theme-balanced-comet .answer-text,
.theme-balanced-comet .cloze-content {
  color: #A7F3D0 !important;
  text-shadow: 0 0 2px rgba(167, 243, 208, 0.18);
}

.theme-balanced-comet .mcq-correct-answer {
  color: #9CEC13 !important;
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(190, 242, 100, 0.45);
}

.theme-balanced-comet .cloze {
  background: linear-gradient(135deg, #0891B2, #22D3EE) !important;
  color: #F0FDF4 !important;
}

.theme-balanced-comet .explanation-section,
.theme-balanced-comet .explanation-block {
  background: rgba(167, 243, 208, 0.06) !important;
  border-left: 5px solid #6EE7B7 !important;
  color: #D1FAE5 !important;
  box-shadow: 0 0 15px rgba(110, 231, 183, 0.3) !important;
}

.theme-balanced-comet .correlation-section,
.theme-balanced-comet .correlation-block {
  background: rgba(165, 243, 252, 0.06) !important;
  border-left: 5px solid #67E8F9 !important;
  color: #A5F3FC !important;
  box-shadow: 0 0 15px rgba(103, 232, 249, 0.3) !important;
}

.theme-balanced-comet .extra-info,
.theme-balanced-comet .extra-block,
.theme-balanced-comet .comments-block {
  background: rgba(199, 210, 254, 0.06) !important;
  border-left: 5px solid #A5B4FC !important;
  color: #E0E7FF !important;
  box-shadow: 0 0 15px rgba(165, 180, 252, 0.3) !important;
}

/* =================================================================== */
/* =========== 🌙 FAMILY: TWILIGHT THEMES (Final v24) ================ */
/* =================================================================== */

.theme-twilight-crescent-moon .custom-image-question,
.theme-twilight-city-night .custom-image-question,
.theme-twilight-deep-forest .custom-image-question,
.theme-twilight-moonlit-ocean .custom-image-question,
.theme-twilight-dusk .custom-image-question {
  background: rgba(15, 23, 42, 0.8) !important;
  backdrop-filter: blur(10px);
  border-color: #38BDF8 !important;
  color: #E2E8F0 !important; /* Makes question text light */
}

/* 4.1: twilight-crescent-moon (Soft Slate & Teal) */
body.theme-twilight-crescent-moon {
  background: linear-gradient(-225deg, #1E293B 0%, #111827 100%);
  --theme-primary: #7DD3FC;
  --theme-secondary: #38BDF8;
  --glow-color: rgba(125, 211, 252, 0.25);
  --cloze-glow-color: #38BDF8;
  --button-glow-color: #7DD3FC;
}

.theme-twilight-crescent-moon .card-container,
.theme-twilight-crescent-moon .mcq-container,
.theme-twilight-crescent-moon .image-container,
.theme-twilight-crescent-moon .cloze-container {
  background: rgba(15, 23, 42, 0.8) !important;
  backdrop-filter: blur(14px) !important;
  color: #E2E8F0 !important;
  border: 2px solid #475569 !important;
  box-shadow: 0 0 18px var(--glow-color) !important;
}

.theme-twilight-crescent-moon .cloze-container {
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-twilight-crescent-moon .cloze-content {
  --glow-color: var(--cloze-glow-color) !important;
  border-radius: 8px;
}

.theme-twilight-crescent-moon .meta-header,
.theme-twilight-crescent-moon .header,
.theme-twilight-crescent-moon .cloze-header,
.theme-twilight-crescent-moon .mcq-header,
.theme-twilight-crescent-moon .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #0F172A !important;
}

.theme-twilight-crescent-moon .theme-family-btn,
.theme-twilight-crescent-moon .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #0F172A !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-twilight-crescent-moon .card-type,
.theme-twilight-crescent-moon .cloze-title,
.theme-twilight-crescent-moon .mcq-title,
.theme-twilight-crescent-moon .image-title,
.theme-twilight-crescent-moon .header-text {
  color: #0F172A !important;
}

.theme-twilight-crescent-moon .question-text,
.theme-twilight-crescent-moon .question-section {
  color: #BAE6FD !important;
}

.theme-twilight-crescent-moon .answer-text,
.theme-twilight-crescent-moon .cloze-content {
  color: #D9F99D !important;
}

.theme-twilight-crescent-moon .mcq-correct-answer {
  color: #0CB3CC !important; /* bright cyan-teal */
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(125, 211, 252, 0.45); /* soft glow */
}

.theme-twilight-crescent-moon .cloze {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #0F172A !important;
}

.theme-twilight-crescent-moon .explanation-section,
.theme-twilight-crescent-moon .explanation-block {
  background: rgba(217, 249, 157, 0.08) !important;
  border-left: 5px solid #A3E635 !important;
  color: #EAFBCC !important;
  box-shadow: 0 0 15px rgba(163, 230, 53, 0.3) !important;
}

.theme-twilight-crescent-moon .correlation-section,
.theme-twilight-crescent-moon .correlation-block {
  background: rgba(186, 230, 253, 0.08) !important;
  border-left: 5px solid #38BDF8 !important;
  color: #E0F2FE !important;
  box-shadow: 0 0 15px rgba(56, 189, 248, 0.3) !important;
}

.theme-twilight-crescent-moon .extra-info,
.theme-twilight-crescent-moon .extra-block,
.theme-twilight-crescent-moon .comments-block {
  background: rgba(252, 211, 77, 0.08) !important;
  border-left: 5px solid #FBBF24 !important;
  color: #FEF9C3 !important;
  box-shadow: 0 0 15px rgba(251, 191, 36, 0.3) !important;
}

/* 4.2: twilight-city-night (Nord Neon Charcoal) */
body.theme-twilight-city-night {
  background: linear-gradient(135deg, #2E3440 0%, #191D24 100%);
  --theme-primary: #88C0D0;
  --theme-secondary: #81A1C1;
  --glow-color: rgba(136, 192, 208, 0.25);
  --cloze-glow-color: #5E81AC;
  --button-glow-color: #88C0D0;
}

.theme-twilight-city-night .card-container,
.theme-twilight-city-night .mcq-container,
.theme-twilight-city-night .image-container,
.theme-twilight-city-night .cloze-container {
  background: rgba(30, 30, 35, 0.8) !important;
  backdrop-filter: blur(10px) !important;
  color: #ECEFF4 !important;
  border: 2px solid #4C566A !important;
  box-shadow: 0 0 18px var(--glow-color) !important;
}

.theme-twilight-city-night .cloze-container {
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-twilight-city-night .cloze-content {
  --glow-color: var(--cloze-glow-color) !important;
  border-radius: 8px;
}

.theme-twilight-city-night .meta-header,
.theme-twilight-city-night .header,
.theme-twilight-city-night .cloze-header,
.theme-twilight-city-night .mcq-header,
.theme-twilight-city-night .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #2E3440 !important;
}

.theme-twilight-city-night .theme-family-btn,
.theme-twilight-city-night .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #2E3440 !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-twilight-city-night .card-type,
.theme-twilight-city-night .cloze-title,
.theme-twilight-city-night .mcq-title,
.theme-twilight-city-night .image-title,
.theme-twilight-city-night .header-text {
  color: #2E3440 !important;
}

.theme-twilight-city-night .question-text,
.theme-twilight-city-night .question-section {
  color: #A5F3FC !important;
}

.theme-twilight-city-night .answer-text,
.theme-twilight-city-night .cloze-content {
  color: #FBCFE8 !important;
}

.theme-twilight-city-night .mcq-correct-answer {
  color: #04CEFB !important; /* vivid icy blue */
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(136, 192, 208, 0.45);
}

.theme-twilight-city-night .cloze {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #2E3440 !important;
}

.theme-twilight-city-night .explanation-section,
.theme-twilight-city-night .explanation-block {
  background: rgba(249, 168, 212, 0.08) !important;
  border-left: 5px solid #F472B6 !important;
  color: #FBCFE8 !important;
  box-shadow: 0 0 15px rgba(244, 114, 182, 0.3) !important;
}

.theme-twilight-city-night .correlation-section,
.theme-twilight-city-night .correlation-block {
  background: rgba(165, 243, 252, 0.08) !important;
  border-left: 5px solid #67E8F9 !important;
  color: #A5F3FC !important;
  box-shadow: 0 0 15px rgba(103, 232, 249, 0.3) !important;
}

.theme-twilight-city-night .extra-info,
.theme-twilight-city-night .extra-block,
.theme-twilight-city-night .comments-block {
  background: rgba(167, 243, 208, 0.08) !important;
  border-left: 5px solid #34D399 !important;
  color: #A7F3D0 !important;
  box-shadow: 0 0 15px rgba(52, 211, 153, 0.3) !important;
}

/* 4.3: twilight-deep-forest (Cool Pine & Moss) */
body.theme-twilight-deep-forest {
  background: linear-gradient(135deg, #1A2E28 0%, #283B32 100%);
  --theme-primary: #A3BE8C;
  --theme-secondary: #8FBCBB;
  --glow-color: rgba(163, 190, 140, 0.25);
  --cloze-glow-color: #A3BE8C;
  --button-glow-color: #A3BE8C;
}

.theme-twilight-deep-forest .card-container,
.theme-twilight-deep-forest .mcq-container,
.theme-twilight-deep-forest .image-container,
.theme-twilight-deep-forest .cloze-container {
  background: rgba(21, 32, 23, 0.8) !important;
  backdrop-filter: blur(10px) !important;
  color: #D8DEE9 !important;
  border: 2px solid #A3BE8C !important;
  box-shadow: 0 0 18px var(--glow-color) !important;
}

.theme-twilight-deep-forest .cloze-container {
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-twilight-deep-forest .cloze-content {
  --glow-color: var(--cloze-glow-color) !important;
  border-radius: 8px;
}

.theme-twilight-deep-forest .meta-header,
.theme-twilight-deep-forest .header,
.theme-twilight-deep-forest .cloze-header,
.theme-twilight-deep-forest .mcq-header,
.theme-twilight-deep-forest .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #2E3440 !important;
}

.theme-twilight-deep-forest .theme-family-btn,
.theme-twilight-deep-forest .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #2E3440 !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-twilight-deep-forest .card-type,
.theme-twilight-deep-forest .cloze-title,
.theme-twilight-deep-forest .mcq-title,
.theme-twilight-deep-forest .image-title,
.theme-twilight-deep-forest .header-text {
  color: #2E3440 !important;
}

.theme-twilight-deep-forest .question-text,
.theme-twilight-deep-forest .question-section {
  color: #BEF264 !important;
}

.theme-twilight-deep-forest .answer-text,
.theme-twilight-deep-forest .cloze-content {
  color: #FDE68A !important;
}

.theme-twilight-deep-forest .mcq-correct-answer {
  color: #5B990B !important; /* luminous lime-green */
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(190, 242, 100, 0.45);
}

.theme-twilight-deep-forest .cloze {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #2E3440 !important;
}

.theme-twilight-deep-forest .explanation-section,
.theme-twilight-deep-forest .explanation-block {
  background: rgba(253, 230, 138, 0.08) !important;
  border-left: 5px solid #FACC15 !important;
  color: #FEF9C3 !important;
  box-shadow: 0 0 15px rgba(250, 204, 21, 0.3) !important;
}

.theme-twilight-deep-forest .correlation-section,
.theme-twilight-deep-forest .correlation-block {
  background: rgba(190, 242, 100, 0.08) !important;
  border-left: 5px solid #BEF264 !important;
  color: #F7FEE7 !important;
  box-shadow: 0 0 15px rgba(190, 242, 100, 0.3) !important;
}

.theme-twilight-deep-forest .extra-info,
.theme-twilight-deep-forest .extra-block,
.theme-twilight-deep-forest .comments-block {
  background: rgba(143, 188, 187, 0.08) !important;
  border-left: 5px solid #8FBCBB !important;
  color: #E5E9F0 !important;
  box-shadow: 0 0 15px rgba(143, 188, 187, 0.3) !important;
}

/* 4.4: twilight-moonlit-ocean (Nord Blue Mist) */
body.theme-twilight-moonlit-ocean {
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
  --theme-primary: #81A1C1;
  --theme-secondary: #5E81AC;
  --glow-color: rgba(94, 129, 172, 0.25);
  --cloze-glow-color: #88C0D0;
  --button-glow-color: #81A1C1;
}

.theme-twilight-moonlit-ocean .card-container,
.theme-twilight-moonlit-ocean .mcq-container,
.theme-twilight-moonlit-ocean .image-container,
.theme-twilight-moonlit-ocean .cloze-container {
  background: rgba(15, 23, 42, 0.8) !important;
  color: #E5E9F0 !important;
  border: 2px solid #4C566A !important;
  box-shadow: 0 0 18px var(--glow-color) !important;
}

.theme-twilight-moonlit-ocean .cloze-container {
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-twilight-moonlit-ocean .cloze-content {
  --glow-color: var(--cloze-glow-color) !important;
  border-radius: 8px;
}

.theme-twilight-moonlit-ocean .meta-header,
.theme-twilight-moonlit-ocean .header,
.theme-twilight-moonlit-ocean .cloze-header,
.theme-twilight-moonlit-ocean .mcq-header,
.theme-twilight-moonlit-ocean .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ECEFF4 !important;
}

.theme-twilight-moonlit-ocean .theme-family-btn,
.theme-twilight-moonlit-ocean .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ECEFF4 !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-twilight-moonlit-ocean .card-type,
.theme-twilight-moonlit-ocean .cloze-title,
.theme-twilight-moonlit-ocean .mcq-title,
.theme-twilight-moonlit-ocean .image-title,
.theme-twilight-moonlit-ocean .header-text {
  color: #ECEFF4 !important;
}

.theme-twilight-moonlit-ocean .question-text,
.theme-twilight-moonlit-ocean .question-section {
  color: #88C0D0 !important;
}

.theme-twilight-moonlit-ocean .answer-text,
.theme-twilight-moonlit-ocean .cloze-content {
  color: #A3BE8C !important;
}

.theme-twilight-moonlit-ocean .mcq-correct-answer {
  color: #3C8296 !important; /* nord aqua blue */
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(94, 129, 172, 0.45);
}

.theme-twilight-moonlit-ocean .cloze {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ECEFF4 !important;
}

.theme-twilight-moonlit-ocean .explanation-section,
.theme-twilight-moonlit-ocean .explanation-block {
  background: rgba(163, 190, 140, 0.08) !important;
  border-left: 5px solid #A3BE8C !important;
  color: #E5E9F0 !important;
  box-shadow: 0 0 15px rgba(163, 190, 140, 0.3) !important;
}

.theme-twilight-moonlit-ocean .correlation-section,
.theme-twilight-moonlit-ocean .correlation-block {
  background: rgba(136, 192, 208, 0.08) !important;
  border-left: 5px solid #88C0D0 !important;
  color: #ECEFF4 !important;
  box-shadow: 0 0 15px rgba(136, 192, 208, 0.3) !important;
}

.theme-twilight-moonlit-ocean .extra-info,
.theme-twilight-moonlit-ocean .extra-block,
.theme-twilight-moonlit-ocean .comments-block {
  background: rgba(94, 129, 172, 0.08) !important;
  border-left: 5px solid #5E81AC !important;
  color: #D8DEE9 !important;
  box-shadow: 0 0 15px rgba(94, 129, 172, 0.3) !important;
}

/* 4.5: twilight-dusk (Warm Aurora Fade) */
body.theme-twilight-dusk {
  background: linear-gradient(135deg, #2B1055 0%, #4C1D95 100%);
  --theme-primary: #D946EF;
  --theme-secondary: #8B5CF6;
  --glow-color: rgba(217, 70, 239, 0.25);
  --cloze-glow-color: #C084FC;
  --button-glow-color: #D946EF;
}

.theme-twilight-dusk .card-container,
.theme-twilight-dusk .mcq-container,
.theme-twilight-dusk .image-container,
.theme-twilight-dusk .cloze-container {
  background: rgba(43, 16, 85, 0.8) !important;
  color: #F3E8FF !important;
  border: 2px solid #C084FC !important;
  box-shadow: 0 0 18px var(--glow-color) !important;
}

.theme-twilight-dusk .cloze-container {
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-twilight-dusk .cloze-content {
  --glow-color: var(--cloze-glow-color) !important;
  border-radius: 8px;
}

.theme-twilight-dusk .meta-header,
.theme-twilight-dusk .header,
.theme-twilight-dusk .cloze-header,
.theme-twilight-dusk .mcq-header,
.theme-twilight-dusk .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #F3E8FF !important;
}

.theme-twilight-dusk .theme-family-btn,
.theme-twilight-dusk .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #F3E8FF !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-twilight-dusk .card-type,
.theme-twilight-dusk .cloze-title,
.theme-twilight-dusk .mcq-title,
.theme-twilight-dusk .image-title,
.theme-twilight-dusk .header-text {
  color: #F3E8FF !important;
}

.theme-twilight-dusk .question-text,
.theme-twilight-dusk .question-section {
  color: #F5D0FE !important;
}

.theme-twilight-dusk .answer-text,
.theme-twilight-dusk .cloze-content {
  color: #C4B5FD !important;
}

.theme-twilight-dusk .mcq-correct-answer {
  color: #C105F0 !important; /* warm pink-violet highlight */
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(245, 208, 254, 0.55);
}

.theme-twilight-dusk .cloze {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #F3E8FF !important;
}

.theme-twilight-dusk .explanation-section,
.theme-twilight-dusk .explanation-block {
  background: rgba(192, 132, 252, 0.08) !important;
  border-left: 5px solid #C084FC !important;
  color: #E9D5FF !important;
  box-shadow: 0 0 15px rgba(192, 132, 252, 0.3) !important;
}

.theme-twilight-dusk .correlation-section,
.theme-twilight-dusk .correlation-block {
  background: rgba(245, 208, 254, 0.08) !important;
  border-left: 5px solid #F5D0FE !important;
  color: #FAFAF9 !important;
  box-shadow: 0 0 15px rgba(245, 208, 254, 0.3) !important;
}

.theme-twilight-dusk .extra-info,
.theme-twilight-dusk .extra-block,
.theme-twilight-dusk .comments-block {
  background: rgba(167, 139, 250, 0.08) !important;
  border-left: 5px solid #A78BFA !important;
  color: #DDD6FE !important;
  box-shadow: 0 0 15px rgba(167, 139, 250, 0.3) !important;
}

/* =================================================================== */
/* ============== 🪐 FAMILY: DARK THEMES (Final v24) ================= */
/* =================================================================== */

.theme-dark-saturn .custom-image-question,
.theme-dark-mars-rover .custom-image-question,
.theme-dark-neptune-deep .custom-image-question,
.theme-dark-black-hole .custom-image-question,
.theme-dark-starless-sky .custom-image-question {
  background: #000000 !important;
  border-color: #4C566A !important;
  color: #E5E9F0 !important; /* Makes question text light */
}

/* 5.1: dark-saturn (Nord Rose on Midnight) */
body.theme-dark-saturn {
  background: linear-gradient(-225deg, #1B1F29 0%, #0B0C10 100%);
  --theme-primary: #BF616A;
  --theme-secondary: #B48EAD;
  --glow-color: rgba(191, 97, 106, 0.5);
  --cloze-glow-color: #A3BE8C;
  --button-glow-color: #BF616A;
}

.theme-dark-saturn .card-container,
.theme-dark-saturn .mcq-container,
.theme-dark-saturn .image-container,
.theme-dark-saturn .cloze-container {
  background: rgba(17, 24, 39, 0.85) !important;
  backdrop-filter: blur(16px) !important;
  color: #ECEFF4 !important;
  border: 2px solid rgba(180, 142, 173, 0.3) !important;
  box-shadow: 0 0 25px var(--glow-color) !important;
}

.theme-dark-saturn .cloze-container {
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-dark-saturn .cloze-content {
  --glow-color: var(--cloze-glow-color) !important;
  border-radius: 8px;
}

.theme-dark-saturn .meta-header,
.theme-dark-saturn .header,
.theme-dark-saturn .cloze-header,
.theme-dark-saturn .mcq-header,
.theme-dark-saturn .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  border-bottom: 1px solid rgba(191, 97, 106, 0.3) !important;
  color: #ECEFF4 !important;
}

.theme-dark-saturn .theme-family-btn,
.theme-dark-saturn .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ECEFF4 !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-dark-saturn .card-type,
.theme-dark-saturn .cloze-title,
.theme-dark-saturn .mcq-title,
.theme-dark-saturn .image-title,
.theme-dark-saturn .header-text {
  color: #ECEFF4 !important;
}

.theme-dark-saturn .question-text,
.theme-dark-saturn .question-section {
  color: #EBCB8B !important;
  text-shadow: 0 0 5px rgba(235, 203, 139, 0.5);
}

.theme-dark-saturn .answer-text,
.theme-dark-saturn .cloze-content {
  color: #A3BE8C !important;
  text-shadow: 0 0 5px rgba(163, 190, 140, 0.5);
}

.theme-dark-saturn .mcq-correct-answer {
  color: #DA9E25 !important; /* nord gold accent */
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(235, 203, 139, 0.45);
}

.theme-dark-saturn .cloze {
  background: linear-gradient(135deg, #A3BE8C, #88C0D0) !important;
  color: #2E3440 !important;
}

.theme-dark-saturn .explanation-section,
.theme-dark-saturn .explanation-block {
  background: rgba(163, 190, 140, 0.08) !important;
  border-left: 5px solid #A3BE8C !important;
  color: #ECEFF4 !important;
  box-shadow: 0 0 15px rgba(163, 190, 140, 0.3) !important;
}

.theme-dark-saturn .correlation-section,
.theme-dark-saturn .correlation-block {
  background: rgba(235, 203, 139, 0.08) !important;
  border-left: 5px solid #EBCB8B !important;
  color: #E5E9F0 !important;
  box-shadow: 0 0 15px rgba(235, 203, 139, 0.3) !important;
}

.theme-dark-saturn .extra-info,
.theme-dark-saturn .extra-block,
.theme-dark-saturn .comments-block {
  background: rgba(180, 142, 173, 0.08) !important;
  border-left: 5px solid #B48EAD !important;
  color: #D8DEE9 !important;
  box-shadow: 0 0 15px rgba(180, 142, 173, 0.3) !important;
}

/* 5.2: dark-mars-rover (Nord Rust on Void) */
body.theme-dark-mars-rover {
  background: #0D0D0D;
  --theme-primary: #BF616A;
  --theme-secondary: #D08770;
  --glow-color: rgba(208, 135, 112, 0.4);
  --cloze-glow-color: #EBCB8B;
  --button-glow-color: #BF616A;
}

.theme-dark-mars-rover .card-container,
.theme-dark-mars-rover .mcq-container,
.theme-dark-mars-rover .image-container,
.theme-dark-mars-rover .cloze-container {
  background: rgba(20, 10, 10, 0.85) !important;
  backdrop-filter: blur(10px) !important;
  color: #ECEFF4 !important;
  border: 2px solid #BF616A !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-dark-mars-rover .cloze-container {
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-dark-mars-rover .cloze-content {
  --glow-color: var(--cloze-glow-color) !important;
  border-radius: 8px;
}

.theme-dark-mars-rover .meta-header,
.theme-dark-mars-rover .header,
.theme-dark-mars-rover .cloze-header,
.theme-dark-mars-rover .mcq-header,
.theme-dark-mars-rover .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ECEFF4 !important;
}

.theme-dark-mars-rover .theme-family-btn,
.theme-dark-mars-rover .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ECEFF4 !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-dark-mars-rover .question-text,
.theme-dark-mars-rover .question-section {
  color: #EBCB8B !important;
  text-shadow: 0 0 5px rgba(235, 203, 139, 0.4);
}

.theme-dark-mars-rover .answer-text,
.theme-dark-mars-rover .cloze-content {
  color: #D8DEE9 !important;
  text-shadow: 0 0 5px rgba(216, 222, 233, 0.4);
}

.theme-dark-mars-rover .mcq-correct-answer {
  color: #C15D3E !important; /* nord rust-orange */
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(208, 135, 112, 0.5);
}

.theme-dark-mars-rover .cloze {
  background: linear-gradient(135deg, #D08770, #BF616A) !important;
  color: #ECEFF4 !important;
}

.theme-dark-mars-rover .explanation-section,
.theme-dark-mars-rover .explanation-block {
  background: rgba(208, 135, 112, 0.08) !important;
  border-left: 5px solid #D08770 !important;
  color: #ECEFF4 !important;
  box-shadow: 0 0 15px rgba(208, 135, 112, 0.3) !important;
}

.theme-dark-mars-rover .correlation-section,
.theme-dark-mars-rover .correlation-block {
  background: rgba(235, 203, 139, 0.08) !important;
  border-left: 5px solid #EBCB8B !important;
  color: #E5E9F0 !important;
  box-shadow: 0 0 15px rgba(235, 203, 139, 0.3) !important;
}

.theme-dark-mars-rover .extra-info,
.theme-dark-mars-rover .extra-block,
.theme-dark-mars-rover .comments-block {
  background: rgba(191, 97, 106, 0.08) !important;
  border-left: 5px solid #BF616A !important;
  color: #D8DEE9 !important;
  box-shadow: 0 0 15px rgba(191, 97, 106, 0.3) !important;
}

/* 5.3: dark-neptune-deep (Nord Ice Ocean) */
body.theme-dark-neptune-deep {
  background: #0A0F1C;
  --theme-primary: #5E81AC;
  --theme-secondary: #81A1C1;
  --glow-color: rgba(94, 129, 172, 0.4);
  --cloze-glow-color: #88C0D0;
  --button-glow-color: #5E81AC;
}

.theme-dark-neptune-deep .card-container,
.theme-dark-neptune-deep .mcq-container,
.theme-dark-neptune-deep .image-container,
.theme-dark-neptune-deep .cloze-container {
  background: rgba(5, 10, 20, 0.8) !important;
  backdrop-filter: blur(10px) !important;
  color: #E5E9F0 !important;
  border: 2px solid #5E81AC !important;
  box-shadow: 0 0 25px var(--glow-color) !important;
}

.theme-dark-neptune-deep .cloze-container {
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-dark-neptune-deep .cloze-content {
  --glow-color: var(--cloze-glow-color) !important;
  border-radius: 8px;
}

.theme-dark-neptune-deep .meta-header,
.theme-dark-neptune-deep .header,
.theme-dark-neptune-deep .cloze-header,
.theme-dark-neptune-deep .mcq-header,
.theme-dark-neptune-deep .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ECEFF4 !important;
}

.theme-dark-neptune-deep .theme-family-btn,
.theme-dark-neptune-deep .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ECEFF4 !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-dark-neptune-deep .question-text,
.theme-dark-neptune-deep .question-section {
  color: #88C0D0 !important;
  text-shadow: 0 0 5px rgba(136, 192, 208, 0.4);
}

.theme-dark-neptune-deep .answer-text,
.theme-dark-neptune-deep .cloze-content {
  color: #A3BE8C !important;
  text-shadow: 0 0 5px rgba(163, 190, 140, 0.4);
}

.theme-dark-neptune-deep .mcq-correct-answer {
  color: #3C8296 !important; /* nord aqua-blue */
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(136, 192, 208, 0.5);
}

.theme-dark-neptune-deep .cloze {
  background: linear-gradient(135deg, #5E81AC, #88C0D0) !important;
  color: #ECEFF4 !important;
}

.theme-dark-neptune-deep .explanation-section,
.theme-dark-neptune-deep .explanation-block {
  background: rgba(136, 192, 208, 0.08) !important;
  border-left: 5px solid #88C0D0 !important;
  color: #ECEFF4 !important;
  box-shadow: 0 0 15px rgba(136, 192, 208, 0.3) !important;
}

.theme-dark-neptune-deep .correlation-section,
.theme-dark-neptune-deep .correlation-block {
  background: rgba(163, 190, 140, 0.08) !important;
  border-left: 5px solid #A3BE8C !important;
  color: #E5E9F0 !important;
  box-shadow: 0 0 15px rgba(163, 190, 140, 0.3) !important;
}

.theme-dark-neptune-deep .extra-info,
.theme-dark-neptune-deep .extra-block,
.theme-dark-neptune-deep .comments-block {
  background: rgba(94, 129, 172, 0.08) !important;
  border-left: 5px solid #5E81AC !important;
  color: #D8DEE9 !important;
  box-shadow: 0 0 15px rgba(94, 129, 172, 0.3) !important;
}

/* 5.4: dark-black-hole (Nord Mono Violet) */
body.theme-dark-black-hole {
  background: #0B0B0C;
  --theme-primary: #B48EAD;
  --theme-secondary: #4C566A;
  --glow-color: rgba(180, 142, 173, 0.3);
  --cloze-glow-color: #A3BE8C;
  --button-glow-color: #B48EAD;
}

.theme-dark-black-hole .card-container,
.theme-dark-black-hole .mcq-container,
.theme-dark-black-hole .image-container,
.theme-dark-black-hole .cloze-container {
  background: rgba(15, 15, 18, 0.85) !important;
  backdrop-filter: blur(10px) !important;
  color: #E5E9F0 !important;
  border: 2px solid #4C566A !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-dark-black-hole .cloze-container {
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-dark-black-hole .cloze-content {
  --glow-color: var(--cloze-glow-color) !important;
  border-radius: 8px;
}

.theme-dark-black-hole .meta-header,
.theme-dark-black-hole .header,
.theme-dark-black-hole .cloze-header,
.theme-dark-black-hole .mcq-header,
.theme-dark-black-hole .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ECEFF4 !important;
}

.theme-dark-black-hole .theme-family-btn,
.theme-dark-black-hole .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #ECEFF4 !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-dark-black-hole .mcq-correct-answer {
  color: #62415C !important; /* nord violet */
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(180, 142, 173, 0.5);
}

.theme-dark-black-hole .cloze {
  background: linear-gradient(135deg, #B48EAD, #A3BE8C) !important;
  color: #ECEFF4 !important;
}

.theme-dark-black-hole .explanation-section,
.theme-dark-black-hole .explanation-block {
  background: rgba(180, 142, 173, 0.08) !important;
  border-left: 5px solid #B48EAD !important;
  color: #ECEFF4 !important;
  box-shadow: 0 0 15px rgba(180, 142, 173, 0.3) !important;
}

.theme-dark-black-hole .correlation-section,
.theme-dark-black-hole .correlation-block {
  background: rgba(163, 190, 140, 0.08) !important;
  border-left: 5px solid #A3BE8C !important;
  color: #E5E9F0 !important;
  box-shadow: 0 0 15px rgba(163, 190, 140, 0.3) !important;
}

.theme-dark-black-hole .extra-info,
.theme-dark-black-hole .extra-block,
.theme-dark-black-hole .comments-block {
  background: rgba(76, 86, 106, 0.1) !important;
  border-left: 5px solid #4C566A !important;
  color: #D8DEE9 !important;
  box-shadow: 0 0 15px rgba(76, 86, 106, 0.3) !important;
}

/* 5.5: dark-starless-sky (Nord Aurora on OLED) */
body.theme-dark-starless-sky {
  background: #000;
  --theme-primary: #8FBCBB;
  --theme-secondary: #88C0D0;
  --glow-color: rgba(143, 188, 187, 0.25);
  --cloze-glow-color: #5E81AC;
  --button-glow-color: #8FBCBB;
}

.theme-dark-starless-sky .card-container,
.theme-dark-starless-sky .mcq-container,
.theme-dark-starless-sky .image-container,
.theme-dark-starless-sky .cloze-container {
  background: #000 !important;
  color: #E5E9F0 !important;
  border: 2px solid #4C566A !important;
  box-shadow: 0 0 20px var(--glow-color) !important;
}

.theme-dark-starless-sky .cloze-container {
  --glow-color: var(--cloze-glow-color) !important;
}

.theme-dark-starless-sky .cloze-content {
  --glow-color: var(--cloze-glow-color) !important;
  border-radius: 8px;
}

.theme-dark-starless-sky .meta-header,
.theme-dark-starless-sky .header,
.theme-dark-starless-sky .cloze-header,
.theme-dark-starless-sky .mcq-header,
.theme-dark-starless-sky .image-header {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #2E3440 !important;
}

.theme-dark-starless-sky .theme-family-btn,
.theme-dark-starless-sky .toggle-btn {
  background: linear-gradient(135deg, var(--theme-primary), var(--theme-secondary)) !important;
  color: #2E3440 !important;
  box-shadow: 0 0 16px var(--button-glow-color) !important;
}

.theme-dark-starless-sky .mcq-correct-answer {
  color: #3D6665 !important; /* nord teal-green */
  font-weight: 700 !important;
  text-shadow: 0 0 6px rgba(143, 188, 187, 0.5);
}

.theme-dark-starless-sky .cloze {
  background: linear-gradient(135deg, #8FBCBB, #88C0D0) !important;
  color: #2E3440 !important;
}

.theme-dark-starless-sky .explanation-section,
.theme-dark-starless-sky .explanation-block {
  background: rgba(143, 188, 187, 0.08) !important;
  border-left: 5px solid #8FBCBB !important;
  color: #ECEFF4 !important;
  box-shadow: 0 0 15px rgba(143, 188, 187, 0.3) !important;
}

.theme-dark-starless-sky .correlation-section,
.theme-dark-starless-sky .correlation-block {
  background: rgba(136, 192, 208, 0.08) !important;
  border-left: 5px solid #88C0D0 !important;
  color: #E5E9F0 !important;
  box-shadow: 0 0 15px rgba(136, 192, 208, 0.3) !important;
}

.theme-dark-starless-sky .extra-info,
.theme-dark-starless-sky .extra-block,
.theme-dark-starless-sky .comments-block {
  background: rgba(94, 129, 172, 0.08) !important;
  border-left: 5px solid #5E81AC !important;
  color: #D8DEE9 !important;
  box-shadow: 0 0 15px rgba(94, 129, 172, 0.3) !important;
}

/* =================================================================== */
/* ==== 💎 UNIVERSAL FIX v6: Complete Layout Solution ================ */
/* =================================================================== */

/*
 * This fixes ALL layout issues across ALL note types:
 * 1. Cloze main text stays CENTER-ALIGNED and properly sized
 * 2. Supplementary fields are LEFT-ALIGNED with proper spacing
 * 3. Image containers don't "fall out" or get squeezed
 * 4. Consistent spacing across all themes
 */

/* ============================================================ */
/* 1. CLOZE MAIN TEXT AREA (Keep center-aligned, proper size) */
/* ============================================================ */
/* The actual cloze statement should be center-aligned and readable */
.cloze-content {
  text-align: center !important;      /* Main cloze text stays centered */
  font-size: 1.2em !important;        /* Keep readable size for cloze text */
  line-height: 1.8 !important;        /* Good spacing for cloze text */
  padding: 20px !important;           /* Breathing room */
}

/* ============================================================ */
/* 2. SUPPLEMENTARY FIELD CONTAINERS (Universal Layout) */
/* ============================================================ */
/* These apply to ALL supplementary fields across ALL note types */
.explanation-section, .explanation-block,
.correlation-section, .correlation-block,
.extra-info, .extra-block,
.comments-block, .comments-section,
.anatomy-section {
  /* LAYOUT (applies to all) */
  padding: 20px !important;
  margin: 20px auto !important;       /* CRITICAL: auto centers, 20px top/bottom */
  border-radius: 15px !important;
  box-sizing: border-box !important;
  width: calc(100% - 40px) !important; /* Full width minus comfortable margins */
  max-width: 100% !important;
  display: block !important;
  
  /* ALIGNMENT */
  text-align: left !important;        /* Content inside is left-aligned */
}

/* ============================================================ */
/* 3. SUPPLEMENTARY FIELDS INSIDE CLOZE (Override inheritance) */
/* ============================================================ */
/* Prevents .cloze-content's center alignment from affecting these */
.cloze-content .explanation-section,
.cloze-content .explanation-block,
.cloze-content .correlation-section,
.cloze-content .correlation-block,
.cloze-content .extra-info,
.cloze-content .extra-block,
.cloze-content .comments-block {
  text-align: left !important;        /* Force left alignment */
  font-size: 1rem !important;         /* Reset to base font size (not 1.2em) */
  line-height: 1.6 !important;        /* Better line spacing */
  margin: 20px auto !important;       /* Consistent spacing */
  width: calc(100% - 30px) !important; /* Not squeezed */
}

/* ============================================================ */
/* 4. SUPPLEMENTARY FIELD TITLES */
/* ============================================================ */
.section-title, .block-title,
.comments-title, .anatomy-title {
  font-size: 1.15em !important;
  font-weight: 500 !important;
  margin-bottom: 12px !important;
  line-height: 1.4 !important;
  text-align: left !important;        /* Titles are left-aligned */
}

/* ============================================================ */
/* 5. SUPPLEMENTARY FIELD CONTENT TEXT */
/* ============================================================ */
.explanation-text, .explanation-content,
.correlation-text, .correlation-content,
.extra-content, .block-content,
.comments-text {
  font-size: 1.0em !important;
  line-height: 1.6 !important;
  font-style: italic !important;
  text-align: left !important;
  font-weight: 500 !important;
}

/* ============================================================ */
/* 6. ANATOMY FIELDS (Image Cards) - CENTER ALIGNED */
/* ============================================================ */
.anatomy-section {
  text-align: center !important;      /* Anatomy containers are centered */
}

.anatomy-title {
  text-align: center !important;      /* Anatomy titles are centered */
  font-size: 1.15em !important;
  font-weight: 500 !important;
  margin-bottom: 12px !important;
  line-height: 1.4 !important;
}

.anatomy-text {
  font-size: 1.0em !important;
  line-height: 1.6 !important;
  text-align: center !important;      /* Anatomy text is centered */
  font-weight: 500 !important;
}

.custom-origin,
.custom-insertion,
.custom-innervation,
.custom-action {
  font-weight: 600 !important;
  font-size: 1.1em !important;
  font-style: normal !important;
  line-height: 1.5 !important;
  text-align: center !important;
}

/* ============================================================ */
/* 7. IMAGE CONTAINER SPECIFIC FIX (Prevent edge-hugging) */
/* ============================================================ */
.image-container .correlation-section,
.image-container .comments-block,
.image-container .anatomy-section {
  margin: 20px auto !important;       /* Centered with breathing room */
  width: calc(100% - 40px) !important; /* Not touching edges */
  max-width: 100% !important;
}

/* ============================================================ */
/* 8. CONTENT AREA SPACING (All note types) */
/* ============================================================ */
/* Ensures the main content area has proper padding */
.content-area {
  padding: 30px !important;           /* Comfortable padding around everything */
}

.cloze-content {
  padding: 25px !important;           /* Match other note types */
}

.mcq-content {
  padding: 25px !important;           /* Consistency */
}

.image-content {
  padding: 25px !important;           /* Consistency */
}

/* ============================================================ */
/* 9. MAIN CONTAINER WIDTHS (Prevent squeezing) */
/* ============================================================ */
/* Ensure all main containers have proper breathing room */
.card-container,
.cloze-container,
.mcq-container,
.image-container {
  width: 90vw !important;
  max-width: 1200px !important;       /* Comfortable max width */
  padding: 0 !important;              /* Remove conflicting padding */
  margin: 0 auto !important;          /* Center the container */
}

.card {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 2.5vh 2.5vw;
    box-sizing: border-box;
    display: flex; /* CRITICAL: Enables flex centering */
    align-items: center; /* CRITICAL: Vertical centering */
    justify-content: center; /* CRITICAL: Horizontal centering */
    min-height: 100vh; /* CRITICAL: Takes up full viewport height */
}

/* ============================================================ */
/* 11. CRITICAL CONSOLIDATED LAYOUT AND ANIMATION FIXES (GLOBAL) */
/* ============================================================ */
/* Global Bounce-In Animation (from all models) */
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

/* 11.1. BASIC Model Container & Elements (from basic_model custom block) */
.card-container {
    width: 90vw !important;
    max-width: 1100px !important;
    max-height: 90vh !important;
    overflow-y: auto !important;
    border-radius: 20px !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2) !important;
    overflow-x: hidden !important;
    animation: bounceIn 0.8s ease-out !important;
    display: flex !important;
    flex-direction: column !important;
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
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
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
.question-text, .answer-text {
    font-size: 1.2em;
    margin-bottom: 25px;
    text-align: center;
    font-weight: 500;
}
.custom-question, .custom-answer {
    font-weight: 600 !important;
    font-size: 1.2em !important;
}
.custom-explanation, .custom-correlation {
    font-weight: 500 !important;
    font-size: 1em !important;
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
}
.toggle-btn:hover {
    transform: translateY(-3px) scale(1.05);
}
.toggle-btn:active {
    transform: translateY(0);
}
.hidden {
    display: none !important;
}
.explanation-section:not(.hidden), .correlation-section:not(.hidden) {
    animation: slideDown 0.3s ease-out;
}
@keyframes slideDown {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* 11.2. CLOZE Model Container & Elements (from cloze_model custom block) */
.cloze-container {
    width: 90vw !important;
    max-width: 1200px !important;
    max-height: 90vh !important;
    overflow-y: auto !important;
    border-radius: 20px !important;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2) !important;
    overflow-x: hidden !important;
    animation: bounceIn 0.8s ease-out !important;
    display: flex !important;
    flex-direction: column !important;
}
.master-header {
        position: relative;
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
.cloze-content img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
    border-radius: 10px;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
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
.cloze {
    padding: 8px 16px;
    border-radius: 25px;
    display: inline-block;
    margin: 0 4px;
    position: relative;
    font-weight: bold;
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
    }
    .toggle-btn.extra-btn {
        background: linear-gradient(135deg, #f97316, #fb923c);
        box-shadow: 0 0 15px rgba(249, 115, 22, 0.4);
    }
    .extra-block:not(.hidden),
    .explanation-block:not(.hidden),
    .correlation-block:not(.hidden) {
        animation: slideDown 0.3s ease-out;
    }
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .hidden {
        display: none !important;
    }


/* 11.3. MCQ Model Container & Elements (from mcq_model custom block) */
.mcq-container {
    width: 90vw !important;
    max-width: 1000px !important;
    max-height: 90vh !important;
    overflow-y: auto !important;
    border-radius: 20px !important;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2) !important;
    overflow-x: hidden !important;
    animation: bounceIn 0.8s ease-out !important;
    display: flex !important;
    flex-direction: column !important;
}
.mcq-content img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
    border-radius: 10px;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
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
.mcq-title {
    font-size: 1.15em;
    font-weight: 500;
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

.option-a { --option-glow-1: #f472b6; --option-glow-2: #ec4899; border-color: #f472b6; }
.option-b { --option-glow-1: #34d399; --option-glow-2: #10b981; border-color: #34d399; }
.option-c { --option-glow-1: #60a5fa; --option-glow-2: #3b82f6; border-color: #60a5fa; }
.option-d { --option-glow-1: #a78bfa; --option-glow-2: #8b5cf6; border-color: #a78bfa; }

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

/* 11.4. IMAGE Model Container & Elements (from image_model custom block) */
.image-container {
    width: 90vw !important;
    max-width: 1200px !important;
    max-height: 90vh !important;
    overflow-y: auto !important;
    border-radius: 20px !important;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2) !important;
    overflow-x: hidden !important;
    animation: bounceIn 0.8s ease-out !important;
    display: flex !important;
    flex-direction: column !important;
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
.question-overlay, .answer-overlay {
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
.image-divider {
    border: none;
    height: 3px;
    background: linear-gradient(90deg, transparent, #74b9ff, transparent);
    margin: 25px 0;
}
.correlation-section:not(.hidden), .comments-block:not(.hidden) {
    animation: slideDown 0.3s ease-out;
}
.occlusion-wrapper {
    text-align: center;
}
.occlusion-wrapper img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
    border-radius: 15px;
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
}
'''

# ==============================================================================
# =================  ANKI MODEL DEFINITIONS (UNCHANGED) ========================
# ==============================================================================
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
        {{#Clinical Correlation}}<div class="correlation-section hidden" id="correlation"><div class="section-title">💉 Clinical Correlation</div><div class="correlation-text custom-correlation">{{Clinical Correlation}}</div></div>{{/Clinical Correlation}}
        <div class="toggle-controls">
            {{#Explanation}}<button onclick="toggleField('explanation')" class="toggle-btn explanation-btn">💡 <span class="toggle-text">Show Explanation</span></button>{{/Explanation}}
            {{#Clinical Correlation}}<button onclick="toggleField('correlation')" class="toggle-btn correlation-btn">💉 <span class="toggle-text">Show Clinical</span></button>{{/Clinical Correlation}}
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
   css=THEME_CSS + THEME_JS_FOUC_FIX + '''
'''
)

# Cloze model (FIXED)
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
                <div class="cloze-content">
                    {{cloze:Text}}
                </div>
                {{#Footer}}<div class="meta-footer"><span class="footer-icon">📖</span><span class="footer-text">{{Footer}}</span></div>{{/Footer}}
            </div>
            ''' + THEME_SCRIPT,
            # FIX: Changed class names from -info to -block to match the CSS styling.
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
                    
                    <!-- FIX #3: Added 'hidden' class to each field block -->
                    {{#Extra}}<div class="extra-block hidden" id="extra"><div class="section-title">📚 Additional Information</div><div class="extra-content custom-extra">{{Extra}}</div></div>{{/Extra}}
                    {{#Explanation}}<div class="explanation-block hidden" id="explanation"><div class="section-title">💡 Explanation</div><div class="explanation-content custom-explanation">{{Explanation}}</div></div>{{/Explanation}}
                    {{#Clinical Correlation}}<div class="correlation-block hidden" id="correlation"><div class="section-title">💉 Clinical Correlation</div><div class="correlation-content custom-correlation">{{Clinical Correlation}}</div></div>{{/Clinical Correlation}}
                    
                    <div class="toggle-controls">
                        {{#Extra}}<button onclick="toggleField('extra')" class="toggle-btn extra-btn">📚 <span class="toggle-text">Show Extra</span></button>{{/Extra}}
                        {{#Explanation}}<button onclick="toggleField('explanation')" class="toggle-btn explanation-btn">💡 <span class="toggle-text">Show Explanation</span></button>{{/Explanation}}
                        {{#Clinical Correlation}}<button onclick="toggleField('correlation')" class="toggle-btn correlation-btn">💉 <span class="toggle-text">Show Clinical</span></button>{{/Clinical Correlation}}
                        <button onclick="toggleAll()" class="toggle-btn showall-btn">👁️ <span id="toggleAllText">Show All</span></button>
                    </div>
                </div>
                {{#Footer}}<div class="meta-footer"><span class="footer-icon">📖</span><span class="footer-text">{{Footer}}</span></div>{{/Footer}}
                {{#Sources}}<div class="sources-section"><span class="sources-icon">🔗</span><span class="sources-text">{{Sources}}</span></div>{{/Sources}}
                
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
                        const fields = document.querySelectorAll('.extra-block, .explanation-block, .correlation-block');
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
   css=THEME_CSS + THEME_JS_FOUC_FIX + '''
'''
    ,
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
        {{#Clinical Correlation}}<div class="correlation-block hidden" id="correlation"><div class="block-title">💉 Clinical Correlation</div><div class="block-content custom-correlation">{{Clinical Correlation}}</div></div>{{/Clinical Correlation}}
        <div class="toggle-controls">
            {{#Explanation}}<button onclick="toggleField('explanation')" class="toggle-btn explanation-btn">💡 <span class="toggle-text">Show Explanation</span></button>{{/Explanation}}
            {{#Clinical Correlation}}<button onclick="toggleField('correlation')" class="toggle-btn correlation-btn">💉 <span class="toggle-text">Show Clinical</span></button>{{/Clinical Correlation}}
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
    css=THEME_CSS + THEME_JS_FOUC_FIX + '''
'''
)

# Image model 
image_model = Model(
    1607392322,
    'Joplin to Anki Image Enhanced',
    fields=[
        {'name': 'Header'},
        {'name': 'QuestionImagePath'},        # TEXT field - Your sync populates this
        {'name': 'AnswerImagePath'},          # TEXT field - Your sync populates this
        {'name': 'QuestionImageOcclusion'},   # IMAGE field - Users paste here (optional)
        {'name': 'AnswerImageOcclusion'},     # IMAGE field - Users paste here (optional)
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
        
        <!-- PRIORITY: Show occlusion image if exists, otherwise show synced path -->
        {{#QuestionImageOcclusion}}
        <div class="occlusion-wrapper">{{QuestionImageOcclusion}}</div>
        {{/QuestionImageOcclusion}}
        
        {{^QuestionImageOcclusion}}
        {{#QuestionImagePath}}
        <img src="{{QuestionImagePath}}" class="main-image">
        {{/QuestionImagePath}}
        {{/QuestionImageOcclusion}}
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
        
        <!-- PRIORITY: Show occlusion image if exists, otherwise show synced path -->
        {{#AnswerImageOcclusion}}
        <div class="occlusion-wrapper">{{AnswerImageOcclusion}}</div>
        {{/AnswerImageOcclusion}}
        
        {{^AnswerImageOcclusion}}
        {{#AnswerImagePath}}
        <img src="{{AnswerImagePath}}" class="main-image">
        {{/AnswerImagePath}}
        {{/AnswerImageOcclusion}}
    </div>
    {{#Clinical Correlation}}<div class="correlation-section hidden" id="correlation"><div class="section-title">💉 Clinical Correlation</div><div class="correlation-text custom-correlation">{{Clinical Correlation}}</div></div>{{/Clinical Correlation}}
    {{#Comments}}<div class="comments-block hidden" id="comments"><div class="comments-title">📝 Comments</div><div class="comments-text custom-comments">{{Comments}}</div></div>{{/Comments}}
    <div class="toggle-controls">
        {{#Clinical Correlation}}<button onclick="toggleField('correlation')" class="toggle-btn correlation-btn">💉 <span class="toggle-text">Show Clinical</span></button>{{/Clinical Correlation}}
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
    css=THEME_CSS + THEME_JS_FOUC_FIX + '''
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
    deck.add_note(Note(model=image_model, 
        fields=[ 'Anatomy - Upper Limb',
            '_media/question_deltoid.jpg',
            '_media/answer_deltoid.jpg',
            '', # Field 4: QuestionImageOcclusion (Placeholder)
            '', # Field 5: AnswerImageOcclusion (Placeholder)
            'Identify the highlighted muscle.',
            'Deltoid Muscle',
            'Lateral third of clavicle, acromion, and spine of scapula',
            'Deltoid tuberosity of humerus',
            'Axillary nerve (C5, C6)',
            'Abduction, flexion, and extension of the shoulder',
            'Axillary nerve damage can paralyze the deltoid.',
            'Key for arm abduction beyond 15 degrees.',
            'Shoulder Joint',
            'Gray\'s Anatomy', # Field 15: Sources (Previously missing)
            'joplin_image_v14_header' # Field 16: Joplin to Anki ID (Previously missing)
        ]))
        # Image without Header (tests large button & question text visibility)
    deck.add_note(Note(model=image_model, fields=[
            '',
            '_media/question_heart.jpg',
            '_media/answer_heart.jpg',
            '', # Field 4: QuestionImageOcclusion (Placeholder)
            '', # Field 5: AnswerImageOcclusion (Placeholder)
            'Identify the chamber indicated by the arrow.',
            'Left Ventricle',
            '',
            '',
            '',
            'Pumps oxygenated blood to the rest of the body via the aorta.',
            '',
            '',
            'Thoracic Cavity',
            '', # Field 15: Sources (Previously missing)
            'joplin_image_v14_noheader' # Field 16: Joplin to Anki ID (Previously missing)
        ]))

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

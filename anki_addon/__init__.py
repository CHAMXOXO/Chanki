# __init__.py - ENHANCED VERSION with Robust Persistence
# -*- coding: utf-8 -*-

from aqt import mw, gui_hooks
from aqt.qt import QAction, QMenu
from aqt.utils import tooltip, showInfo
from typing import Any, List, Dict, Optional
import json

# ==============================================================================
# CONFIGURATION
# ==============================================================================
ADDON_NAME = "JoplinSyncSuite"
THEME_KEY = f"{ADDON_NAME}_Theme_v1"
CONFIG_KEY = f"{ADDON_NAME}_config"

THEMES = [
    'light-full-moon', 'light-waning-gibbous', 'light-last-quarter', 'light-waning-crescent', 'light-new-moon',
    'nord-bright-sun', 'nord-overcast-day', 'nord-stormy-sky', 'nord-aurora', 'nord-polar-night',
    'balanced-star', 'balanced-nebula', 'balanced-supernova', 'balanced-galaxy', 'balanced-comet',
    'twilight-crescent-moon', 'twilight-city-night', 'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk',
    'dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 'dark-black-hole', 'dark-starless-sky'
]

# ==============================================================================
# ADVANCED THEME CSS
# ==============================================================================
THEME_CSS = """
/* Base Reset and Container Setup */
body.card {
    margin: 0 !important;
    padding: 20px !important;
    min-height: 100vh !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
    text-align: center !important;
}

/* =================================================================== */
/* =================== KEYFRAME ANIMATIONS =========================== */
/* =================================================================== */

@keyframes rotate-emoji {
    0% { transform: rotate(0deg); }
    50% { transform: rotate(60deg); }
    100% { transform: rotate(0deg); }
}

@keyframes pulse-button {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

@keyframes pulsating-glow {
    0% { text-shadow: 0 0 5px, 0 0 10px, 0 0 15px; }
    50% { text-shadow: 0 0 10px, 0 0 20px, 0 0 30px; }
    100% { text-shadow: 0 0 5px, 0 0 10px, 0 0 15px; }
}

/* =================================================================== */
/* =================== GENERIC ELEMENT STYLES ======================== */
/* =================================================================== */

.light-bulb-emoji {
    font-size: 0.8em !important;
    display: inline-block !important;
}

.cloze .emoji {
    display: inline-block;
    animation: rotate-emoji 3s infinite linear !important;
}

.card-container, .cloze-container, .mcq-container, .image-container {
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border-radius: 16px !important;
    padding: 25px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    margin-bottom: 20px !important;
}

.show-answer-button {
    padding: 12px 25px !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 16px !important;
    font-weight: bold !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    animation: pulse-button 2.5s infinite !important;
}

.show-answer-button:hover {
    transform: scale(1.1) !important;
    box-shadow: 0 0 15px, 0 0 25px !important;
}

.mcq-option {
    padding: 15px !important;
    margin: 8px 0 !important;
    border-radius: 10px !important;
    border: 1px solid transparent !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    cursor: pointer;
}

.mcq-option:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
}

.cloze {
    font-weight: bold !important;
    animation-name: pulsating-glow !important;
    animation-duration: 2s !important;
    animation-iteration-count: infinite !important;
}

/* =================================================================== */
/* =================== 🌕 FAMILY: LIGHT THEMES ======================= */
/* =================================================================== */

/* 1.1: light-full-moon */
body.theme-light-full-moon { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important; }
.theme-light-full-moon .card-container, .theme-light-full-moon .cloze-container, .theme-light-full-moon .mcq-container, .theme-light-full-moon .image-container { background: rgba(255, 255, 255, 0.7) !important; color: #3a3a3a !important; }
.theme-light-full-moon .show-answer-button { background-color: #4a5568 !important; color: #f7fafc !important; }
.theme-light-full-moon .show-answer-button:hover { box-shadow: 0 0 15px #4a5568 !important; }
.theme-light-full-moon .cloze { color: #2c5282 !important; }
.theme-light-full-moon .mcq-option:nth-of-type(1) { background: #e2e8f0 !important; color: #2d3748 !important; }
.theme-light-full-moon .mcq-option:nth-of-type(2) { background: #d2f0ea !important; color: #234e52 !important; }
.theme-light-full-moon .mcq-option:nth-of-type(3) { background: #e1e3f8 !important; color: #303162 !important; }

/* 1.2: light-waning-gibbous */
body.theme-light-waning-gibbous { background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%) !important; }
.theme-light-waning-gibbous .card-container, .theme-light-waning-gibbous .cloze-container, .theme-light-waning-gibbous .mcq-container, .theme-light-waning-gibbous .image-container { background: rgba(255, 255, 255, 0.75) !important; color: #5c4033 !important; }
.theme-light-waning-gibbous .show-answer-button { background-color: #dd6b20 !important; color: #fffaf0 !important; }
.theme-light-waning-gibbous .show-answer-button:hover { box-shadow: 0 0 15px #dd6b20 !important; }
.theme-light-waning-gibbous .cloze { color: #c05621 !important; }
.theme-light-waning-gibbous .mcq-option:nth-of-type(1) { background: #fed7d7 !important; color: #742a2a !important; }
.theme-light-waning-gibbous .mcq-option:nth-of-type(2) { background: #feebc8 !important; color: #744210 !important; }
.theme-light-waning-gibbous .mcq-option:nth-of-type(3) { background: #fefcbf !important; color: #744210 !important; }

/* =================================================================== */
/* =================== 🪐 FAMILY: DARK THEMES ======================== */
/* =================================================================== */

/* 5.1: dark-saturn */
body.theme-dark-saturn { background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%) !important; }
.theme-dark-saturn .card-container, .theme-dark-saturn .cloze-container, .theme-dark-saturn .mcq-container, .theme-dark-saturn .image-container { background: rgba(30, 30, 40, 0.75) !important; color: #e0e0e0 !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
.theme-dark-saturn .show-answer-button { background-color: #9f7aea !important; color: #1a202c !important; }
.theme-dark-saturn .show-answer-button:hover { box-shadow: 0 0 15px #9f7aea !important; }
.theme-dark-saturn .cloze { color: #d6bcfa !important; }
.theme-dark-saturn .mcq-option:nth-of-type(1) { background: #2d3748 !important; color: #e2e8f0 !important; }
.theme-dark-saturn .mcq-option:nth-of-type(2) { background: #4a5568 !important; color: #e2e8f0 !important; }
.theme-dark-saturn .mcq-option:nth-of-type(3) { background: #1a202c !important; color: #e2e8f0 !important; }

/* 5.2: dark-mars-rover */
body.theme-dark-mars-rover { background: linear-gradient(135deg, #200122 0%, #6f0000 100%) !important; }
.theme-dark-mars-rover .card-container, .theme-dark-mars-rover .cloze-container, .theme-dark-mars-rover .mcq-container, .theme-dark-mars-rover .image-container { background: rgba(40, 20, 30, 0.8) !important; color: #f7fafc !important; border: 1px solid rgba(255, 100, 100, 0.15) !important; }
.theme-dark-mars-rover .show-answer-button { background-color: #e53e3e !important; color: #fff5f5 !important; }
.theme-dark-mars-rover .show-answer-button:hover { box-shadow: 0 0 15px #e53e3e !important; }
.theme-dark-mars-rover .cloze { color: #fed7d7 !important; }
.theme-dark-mars-rover .mcq-option:nth-of-type(1) { background: #4a1d1d !important; color: #fed7d7 !important; }
.theme-dark-mars-rover .mcq-option:nth-of-type(2) { background: #692c2c !important; color: #fed7d7 !important; }
.theme-dark-mars-rover .mcq-option:nth-of-type(3) { background: #230122 !important; color: #f7fafc !important; }

/* 5.3: dark-neptune-deep */
body.theme-dark-neptune-deep { background: linear-gradient(135deg, #051937 0%, #004d7a 50%, #008793 100%) !important; }
.theme-dark-neptune-deep .card-container, .theme-dark-neptune-deep .cloze-container, .theme-dark-neptune-deep .mcq-container, .theme-dark-neptune-deep .image-container { background: rgba(10, 30, 50, 0.8) !important; color: #cbeef3 !important; border: 1px solid rgba(100, 200, 255, 0.2) !important; }
.theme-dark-neptune-deep .show-answer-button { background-color: #38b2ac !important; color: #051937 !important; }
.theme-dark-neptune-deep .show-answer-button:hover { box-shadow: 0 0 15px #38b2ac !important; }
.theme-dark-neptune-deep .cloze { color: #81e6d9 !important; }
.theme-dark-neptune-deep .mcq-option:nth-of-type(1) { background: #003a5c !important; color: #b2f5ea !important; }
.theme-dark-neptune-deep .mcq-option:nth-of-type(2) { background: #00607a !important; color: #b2f5ea !important; }
.theme-dark-neptune-deep .mcq-option:nth-of-type(3) { background: #022c47 !important; color: #b2f5ea !important; }

/* 5.4: dark-black-hole */
body.theme-dark-black-hole { background: radial-gradient(circle at center, #0a0a0a 0%, #000000 100%) !important; }
.theme-dark-black-hole .card-container, .theme-dark-black-hole .cloze-container, .theme-dark-black-hole .mcq-container, .theme-dark-black-hole .image-container { background: rgba(15, 15, 15, 0.8) !important; color: #a0aec0 !important; border: 1px solid rgba(255, 255, 255, 0.05) !important; }
.theme-dark-black-hole .show-answer-button { background-color: #718096 !important; color: #000000 !important; }
.theme-dark-black-hole .show-answer-button:hover { box-shadow: 0 0 15px #718096 !important; }
.theme-dark-black-hole .cloze { color: #e2e8f0 !important; }
.theme-dark-black-hole .mcq-option:nth-of-type(1) { background: #2d3748 !important; color: #cbd5e0 !important; }
.theme-dark-black-hole .mcq-option:nth-of-type(2) { background: #1a202c !important; color: #cbd5e0 !important; }
.theme-dark-black-hole .mcq-option:nth-of-type(3) { background: #111827 !important; color: #cbd5e0 !important; }

/* 5.5: dark-starless-sky */
body.theme-dark-starless-sky { background: linear-gradient(135deg, #000000 0%, #0a0a0a 100%) !important; }
.theme-dark-starless-sky .card-container, .theme-dark-starless-sky .cloze-container, .theme-dark-starless-sky .mcq-container, .theme-dark-starless-sky .image-container { background: rgba(20, 20, 20, 0.85) !important; color: #edf2f7 !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
.theme-dark-starless-sky .show-answer-button { background-color: #edf2f7 !important; color: #1a202c !important; }
.theme-dark-starless-sky .show-answer-button:hover { box-shadow: 0 0 15px #edf2f7 !important; }
.theme-dark-starless-sky .cloze { color: #a0aec0 !important; }
.theme-dark-starless-sky .mcq-option:nth-of-type(1) { background: #4a5568 !important; color: #f7fafc !important; }
.theme-dark-starless-sky .mcq-option:nth-of-type(2) { background: #2d3748 !important; color: #f7fafc !important; }
.theme-dark-starless-sky .mcq-option:nth-of-type(3) { background: #171923 !important; color: #f7fafc !important; }
"""

# ==============================================================================
# ENHANCED THEME JAVASCRIPT WITH PERSISTENCE
# ==============================================================================
THEME_SCRIPT = """
(function() {
    'use strict';
    
    // --- Configuration ---
    const THEME_FAMILIES = {
        'light': ['light-full-moon', 'light-waning-gibbous', 'light-last-quarter', 'light-waning-crescent', 'light-new-moon'],
        'nord': ['nord-bright-sun', 'nord-overcast-day', 'nord-stormy-sky', 'nord-aurora', 'nord-polar-night'],
        'balanced': ['balanced-star', 'balanced-nebula', 'balanced-supernova', 'balanced-galaxy', 'balanced-comet'],
        'twilight': ['twilight-crescent-moon', 'twilight-city-night', 'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk'],
        'dark': ['dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 'dark-black-hole', 'dark-starless-sky']
    };
    const ALL_THEMES = Object.values(THEME_FAMILIES).flat();
    const THEME_KEY = 'JoplinSyncSuite_Theme_v1';
    
    let currentTheme = null;
    let initCount = 0;
    
    // --- Enhanced Theme Application ---
    function applyTheme(theme, source) {
        if (!theme || !ALL_THEMES.includes(theme)) {
            theme = 'light-full-moon';
        }
        
        // Prevent redundant applications
        if (currentTheme === theme && initCount > 0) {
            console.log('[JoplinSync] Theme already applied:', theme);
            return;
        }
        
        console.log('[JoplinSync] Applying theme:', theme, 'from:', source);
        
        const body = document.body;
        
        // Remove all theme classes efficiently
        const classesToRemove = Array.from(body.classList).filter(c => c.startsWith('theme-'));
        classesToRemove.forEach(c => body.classList.remove(c));
        
        // Add the new theme class
        body.classList.add('theme-' + theme);
        
        // Ensure card class is present
        if (!body.classList.contains('card')) {
            body.classList.add('card');
        }
        
        // Force style recalculation
        void body.offsetHeight;
        
        currentTheme = theme;
        console.log('[JoplinSync] Theme applied successfully. Classes:', body.className);
        
        // Persist to localStorage
        saveThemeToLocal(theme);
        
        return true;
    }
    
    // --- Multi-source Theme Loading with Priority ---
    function loadTheme() {
        // Priority 1: Server-injected meta tag (from Python)
        const metaTheme = document.querySelector('meta[name="anki-theme"]');
        if (metaTheme && metaTheme.content && ALL_THEMES.includes(metaTheme.content)) {
            console.log('[JoplinSync] Theme from meta tag:', metaTheme.content);
            return metaTheme.content;
        }
        
        // Priority 2: Check if pycmd is available (Anki bridge)
        if (typeof pycmd !== 'undefined') {
            // Theme will be set via meta tag on next card load
            console.log('[JoplinSync] pycmd available, waiting for meta tag');
        }
        
        // Priority 3: localStorage (client-side persistence)
        try {
            const localTheme = localStorage.getItem(THEME_KEY);
            if (localTheme && ALL_THEMES.includes(localTheme)) {
                console.log('[JoplinSync] Theme from localStorage:', localTheme);
                return localTheme;
            }
        } catch(e) {
            console.warn('[JoplinSync] localStorage not available:', e);
        }
        
        // Priority 4: Default fallback
        console.log('[JoplinSync] Using default theme');
        return 'light-full-moon';
    }
    
    // --- Save theme to localStorage ---
    function saveThemeToLocal(theme) {
        try {
            localStorage.setItem(THEME_KEY, theme);
            console.log('[JoplinSync] Theme persisted to localStorage:', theme);
        } catch(e) {
            console.warn('[JoplinSync] Could not save theme to localStorage:', e);
        }
    }
    
    // --- Notify Python backend of theme change (modern bridge method) ---
    function notifyPython(theme) {
        try {
            // Modern Anki 2.1.50+ bridge method
            if (typeof bridgeCommand !== 'undefined') {
                bridgeCommand('joplinsync_theme:' + theme);
                console.log('[JoplinSync] Notified Python via bridge:', theme);
            }
            // Fallback to pycmd for older versions
            else if (typeof pycmd !== 'undefined') {
                pycmd('joplinsync_theme:' + theme);
                console.log('[JoplinSync] Notified Python via pycmd:', theme);
            }
        } catch(e) {
            console.warn('[JoplinSync] Could not notify Python:', e);
        }
    }
    
    // --- Initialization with persistence ---
    function initTheme() {
        initCount++;
        const themeToApply = loadTheme();
        console.log('[JoplinSync] Init #' + initCount + ' with theme:', themeToApply);
        const applied = applyTheme(themeToApply, 'init-' + initCount);
        
        if (applied && initCount === 1) {
            // First successful init, ensure it's synced
            notifyPython(themeToApply);
        }
    }
    
    // --- Make globally available ---
    window.applyTheme = function(theme) {
        return applyTheme(theme, 'external-call');
    };
    window.loadTheme = loadTheme;
    window.getCurrentTheme = function() { return currentTheme; };
    
    // --- Robust initialization sequence ---
    
    // Method 1: Immediate execution
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }
    
    // Method 2: Window load event
    window.addEventListener('load', function() {
        if (initCount === 0) initTheme();
    });
    
    // Method 3: Delayed fallbacks for reliability
    setTimeout(function() {
        if (initCount === 0) initTheme();
    }, 0);
    
    setTimeout(function() {
        if (initCount < 2) initTheme();
    }, 100);
    
    setTimeout(function() {
        if (initCount < 3) initTheme();
    }, 300);
    
    // Method 4: Listen for Anki's card show events
    if (typeof AnkiCardShown !== 'undefined') {
        document.addEventListener('AnkiCardShown', initTheme);
    }
    
    console.log('[JoplinSync] Theme script loaded and initialized');
})();
"""

# ==============================================================================
# ENHANCED PERSISTENCE FUNCTIONS
# ==============================================================================
def get_theme() -> str:
    """Gets the saved theme with multiple fallback mechanisms."""
    theme = None
    
    # Method 1: Anki collection config (primary storage)
    try:
        if mw and mw.col:
            theme = mw.col.conf.get(THEME_KEY)
            if theme and theme in THEMES:
                return theme
    except Exception as e:
        print(f"[JoplinSync] Error reading from col.conf: {e}")
    
    # Method 2: Addon config (secondary storage)
    try:
        config = mw.addonManager.getConfig(__name__)
        if config and 'theme' in config:
            theme = config['theme']
            if theme in THEMES:
                # Sync back to col.conf
                save_theme(theme)
                return theme
    except Exception as e:
        print(f"[JoplinSync] Error reading addon config: {e}")
    
    # Method 3: Default fallback
    default_theme = 'light-full-moon'
    save_theme(default_theme)
    return default_theme

def save_theme(theme: str, sync_to_all: bool = True):
    """Saves the selected theme to multiple storage locations for redundancy."""
    if theme not in THEMES:
        print(f"[JoplinSync] Invalid theme: {theme}")
        return False
    
    success = False
    
    # Storage 1: Anki collection config (survives profile switches)
    try:
        if mw and mw.col:
            mw.col.conf[THEME_KEY] = theme
            mw.col.setMod()
            success = True
            print(f"[JoplinSync] Theme saved to col.conf: {theme}")
    except Exception as e:
        print(f"[JoplinSync] Error saving to col.conf: {e}")
    
    # Storage 2: Addon config (additional redundancy)
    if sync_to_all:
        try:
            config = mw.addonManager.getConfig(__name__) or {}
            config['theme'] = theme
            mw.addonManager.writeConfig(__name__, config)
            print(f"[JoplinSync] Theme saved to addon config: {theme}")
        except Exception as e:
            print(f"[JoplinSync] Error saving addon config: {e}")
    
    return success

def is_dark_theme(theme_name: str) -> bool:
    """Determines if a theme should use dark mode."""
    dark_themes = {
        'nord-stormy-sky', 'nord-polar-night',
        'balanced-star', 'balanced-nebula', 'balanced-galaxy',
        'twilight-crescent-moon', 'twilight-city-night', 
        'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk',
        'dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 
        'dark-black-hole', 'dark-starless-sky'
    }
    return theme_name in dark_themes

def apply_global_theme(theme_name: str, show_tooltip: bool = True):
    """Saves the theme and updates Anki's UI with enhanced persistence."""
    if theme_name not in THEMES:
        print(f"[JoplinSync] Invalid theme: {theme_name}")
        return
    
    # Save with full redundancy
    if not save_theme(theme_name, sync_to_all=True):
        if show_tooltip:
            tooltip("⚠️ Failed to save theme", period=2000)
        return
    
    # Determine if we need dark mode
    needs_dark = is_dark_theme(theme_name)
    
    # Update Anki's night mode
    try:
        from aqt.theme import theme_manager
        if hasattr(theme_manager, 'night_mode'):
            if theme_manager.night_mode != needs_dark:
                theme_manager.night_mode = needs_dark
                print(f"[JoplinSync] Night mode set to: {needs_dark}")
    except Exception as e:
        print(f"[JoplinSync] Error setting night mode: {e}")
    
    # Force JavaScript to apply theme immediately if in review
    if mw.state == "review" and hasattr(mw.reviewer, 'web'):
        try:
            js_code = f"""
                (function() {{
                    console.log('[JoplinSync] Applying theme via Python injection: {theme_name}');
                    if (typeof applyTheme === 'function') {{
                        applyTheme('{theme_name}');
                    }} else {{
                        console.error('[JoplinSync] applyTheme function not found');
                    }}
                }})();
            """
            mw.reviewer.web.eval(js_code)
            print(f"[JoplinSync] JavaScript theme application triggered")
        except Exception as e:
            print(f"[JoplinSync] Error applying theme via JS: {e}")
    
    # Refresh reviewer if active
    if mw.state == "review":
        try:
            mw.reviewer.refresh()
            print(f"[JoplinSync] Reviewer refreshed")
        except Exception as e:
            print(f"[JoplinSync] Error refreshing reviewer: {e}")
    
    if show_tooltip:
        tooltip(f"✨ Theme: {theme_name.replace('-', ' ').title()}", period=2000)
    
    print(f"[JoplinSync] Theme applied globally: {theme_name}")

# ==============================================================================
# INJECTION HOOK WITH ENHANCED METADATA
# ==============================================================================
def inject_theme_assets(html: str, card: Any, context: Any) -> str:
    """Injects CSS, JS, and meta tag into the card's HTML with cache-busting."""
    theme = get_theme()
    
    # Cache-busting timestamp to force refresh
    import time
    cache_buster = int(time.time() * 1000)  # milliseconds timestamp
    
    # Create comprehensive injection payload with cache busting
    injection_payload = f'''
<meta name="anki-theme" content="{theme}">
<meta name="anki-theme-version" content="1.0.{cache_buster}">
<meta name="anki-theme-timestamp" content="{cache_buster}">
<style id="joplin-theme-css-{cache_buster}">
{THEME_CSS}
</style>
<script id="joplin-theme-script-{cache_buster}">
{THEME_SCRIPT}
</script>
'''
    
    # Inject before </head> if exists, otherwise at the beginning
    if "</head>" in html:
        html = html.replace("</head>", f"{injection_payload}</head>", 1)
    else:
        html = injection_payload + html
    
    return html

# Register the injection hook
gui_hooks.card_will_show.append(inject_theme_assets)

# ==============================================================================
# PYCMD BRIDGE FOR BIDIRECTIONAL COMMUNICATION
# ==============================================================================
def handle_theme_message(handled: tuple, message: str, context: Any) -> tuple:
    """Handles theme change messages from JavaScript."""
    if message.startswith("joplinsync_theme:"):
        theme = message.replace("joplinsync_theme:", "")
        if theme in THEMES:
            save_theme(theme, sync_to_all=True)
            print(f"[JoplinSync] Theme updated from JS: {theme}")
        return (True, None)
    return handled

# Register the message handler
gui_hooks.webview_did_receive_js_message.append(handle_theme_message)

# ==============================================================================
# MENU CREATION WITH PERSISTENCE INDICATOR
# ==============================================================================
_MENU_CREATED = False

def setup_theme_menu():
    """Builds and adds the 'Themes' menu to Anki's Tools menu."""
    global _MENU_CREATED
    
    if _MENU_CREATED:
        return
    
    theme_families: Dict[str, List[str]] = {
        'Light 🌕': [t for t in THEMES if t.startswith('light-')],
        'Nord ❄️': [t for t in THEMES if t.startswith('nord-')],
        'Balanced ⭐': [t for t in THEMES if t.startswith('balanced-')],
        'Twilight 🌙': [t for t in THEMES if t.startswith('twilight-')],
        'Dark 🪐': [t for t in THEMES if t.startswith('dark-')]
    }
    
    # Create main menu
    main_menu = QMenu("🎨 Chanki Themes", mw)
    
    # Add current theme indicator with persistence status
    current_theme = get_theme()
    current_display = f"✓ Current: {current_theme.replace('-', ' ').title()}"
    current_action = QAction(current_display, mw)
    current_action.setEnabled(False)
    main_menu.addAction(current_action)
    main_menu.addSeparator()
    
    # Add theme families
    for family_name, theme_list in theme_families.items():
        sub_menu = QMenu(family_name, mw)
        for theme_name in theme_list:
            display_name = theme_name.replace(theme_name.split('-')[0] + '-', '').replace('-', ' ').title()
            action = QAction(display_name, mw)
            # Add checkmark for current theme
            if theme_name == current_theme:
                action.setCheckable(True)
                action.setChecked(True)
            action.triggered.connect(lambda checked, name=theme_name: apply_global_theme(name))
            sub_menu.addAction(action)
        main_menu.addMenu(sub_menu)
    
    # Add utility actions
    main_menu.addSeparator()
    
    # Reset to default action
    reset_action = QAction("🔄 Reset to Default", mw)
    reset_action.triggered.connect(lambda: apply_global_theme('light-full-moon'))
    main_menu.addAction(reset_action)
    
    # Force refresh action
    refresh_action = QAction("⚡ Force Refresh Theme", mw)
    refresh_action.triggered.connect(force_refresh_theme)
    main_menu.addAction(refresh_action)
    
    # Add to Tools menu
    mw.form.menuTools.addSeparator()
    mw.form.menuTools.addMenu(main_menu)
    
    _MENU_CREATED = True
    print("[JoplinSync] Theme menu created")

def force_refresh_theme():
    """Forces a complete theme refresh across all components."""
    current_theme = get_theme()
    print(f"[JoplinSync] Force refreshing theme: {current_theme}")
    
    # Re-save to all storage locations
    save_theme(current_theme, sync_to_all=True)
    
    # Re-apply globally
    apply_global_theme(current_theme, show_tooltip=False)
    
    tooltip(f"🔄 Theme Refreshed: {current_theme.replace('-', ' ').title()}", period=2000)

# ==============================================================================
# PROFILE CHANGE HANDLER - Ensures persistence across profiles
# ==============================================================================
def on_profile_loaded():
    """Reapplies theme when profile is loaded."""
    try:
        theme = get_theme()
        needs_dark = is_dark_theme(theme)
        
        # Apply night mode setting
        try:
            from aqt.theme import theme_manager
            if hasattr(theme_manager, 'night_mode'):
                theme_manager.night_mode = needs_dark
        except:
            pass
        
        print(f"[JoplinSync] Profile loaded, theme restored: {theme}")
    except Exception as e:
        print(f"[JoplinSync] Error in profile load: {e}")

# Register profile load hook
gui_hooks.profile_did_open.append(on_profile_loaded)

# ==============================================================================
# COLLECTION LOAD HANDLER - Ensures persistence on collection load
# ==============================================================================
def on_collection_loaded(col):
    """Ensures theme is synced when collection loads."""
    try:
        theme = get_theme()
        print(f"[JoplinSync] Collection loaded, theme confirmed: {theme}")
    except Exception as e:
        print(f"[JoplinSync] Error in collection load: {e}")

# Register collection load hook (if available in Anki 25.09+)
try:
    gui_hooks.collection_did_load.append(on_collection_loaded)
except AttributeError:
    print("[JoplinSync] collection_did_load hook not available")

# ==============================================================================
# REVIEWER STATE CHANGE HANDLER - Reapplies theme on state changes
# ==============================================================================
def on_reviewer_state_change(state: str, *args):
    """Reapplies theme when reviewer state changes."""
    if state == "review":
        try:
            theme = get_theme()
            if hasattr(mw.reviewer, 'web'):
                js_code = f"""
                    setTimeout(function() {{
                        if (typeof applyTheme === 'function') {{
                            console.log('[JoplinSync] Reapplying theme on state change: {theme}');
                            applyTheme('{theme}');
                        }}
                    }}, 50);
                """
                mw.reviewer.web.eval(js_code)
        except Exception as e:
            print(f"[JoplinSync] Error in state change: {e}")

# Register state change hook
gui_hooks.state_did_change.append(on_reviewer_state_change)

# ==============================================================================
# INITIALIZATION WITH ENHANCED PERSISTENCE
# ==============================================================================
def init_addon():
    """Initialize the addon with enhanced persistence mechanisms."""
    try:
        print("[JoplinSync] Initializing addon...")
        
        # Ensure theme is properly saved in all locations
        theme = get_theme()
        save_theme(theme, sync_to_all=True)
        
        # Apply night mode based on theme
        needs_dark = is_dark_theme(theme)
        try:
            from aqt.theme import theme_manager
            if hasattr(theme_manager, 'night_mode'):
                theme_manager.night_mode = needs_dark
                print(f"[JoplinSync] Night mode initialized: {needs_dark}")
        except Exception as e:
            print(f"[JoplinSync] Could not set night mode: {e}")
        
        # Setup menu
        setup_theme_menu()
        
        print(f"[JoplinSync] ✓ Addon initialized successfully with theme: {theme}")
        
    except Exception as e:
        print(f"[JoplinSync] ✗ Init error: {e}")
        import traceback
        traceback.print_exc()

# Register initialization with multiple hooks for reliability
gui_hooks.main_window_did_init.append(init_addon)

print("[JoplinSync] ✓ Theme addon loaded with enhanced persistence")

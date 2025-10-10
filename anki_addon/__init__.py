# __init__.py (COMPLETE FIX for Anki 24.09+ / 25.09+)
# -*- coding: utf-8 -*-

# --- IMPORTS ---
from aqt import mw, gui_hooks
from aqt.qt import QAction, QMenu
from aqt.utils import tooltip
from typing import Any, List, Dict
import json

# ==============================================================================
# ========================  STEP 1: CENTRAL CONFIGURATION ======================
# ==============================================================================
ADDON_NAME = "JoplinSyncSuite"
THEME_KEY = f"{ADDON_NAME}_Theme_v1"
STYLE_INJECTED_KEY = f"{ADDON_NAME}_Style_Injected"

THEMES = [
    'light-full-moon', 'light-waning-gibbous', 'light-last-quarter', 'light-waning-crescent', 'light-new-moon',
    'nord-bright-sun', 'nord-overcast-day', 'nord-stormy-sky', 'nord-aurora', 'nord-polar-night',
    'balanced-star', 'balanced-nebula', 'balanced-supernova', 'balanced-galaxy', 'balanced-comet',
    'twilight-crescent-moon', 'twilight-city-night', 'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk',
    'dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 'dark-black-hole', 'dark-starless-sky'
]

# --- COMPLETE THEME CSS (Including all themes) ---
THEME_CSS = """
/* Base Reset and Container Setup */
body.card {
    margin: 0;
    padding: 20px;
    min-height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* =================================================================== */
/* =================== 🌕 FAMILY: LIGHT THEMES ======================= */
/* =================================================================== */

/* 1.1: light-full-moon (Original Light) */
body.theme-light-full-moon {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
}
.theme-light-full-moon .card-container,
.theme-light-full-moon .cloze-container,
.theme-light-full-moon .mcq-container,
.theme-light-full-moon .image-container {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(12px);
    color: #433865;
    border: 1px solid rgba(226, 232, 240, 0.9);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
}

/* 1.2: light-waning-gibbous */
body.theme-light-waning-gibbous {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%) !important;
}

/* 1.3: light-last-quarter */
body.theme-light-last-quarter {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%) !important;
}

/* 1.4: light-waning-crescent */
body.theme-light-waning-crescent {
    background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%) !important;
}

/* 1.5: light-new-moon */
body.theme-light-new-moon {
    background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%) !important;
}

/* =================================================================== */
/* =================== ❄️ FAMILY: NORD THEMES ======================== */
/* =================================================================== */

/* 2.1: nord-bright-sun */
body.theme-nord-bright-sun {
    background: linear-gradient(135deg, #ECEFF4 0%, #D8DEE9 100%) !important;
}

/* 2.2: nord-overcast-day */
body.theme-nord-overcast-day {
    background: linear-gradient(135deg, #E5E9F0 0%, #D8DEE9 50%, #ECEFF4 100%) !important;
}

/* 2.3: nord-stormy-sky */
body.theme-nord-stormy-sky {
    background: linear-gradient(135deg, #4C566A 0%, #434C5E 50%, #3B4252 100%) !important;
}

/* 2.4: nord-aurora */
body.theme-nord-aurora {
    background: linear-gradient(135deg, #BF616A 0%, #D08770 25%, #EBCB8B 50%, #A3BE8C 75%, #B48EAD 100%) !important;
}

/* 2.5: nord-polar-night */
body.theme-nord-polar-night {
    background: linear-gradient(135deg, #2E3440 0%, #3B4252 50%, #434C5E 100%) !important;
}

/* =================================================================== */
/* =================== ⭐ FAMILY: BALANCED THEMES ==================== */
/* =================================================================== */

/* 3.1: balanced-star */
body.theme-balanced-star {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

/* 3.2: balanced-nebula */
body.theme-balanced-nebula {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
}

/* 3.3: balanced-supernova */
body.theme-balanced-supernova {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%) !important;
}

/* 3.4: balanced-galaxy */
body.theme-balanced-galaxy {
    background: linear-gradient(135deg, #30cfd0 0%, #330867 100%) !important;
}

/* 3.5: balanced-comet */
body.theme-balanced-comet {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%) !important;
}

/* =================================================================== */
/* =================== 🌙 FAMILY: TWILIGHT THEMES ==================== */
/* =================================================================== */

/* 4.1: twilight-crescent-moon */
body.theme-twilight-crescent-moon {
    background: linear-gradient(135deg, #2D3748 0%, #1A202C 100%) !important;
}

/* 4.2: twilight-city-night */
body.theme-twilight-city-night {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important;
}

/* 4.3: twilight-deep-forest */
body.theme-twilight-deep-forest {
    background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%) !important;
}

/* 4.4: twilight-moonlit-ocean */
body.theme-twilight-moonlit-ocean {
    background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%) !important;
}

/* 4.5: twilight-dusk */
body.theme-twilight-dusk {
    background: linear-gradient(135deg, #141e30 0%, #243b55 100%) !important;
}

/* =================================================================== */
/* =================== 🪐 FAMILY: DARK THEMES ======================== */
/* =================================================================== */

/* 5.1: dark-saturn */
body.theme-dark-saturn {
    background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%) !important;
}

/* 5.2: dark-mars-rover */
body.theme-dark-mars-rover {
    background: linear-gradient(135deg, #200122 0%, #6f0000 100%) !important;
}

/* 5.3: dark-neptune-deep */
body.theme-dark-neptune-deep {
    background: linear-gradient(135deg, #051937 0%, #004d7a 50%, #008793 100%) !important;
}

/* 5.4: dark-black-hole */
body.theme-dark-black-hole {
    background: radial-gradient(circle at center, #0a0a0a 0%, #000000 100%) !important;
}

/* 5.5: dark-starless-sky */
body.theme-dark-starless-sky {
    background: linear-gradient(135deg, #000000 0%, #0a0a0a 100%) !important;
}

/* Container styles for dark themes */
.theme-nord-stormy-sky .card-container,
.theme-nord-polar-night .card-container,
.theme-balanced-star .card-container,
.theme-balanced-nebula .card-container,
.theme-balanced-galaxy .card-container,
.theme-twilight-crescent-moon .card-container,
.theme-twilight-city-night .card-container,
.theme-twilight-deep-forest .card-container,
.theme-twilight-moonlit-ocean .card-container,
.theme-twilight-dusk .card-container,
.theme-dark-saturn .card-container,
.theme-dark-mars-rover .card-container,
.theme-dark-neptune-deep .card-container,
.theme-dark-black-hole .card-container,
.theme-dark-starless-sky .card-container {
    background: rgba(30, 30, 40, 0.95);
    color: #e0e0e0;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Add more specific styles for headers, text, etc. as needed */
"""

# --- ENHANCED THEME SCRIPT ---
THEME_SCRIPT = """
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

// --- Enhanced Theme Application ---
function applyTheme(theme) {
    if (!theme || !ALL_THEMES.includes(theme)) {
        theme = 'light-full-moon';
    }
    
    // Remove all theme classes
    document.body.classList.forEach(c => {
        if (c.startsWith('theme-')) {
            document.body.classList.remove(c);
        }
    });
    
    // Add the new theme class
    document.body.classList.add('theme-' + theme);
    
    // Ensure card class is present
    if (!document.body.classList.contains('card')) {
        document.body.classList.add('card');
    }
    
    // Force style recalculation
    document.body.style.display = 'none';
    document.body.offsetHeight; // Trigger reflow
    document.body.style.display = '';
}

// --- Enhanced Storage Function ---
function loadTheme() {
    // First check meta tag (from server)
    const metaTheme = document.querySelector('meta[name="anki-theme"]');
    if (metaTheme && metaTheme.content && ALL_THEMES.includes(metaTheme.content)) {
        return metaTheme.content;
    }
    
    // Then check localStorage
    try {
        const localTheme = localStorage.getItem(THEME_KEY);
        if (localTheme && ALL_THEMES.includes(localTheme)) {
            return localTheme;
        }
    } catch(e) {
        console.warn('localStorage not available:', e);
    }
    
    return 'light-full-moon';
}

// --- Save theme to localStorage ---
function saveThemeToLocal(theme) {
    try {
        localStorage.setItem(THEME_KEY, theme);
    } catch(e) {
        console.warn('Could not save theme to localStorage:', e);
    }
}

// --- Initialization with persistence ---
function initTheme() {
    const themeToApply = loadTheme();
    applyTheme(themeToApply);
    saveThemeToLocal(themeToApply);
}

// --- Multiple initialization points for reliability ---
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
} else {
    initTheme();
}

// Anki-specific events
window.addEventListener('ankiCardShown', initTheme);
window.addEventListener('load', initTheme);

// Also run immediately
setTimeout(initTheme, 0);
setTimeout(initTheme, 100);
"""

# ==============================================================================
# =======================  STEP 2: CORE THEME LOGIC ============================
# ==============================================================================
def get_theme() -> str:
    """Gets the saved theme from Anki's configuration."""
    return mw.col.conf.get(THEME_KEY, 'light-full-moon')

def save_theme(theme: str):
    """Saves the selected theme to Anki's configuration if it's valid."""
    if theme in THEMES:
        mw.col.conf[THEME_KEY] = theme
        mw.col.setMod()
        # Also save to profile config for persistence
        mw.pm.profile['joplin_theme'] = theme
        mw.pm.save()

def is_dark_theme(theme_name: str) -> bool:
    """Determines if a theme should use dark mode."""
    dark_themes = [
        'nord-stormy-sky', 'nord-polar-night',
        'balanced-star', 'balanced-nebula', 'balanced-galaxy',
        'twilight-crescent-moon', 'twilight-city-night', 
        'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk',
        'dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 
        'dark-black-hole', 'dark-starless-sky'
    ]
    return theme_name in dark_themes

def apply_global_theme(theme_name: str):
    """Saves the theme and updates Anki's UI."""
    save_theme(theme_name)
    
    # Determine if we need dark mode
    needs_dark = is_dark_theme(theme_name)
    
    # Try modern Anki API first (25.09+)
    try:
        from aqt.theme import theme_manager
        if theme_manager.night_mode != needs_dark:
            theme_manager.night_mode = needs_dark
            # Force update without full reset
            mw.app.setStyle(mw.app.style())
    except:
        # Fallback for older versions
        try:
            if hasattr(mw, 'pm') and hasattr(mw.pm, 'night_mode'):
                current_dark = mw.pm.night_mode()
                if current_dark != needs_dark:
                    mw.pm.set_night_mode(needs_dark)
        except:
            pass
    
    # Refresh reviewer if active
    if mw.state == "review":
        mw.reviewer.refresh()
    
    # Force webview refresh
    if hasattr(mw, 'web'):
        mw.web.eval(f"""
            if (typeof applyTheme === 'function') {{
                applyTheme('{theme_name}');
            }}
        """)
    
    tooltip(f"✨ Theme changed to: {theme_name.replace('-', ' ').title()}", period=2000)

# ==============================================================================
# =====================  STEP 3: DYNAMIC INJECTION HOOKS =======================
# ==============================================================================
def inject_theme_assets(html: str, card: Any, context: Any) -> str:
    """Injects CSS, JS, and meta tag into the card's HTML."""
    theme = get_theme()
    
    # Create injection payload with theme metadata
    injection_payload = f'''
<meta name="anki-theme" content="{theme}">
<style id="joplin-theme-css">
{THEME_CSS}
</style>
<script id="joplin-theme-script">
{THEME_SCRIPT}
</script>
'''
    
    # Inject before </head> if exists, otherwise at the beginning
    if "</head>" in html:
        return html.replace("</head>", f"{injection_payload}</head>", 1)
    elif "<html" in html:
        return html.replace("<html", f"{injection_payload}<html", 1)
    else:
        return injection_payload + html

# Register the hook
gui_hooks.card_will_show.append(inject_theme_assets)

# ==============================================================================
# ==================  STEP 4: WEBVIEW STYLE INJECTION ==========================
# ==============================================================================
def inject_webview_styles():
    """Inject styles into the main webview for consistent theming."""
    theme = get_theme()
    is_dark = is_dark_theme(theme)
    
    # Base styles for the main window
    webview_style = f"""
    <style id="joplin-webview-theme">
    body {{
        background: {'#1a1a1a' if is_dark else '#f5f7fa'} !important;
        color: {'#e0e0e0' if is_dark else '#333333'} !important;
    }}
    </style>
    """
    
    if hasattr(mw, 'web'):
        mw.web.eval(f"""
            (function() {{
                // Remove old style if exists
                const oldStyle = document.getElementById('joplin-webview-theme');
                if (oldStyle) {{
                    oldStyle.remove();
                }}
                // Add new style
                const styleElement = document.createElement('div');
                styleElement.innerHTML = `{webview_style}`;
                document.head.appendChild(styleElement.firstChild);
            }})();
        """)

# ==============================================================================
# =======================  STEP 5: CREATE THE MENU =============================
# ==============================================================================
def setup_theme_menu():
    """Builds and adds the 'Themes' menu to Anki's Tools menu."""
    theme_families: Dict[str, List[str]] = {
        'Light 🌕': [t for t in THEMES if t.startswith('light-')],
        'Nord ❄️': [t for t in THEMES if t.startswith('nord-')],
        'Balanced ⭐': [t for t in THEMES if t.startswith('balanced-')],
        'Twilight 🌙': [t for t in THEMES if t.startswith('twilight-')],
        'Dark 🪐': [t for t in THEMES if t.startswith('dark-')]
    }
    
    # Create main menu
    main_menu = QMenu("🎨 JoplinSync Themes", mw)
    
    # Add current theme indicator
    current_theme = get_theme()
    current_action = QAction(f"Current: {current_theme.replace('-', ' ').title()}", mw)
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
    
    # Add to Tools menu
    mw.form.menuTools.addSeparator()
    theme_action = QAction("🎨 JoplinSync Themes", mw)
    theme_action.setMenu(main_menu)
    mw.form.menuTools.addAction(theme_action)

# ==============================================================================
# ==========================  STEP 6: INITIALIZATION ===========================
# ==============================================================================
def init_addon():
    """Initialize the addon and apply saved theme."""
    # Apply the saved theme on startup
    theme = get_theme()
    is_dark = is_dark_theme(theme)
    
    try:
        from aqt.theme import theme_manager
        theme_manager.night_mode = is_dark
    except:
        try:
            if hasattr(mw, 'pm'):
                mw.pm.set_night_mode(is_dark)
        except:
            pass
    
    # Inject webview styles
    inject_webview_styles()
    
    # Setup menu
    setup_theme_menu()

# Register initialization
gui_hooks.main_window_did_init.append(init_addon)

# Also reinitialize on profile load
gui_hooks.profile_did_open.append(lambda: inject_webview_styles())

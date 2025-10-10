# __init__.py (FIXED VERSION for Anki 24.09+ / 25.09+)
# -*- coding: utf-8 -*-

# --- IMPORTS ---
from aqt import mw, gui_hooks
from aqt.qt import QAction, QMenu
from aqt.utils import tooltip
from typing import Any, List, Dict

# ==============================================================================
# ========================  STEP 1: CENTRAL CONFIGURATION ======================
# ==============================================================================
ADDON_NAME = "JoplinSyncSuite"
THEME_KEY = f"{ADDON_NAME}_Theme_v1"

THEMES = [
    'light-full-moon', 'light-waning-gibbous', 'light-last-quarter', 'light-waning-crescent', 'light-new-moon',
    'nord-bright-sun', 'nord-overcast-day', 'nord-stormy-sky', 'nord-aurora', 'nord-polar-night',
    'balanced-star', 'balanced-nebula', 'balanced-supernova', 'balanced-galaxy', 'balanced-comet',
    'twilight-crescent-moon', 'twilight-city-night', 'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk',
    'dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 'dark-black-hole', 'dark-starless-sky'
]

# --- FULL THEME CSS ---
THEME_CSS = """
/* =================================================================== */
/* =================== 🌕 FAMILY: LIGHT THEMES ======================= */
/* =================================================================== */
/* 1.1: light-full-moon (Original Light) */
body.theme-light-full-moon{background:linear-gradient(135deg,#f5f7fa 0%,#c3cfe2 100%)}
.theme-light-full-moon .card-container,.theme-light-full-moon .cloze-container,.theme-light-full-moon .mcq-container,.theme-light-full-moon .image-container{background:rgba(255,255,255,0.8);backdrop-filter:blur(12px);color:#433865;border:1px solid rgba(226,232,240,0.9)}
.theme-light-full-moon .meta-header,.theme-light-full-moon .header,.theme-light-full-moon .cloze-header,.theme-light-full-moon .mcq-header,.theme-light-full-moon .image-header{background:linear-gradient(135deg,#a855f7 0%,#d946ef 100%)}
.theme-light-full-moon .card-type,.theme-light-full-moon .cloze-title,.theme-light-full-moon .mcq-title,.theme-light-full-moon .image-title,.theme-light-full-moon .header-text{color:#F5F3FF!important;text-shadow:1px 1px 3px rgba(0,0,0,0.2)}
.theme-light-full-moon .question-text,.theme-light-full-moon .question-section{color:#581C87!important}
.theme-light-full-moon .answer-text,.theme-light-full-moon .cloze-content{color:#065F46!important}
.theme-light-full-moon .cloze{background:linear-gradient(135deg,#d946ef,#ec4899)!important;color:#F5F3FF;font-weight:700}
.theme-light-full-moon .explanation-block,.theme-light-full-moon .explanation-section,.theme-light-full-moon .explanation-info{background:#E6FFFA;border-left:5px solid #38B2AC}
.theme-light-full-moon .correlation-block,.theme-light-full-moon .correlation-section,.theme-light-full-moon .correlation-info{background:#F0E6FF;border-left:5px solid #8B5CF6}
.theme-light-full-moon .extra-info,.theme-light-full-moon .comments-block{background:#FFF5E6;border-left:5px solid #F97316}
/* (Include all other theme CSS from your original file - truncated here for space) */
"""

# --- MODIFIED THEME SCRIPT ---
THEME_SCRIPT = """
// --- Configuration ---
const THEME_FAMILIES = {
    'light': {
        modes: ['light-full-moon', 'light-waning-gibbous', 'light-last-quarter', 'light-waning-crescent', 'light-new-moon']
    },
    'nord': {
        modes: ['nord-bright-sun', 'nord-overcast-day', 'nord-stormy-sky', 'nord-aurora', 'nord-polar-night']
    },
    'balanced': {
        modes: ['balanced-star', 'balanced-nebula', 'balanced-supernova', 'balanced-galaxy', 'balanced-comet']
    },
    'twilight': {
        modes: ['twilight-crescent-moon', 'twilight-city-night', 'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk']
    },
    'dark': {
        modes: ['dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 'dark-black-hole', 'dark-starless-sky']
    }
};
const ALL_THEMES = Object.values(THEME_FAMILIES).flatMap(f => f.modes);
const THEME_KEY = 'JoplinSyncSuite_Theme_v1';

// --- Core Helper Function ---
function applyTheme(theme) {
    if (!theme || !ALL_THEMES.includes(theme)) {
        theme = 'light-full-moon'; // Fallback to default
    }
    document.body.classList.forEach(c => {
        if (c.startsWith('theme-')) {
            document.body.classList.remove(c);
        }
    });
    document.body.classList.add('theme-' + theme);
    if (!document.body.classList.contains('card')) {
        document.body.classList.add('card');
    }
}

// --- Core Storage Function ---
function loadTheme() {
    const metaTheme = document.querySelector('meta[name="anki-theme"]');
    if (metaTheme && metaTheme.content && ALL_THEMES.includes(metaTheme.content)) {
        return metaTheme.content;
    }
    try {
        const localTheme = localStorage.getItem(THEME_KEY);
        if (localTheme && ALL_THEMES.includes(localTheme)) {
            return localTheme;
        }
    } catch(e) {}

    return 'light-full-moon'; // Default theme
}

// --- Simplified Initialization ---
function initTheme() {
    const themeToApply = loadTheme();
    applyTheme(themeToApply);
}

// --- Run Logic ---
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
} else {
    initTheme();
}
window.addEventListener('ankiCardShown', initTheme);
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

def apply_global_theme(theme_name: str):
    """Saves the theme, updates Anki's UI, and refreshes the reviewer."""
    save_theme(theme_name)
    dark_families = ["dark", "twilight", "balanced"]
    current_family = theme_name.split('-')[0]
    is_dark = current_family in dark_families
    
    # Updated for Anki 25.09+ API
    try:
        from aqt.theme import theme_manager
        current_theme = theme_manager.night_mode
        if is_dark != current_theme:
            theme_manager.night_mode = is_dark
            mw.reset()
    except:
        # Fallback for older Anki versions
        try:
            if is_dark != mw.pm.night_mode():
                mw.pm.set_night_mode(is_dark)
                mw.reset()
        except:
            pass
        
    if mw.state == "review":
        mw.reviewer.refresh()
    
    tooltip(f"Theme set to {theme_name.replace('-', ' ').title()}")

# ==============================================================================
# =====================  STEP 3: DYNAMIC INJECTION HOOKS =======================
# ==============================================================================
def inject_theme_assets(html: str, card, context: Any) -> str:
    """Injects CSS, JS, and a meta tag into the card's HTML head."""
    theme = get_theme()
    meta_tag = f'<meta name="anki-theme" content="{theme}">'
    
    injection_payload = f'''
{meta_tag}
<style>{THEME_CSS}</style>
<script>{THEME_SCRIPT}</script>
'''
    
    if "</head>" in html:
        return html.replace("</head>", f"{injection_payload}</head>", 1)
    
    return injection_payload + html

gui_hooks.card_will_show.append(inject_theme_assets)

# ==============================================================================
# =======================  STEP 4: CREATE THE GLOBAL UI ========================
# ==============================================================================
def setup_theme_menu():
    """Builds and adds the 'Themes' menu to Anki's main toolbar."""
    theme_families: Dict[str, List[str]] = {
        'Light 🌕': [t for t in THEMES if t.startswith('light-')],
        'Nord ☀️': [t for t in THEMES if t.startswith('nord-')],
        'Balanced ⭐': [t for t in THEMES if t.startswith('balanced-')],
        'Twilight 🌙': [t for t in THEMES if t.startswith('twilight-')],
        'Dark 🪐': [t for t in THEMES if t.startswith('dark-')]
    }

    action_name = f"{ADDON_NAME}_theme_menu_action"

    # --- FIXED ---
    # Properly remove old menu if add-on is reloaded
    # Access the toolbar's web widget to find and remove actions
    try:
        # Get all children actions from the toolbar
        for child in mw.form.menubar.findChildren(QAction):
            if child.objectName() == action_name:
                mw.form.menubar.removeAction(child)
                break
    except Exception as e:
        # Silently continue if removal fails (first time loading)
        pass

    main_menu = QMenu("Change Theme", mw)

    for family_name, theme_list in theme_families.items():
        sub_menu = QMenu(family_name, mw)
        for theme_name in theme_list:
            display_name = theme_name.replace(theme_name.split('-')[0] + '-', '').replace('-', ' ').title()
            action = QAction(display_name, mw)
            action.triggered.connect(lambda checked, name=theme_name: apply_global_theme(name))
            sub_menu.addAction(action)
        main_menu.addMenu(sub_menu)

    main_toolbar_action = QAction("🎨 Themes", mw)
    main_toolbar_action.setObjectName(action_name)
    main_toolbar_action.setMenu(main_menu)

    # Add to the Tools menu instead of toolbar
    mw.form.menuTools.addAction(main_toolbar_action)

# ==============================================================================
# ==========================  STEP 5: INITIALIZATION ===========================
# ==============================================================================
gui_hooks.main_window_did_init.append(setup_theme_menu)

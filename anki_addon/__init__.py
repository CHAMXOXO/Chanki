# __init__.py - ACTUALLY WORKING VERSION for Anki 25.09.2
# -*- coding: utf-8 -*-
"""
This addon applies custom gradient themes to your Anki cards.
It works WITH Anki's native theming, not against it.
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction, QMenu
from aqt.utils import tooltip, showInfo
from typing import Any
import os

# ==============================================================================
# CONFIGURATION
# ==============================================================================
ADDON_NAME = "JoplinSyncSuite"
THEME_KEY = f"{ADDON_NAME}_Theme_v2"

THEMES = [
    'light-full-moon', 'light-waning-gibbous', 'light-last-quarter', 'light-waning-crescent', 'light-new-moon',
    'nord-bright-sun', 'nord-overcast-day', 'nord-stormy-sky', 'nord-aurora', 'nord-polar-night',
    'balanced-star', 'balanced-nebula', 'balanced-supernova', 'balanced-galaxy', 'balanced-comet',
    'twilight-crescent-moon', 'twilight-city-night', 'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk',
    'dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 'dark-black-hole', 'dark-starless-sky'
]

# Which themes work better with dark mode text
DARK_MODE_THEMES = {
    'nord-stormy-sky', 'nord-polar-night',
    'balanced-star', 'balanced-nebula', 'balanced-galaxy',
    'twilight-crescent-moon', 'twilight-city-night', 
    'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk',
    'dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 
    'dark-black-hole', 'dark-starless-sky'
}

# ==============================================================================
# COMPLETE THEME CSS - This will be injected into EVERY card
# ==============================================================================
THEME_CSS = """
/* === JOPLINSYNC THEME SYSTEM === */
/* Force override all existing styles */

html, body {
    margin: 0 !important;
    padding: 0 !important;
    min-height: 100vh !important;
    width: 100% !important;
}

body.card {
    margin: 0 !important;
    padding: 20px !important;
    min-height: 100vh !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
    /* Default background - will be overridden by theme classes */
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
}

/* === LIGHT FAMILY === */
body.theme-light-full-moon { 
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important; 
}
body.theme-light-waning-gibbous { 
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%) !important; 
}
body.theme-light-last-quarter { 
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%) !important; 
}
body.theme-light-waning-crescent { 
    background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%) !important; 
}
body.theme-light-new-moon { 
    background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%) !important; 
}

/* === NORD FAMILY === */
body.theme-nord-bright-sun { 
    background: linear-gradient(135deg, #ECEFF4 0%, #D8DEE9 100%) !important; 
}
body.theme-nord-overcast-day { 
    background: linear-gradient(135deg, #E5E9F0 0%, #D8DEE9 50%, #ECEFF4 100%) !important; 
}
body.theme-nord-stormy-sky { 
    background: linear-gradient(135deg, #4C566A 0%, #434C5E 50%, #3B4252 100%) !important; 
}
body.theme-nord-aurora { 
    background: linear-gradient(135deg, #BF616A 0%, #D08770 25%, #EBCB8B 50%, #A3BE8C 75%, #B48EAD 100%) !important; 
}
body.theme-nord-polar-night { 
    background: linear-gradient(135deg, #2E3440 0%, #3B4252 50%, #434C5E 100%) !important; 
}

/* === BALANCED FAMILY === */
body.theme-balanced-star { 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; 
}
body.theme-balanced-nebula { 
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important; 
}
body.theme-balanced-supernova { 
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%) !important; 
}
body.theme-balanced-galaxy { 
    background: linear-gradient(135deg, #30cfd0 0%, #330867 100%) !important; 
}
body.theme-balanced-comet { 
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%) !important; 
}

/* === TWILIGHT FAMILY === */
body.theme-twilight-crescent-moon { 
    background: linear-gradient(135deg, #2D3748 0%, #1A202C 100%) !important; 
}
body.theme-twilight-city-night { 
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important; 
}
body.theme-twilight-deep-forest { 
    background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%) !important; 
}
body.theme-twilight-moonlit-ocean { 
    background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%) !important; 
}
body.theme-twilight-dusk { 
    background: linear-gradient(135deg, #141e30 0%, #243b55 100%) !important; 
}

/* === DARK FAMILY === */
body.theme-dark-saturn { 
    background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%) !important; 
}
body.theme-dark-mars-rover { 
    background: linear-gradient(135deg, #200122 0%, #6f0000 100%) !important; 
}
body.theme-dark-neptune-deep { 
    background: linear-gradient(135deg, #051937 0%, #004d7a 50%, #008793 100%) !important; 
}
body.theme-dark-black-hole { 
    background: radial-gradient(circle at center, #0a0a0a 0%, #000000 100%) !important; 
}
body.theme-dark-starless-sky { 
    background: linear-gradient(135deg, #000000 0%, #0a0a0a 100%) !important; 
}

/* === CONTAINER STYLES === */
.card-container, .cloze-container, .mcq-container, .image-container,
div[class*="container"], .content, .card-content {
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    color: #2d3748 !important;
    border: 1px solid rgba(226, 232, 240, 0.9) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07) !important;
    margin: 10px 0 !important;
}

/* Dark theme containers - adjust for all dark themes */
body.theme-nord-stormy-sky .card-container,
body.theme-nord-stormy-sky .cloze-container,
body.theme-nord-stormy-sky .mcq-container,
body.theme-nord-stormy-sky .image-container,
body.theme-nord-stormy-sky div[class*="container"],
body.theme-nord-stormy-sky .content,
body.theme-nord-stormy-sky .card-content,
body.theme-nord-polar-night .card-container,
body.theme-nord-polar-night .cloze-container,
body.theme-nord-polar-night .mcq-container,
body.theme-nord-polar-night .image-container,
body.theme-nord-polar-night div[class*="container"],
body.theme-nord-polar-night .content,
body.theme-nord-polar-night .card-content,
body.theme-balanced-star .card-container,
body.theme-balanced-star .cloze-container,
body.theme-balanced-star .mcq-container,
body.theme-balanced-star .image-container,
body.theme-balanced-star div[class*="container"],
body.theme-balanced-star .content,
body.theme-balanced-star .card-content,
body.theme-balanced-nebula .card-container,
body.theme-balanced-nebula .cloze-container,
body.theme-balanced-nebula .mcq-container,
body.theme-balanced-nebula .image-container,
body.theme-balanced-nebula div[class*="container"],
body.theme-balanced-nebula .content,
body.theme-balanced-nebula .card-content,
body.theme-balanced-galaxy .card-container,
body.theme-balanced-galaxy .cloze-container,
body.theme-balanced-galaxy .mcq-container,
body.theme-balanced-galaxy .image-container,
body.theme-balanced-galaxy div[class*="container"],
body.theme-balanced-galaxy .content,
body.theme-balanced-galaxy .card-content,
body.theme-twilight-crescent-moon .card-container,
body.theme-twilight-crescent-moon .cloze-container,
body.theme-twilight-crescent-moon .mcq-container,
body.theme-twilight-crescent-moon .image-container,
body.theme-twilight-crescent-moon div[class*="container"],
body.theme-twilight-crescent-moon .content,
body.theme-twilight-crescent-moon .card-content,
body.theme-twilight-city-night .card-container,
body.theme-twilight-city-night .cloze-container,
body.theme-twilight-city-night .mcq-container,
body.theme-twilight-city-night .image-container,
body.theme-twilight-city-night div[class*="container"],
body.theme-twilight-city-night .content,
body.theme-twilight-city-night .card-content,
body.theme-twilight-deep-forest .card-container,
body.theme-twilight-deep-forest .cloze-container,
body.theme-twilight-deep-forest .mcq-container,
body.theme-twilight-deep-forest .image-container,
body.theme-twilight-deep-forest div[class*="container"],
body.theme-twilight-deep-forest .content,
body.theme-twilight-deep-forest .card-content,
body.theme-twilight-moonlit-ocean .card-container,
body.theme-twilight-moonlit-ocean .cloze-container,
body.theme-twilight-moonlit-ocean .mcq-container,
body.theme-twilight-moonlit-ocean .image-container,
body.theme-twilight-moonlit-ocean div[class*="container"],
body.theme-twilight-moonlit-ocean .content,
body.theme-twilight-moonlit-ocean .card-content,
body.theme-twilight-dusk .card-container,
body.theme-twilight-dusk .cloze-container,
body.theme-twilight-dusk .mcq-container,
body.theme-twilight-dusk .image-container,
body.theme-twilight-dusk div[class*="container"],
body.theme-twilight-dusk .content,
body.theme-twilight-dusk .card-content,
body.theme-dark-saturn .card-container,
body.theme-dark-saturn .cloze-container,
body.theme-dark-saturn .mcq-container,
body.theme-dark-saturn .image-container,
body.theme-dark-saturn div[class*="container"],
body.theme-dark-saturn .content,
body.theme-dark-saturn .card-content,
body.theme-dark-mars-rover .card-container,
body.theme-dark-mars-rover .cloze-container,
body.theme-dark-mars-rover .mcq-container,
body.theme-dark-mars-rover .image-container,
body.theme-dark-mars-rover div[class*="container"],
body.theme-dark-mars-rover .content,
body.theme-dark-mars-rover .card-content,
body.theme-dark-neptune-deep .card-container,
body.theme-dark-neptune-deep .cloze-container,
body.theme-dark-neptune-deep .mcq-container,
body.theme-dark-neptune-deep .image-container,
body.theme-dark-neptune-deep div[class*="container"],
body.theme-dark-neptune-deep .content,
body.theme-dark-neptune-deep .card-content,
body.theme-dark-black-hole .card-container,
body.theme-dark-black-hole .cloze-container,
body.theme-dark-black-hole .mcq-container,
body.theme-dark-black-hole .image-container,
body.theme-dark-black-hole div[class*="container"],
body.theme-dark-black-hole .content,
body.theme-dark-black-hole .card-content,
body.theme-dark-starless-sky .card-container,
body.theme-dark-starless-sky .cloze-container,
body.theme-dark-starless-sky .mcq-container,
body.theme-dark-starless-sky .image-container,
body.theme-dark-starless-sky div[class*="container"],
body.theme-dark-starless-sky .content,
body.theme-dark-starless-sky .card-content {
    background: rgba(30, 30, 40, 0.95) !important;
    color: #e0e0e0 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* Make sure text is readable */
body.card, body.card * {
    line-height: 1.6 !important;
}

/* Headers */
h1, h2, h3, h4, h5, h6 {
    margin-top: 1em !important;
    margin-bottom: 0.5em !important;
}

/* Code blocks */
pre, code {
    background: rgba(0, 0, 0, 0.05) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
}

/* Images */
img {
    max-width: 100% !important;
    height: auto !important;
    border-radius: 8px !important;
    margin: 10px 0 !important;
}
"""

# ==============================================================================
# AGGRESSIVE THEME JAVASCRIPT - Runs multiple times to ensure it sticks
# ==============================================================================
THEME_SCRIPT = """
(function() {
    'use strict';
    
    // Configuration
    const THEME_KEY = 'JoplinSyncSuite_Theme_v2';
    const ALL_THEMES = %s;
    
    // Get theme from multiple sources
    function getTheme() {
        // 1. Check meta tag (set by Python on card load)
        const metaTag = document.querySelector('meta[name="joplin-theme"]');
        if (metaTag && metaTag.content && ALL_THEMES.includes(metaTag.content)) {
            return metaTag.content;
        }
        
        // 2. Check localStorage
        try {
            const saved = localStorage.getItem(THEME_KEY);
            if (saved && ALL_THEMES.includes(saved)) {
                return saved;
            }
        } catch(e) {
            console.warn('localStorage unavailable:', e);
        }
        
        // 3. Default fallback
        return 'light-full-moon';
    }
    
    // Apply theme - AGGRESSIVE version
    function applyTheme(themeName) {
        if (!themeName || !ALL_THEMES.includes(themeName)) {
            themeName = 'light-full-moon';
        }
        
        console.log('[JoplinSync] Applying theme:', themeName);
        
        // Remove ALL theme classes
        const body = document.body;
        const classes = Array.from(body.classList);
        classes.forEach(cls => {
            if (cls.startsWith('theme-')) {
                body.classList.remove(cls);
            }
        });
        
        // Add the card class if missing
        if (!body.classList.contains('card')) {
            body.classList.add('card');
        }
        
        // Add new theme class
        body.classList.add('theme-' + themeName);
        
        // Save to localStorage
        try {
            localStorage.setItem(THEME_KEY, themeName);
            console.log('[JoplinSync] Theme saved to localStorage');
        } catch(e) {
            console.warn('[JoplinSync] Could not save to localStorage:', e);
        }
        
        // Force a reflow to ensure styles apply
        void body.offsetHeight;
        
        console.log('[JoplinSync] Theme applied. Body classes:', body.className);
    }
    
    // Initialize
    function init() {
        const theme = getTheme();
        console.log('[JoplinSync] Initializing with theme:', theme);
        applyTheme(theme);
    }
    
    // Make globally available
    window.applyJoplinTheme = applyTheme;
    window.getJoplinTheme = getTheme;
    
    // Run immediately
    init();
    
    // Run on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    }
    
    // Run on window load
    window.addEventListener('load', init);
    
    // Run on Anki-specific events
    if (typeof pycmd !== 'undefined') {
        // We're in Anki's webview
        setTimeout(init, 50);
        setTimeout(init, 100);
        setTimeout(init, 200);
    }
    
    console.log('[JoplinSync] Theme script loaded');
})();
""" % str(THEMES).replace("'", '"')

# ==============================================================================
# THEME MANAGEMENT
# ==============================================================================
def get_theme() -> str:
    """Get the currently selected theme"""
    try:
        if mw.col:
            theme = mw.col.conf.get(THEME_KEY, 'light-full-moon')
            if theme in THEMES:
                return theme
    except:
        pass
    return 'light-full-moon'

def save_theme(theme: str) -> bool:
    """Save theme to Anki's collection config"""
    if theme not in THEMES:
        return False
    
    try:
        if mw.col:
            mw.col.conf[THEME_KEY] = theme
            mw.col.setMod()
            return True
    except Exception as e:
        print(f"[JoplinSync] Error saving theme: {e}")
    
    return False

def is_dark_theme(theme: str) -> bool:
    """Check if theme needs dark mode"""
    return theme in DARK_MODE_THEMES

# ==============================================================================
# CARD INJECTION - This is where the magic happens
# ==============================================================================
def inject_theme_into_card(html: str, card: Any, context: Any) -> str:
    """
    Inject theme CSS and JS into every card.
    This runs on EVERY card shown, ensuring themes always apply.
    """
    theme = get_theme()
    
    # Create injection bundle
    injection = f'''
<!-- JoplinSync Theme System -->
<meta name="joplin-theme" content="{theme}">
<style id="joplin-theme-css">
{THEME_CSS}
</style>
<script id="joplin-theme-js">
{THEME_SCRIPT}
</script>
<!-- End JoplinSync Theme System -->
'''
    
    # Try to inject before </head>
    if "</head>" in html:
        html = html.replace("</head>", injection + "</head>", 1)
    # If no </head>, inject at the very start
    else:
        html = injection + html
    
    return html

# ==============================================================================
# THEME SWITCHING
# ==============================================================================
def switch_to_theme(theme_name: str):
    """Switch to a new theme and refresh the UI"""
    if theme_name not in THEMES:
        tooltip(f"⚠️ Invalid theme: {theme_name}")
        return
    
    # Save the theme
    if not save_theme(theme_name):
        tooltip("⚠️ Could not save theme")
        return
    
    # Update Anki's night mode to match
    needs_dark = is_dark_theme(theme_name)
    try:
        from aqt.theme import theme_manager
        if theme_manager.night_mode != needs_dark:
            theme_manager.night_mode = needs_dark
    except:
        pass
    
    # Refresh the reviewer if in review mode
    if mw.state == "review":
        try:
            # Force JavaScript to reapply theme
            if hasattr(mw.reviewer, 'web'):
                mw.reviewer.web.eval(f"""
                    if (typeof applyJoplinTheme === 'function') {{
                        applyJoplinTheme('{theme_name}');
                    }}
                """)
            # Then refresh the card
            mw.reviewer.refresh()
        except Exception as e:
            print(f"[JoplinSync] Error refreshing reviewer: {e}")
    
    # Show confirmation
    display_name = theme_name.replace('-', ' ').title()
    tooltip(f"✨ Theme: {display_name}", period=2000)

# ==============================================================================
# MENU CREATION
# ==============================================================================
def create_theme_menu():
    """Create the theme selection menu"""
    
    # Theme families
    families = {
        '🌕 Light': [t for t in THEMES if t.startswith('light-')],
        '❄️ Nord': [t for t in THEMES if t.startswith('nord-')],
        '⭐ Balanced': [t for t in THEMES if t.startswith('balanced-')],
        '🌙 Twilight': [t for t in THEMES if t.startswith('twilight-')],
        '🪐 Dark': [t for t in THEMES if t.startswith('dark-')]
    }
    
    # Create main menu
    main_menu = QMenu("🎨 JoplinSync Themes", mw)
    
    # Show current theme
    current = get_theme()
    current_display = current.replace('-', ' ').title()
    current_action = QAction(f"Current: {current_display}", mw)
    current_action.setEnabled(False)
    main_menu.addAction(current_action)
    main_menu.addSeparator()
    
    # Add theme families
    for family_name, theme_list in families.items():
        family_menu = QMenu(family_name, mw)
        
        for theme in theme_list:
            # Create display name (remove prefix)
            prefix = theme.split('-')[0] + '-'
            display = theme.replace(prefix, '', 1).replace('-', ' ').title()
            
            action = QAction(display, mw)
            
            # Mark current theme
            if theme == current:
                action.setCheckable(True)
                action.setChecked(True)
            
            # Connect to theme switcher
            action.triggered.connect(
                lambda checked, t=theme: switch_to_theme(t)
            )
            
            family_menu.addAction(action)
        
        main_menu.addMenu(family_menu)
    
    # Add info action
    main_menu.addSeparator()
    info_action = QAction("ℹ️ About Themes", mw)
    info_action.triggered.connect(show_theme_info)
    main_menu.addAction(info_action)
    
    # Add to Tools menu
    tools_menu = mw.form.menuTools
    tools_menu.addSeparator()
    tools_menu.addMenu(main_menu)

def show_theme_info():
    """Show information about the theme system"""
    current = get_theme()
    info = f"""
<h2>JoplinSync Theme System</h2>
<p><b>Current Theme:</b> {current.replace('-', ' ').title()}</p>
<p><b>Total Themes:</b> {len(THEMES)} themes across 5 families</p>
<hr>
<p><b>How it works:</b></p>
<ul>
<li>Themes are applied to all your flashcards</li>
<li>Each theme persists across sessions</li>
<li>Themes sync with Anki's light/dark mode</li>
<li>Works on desktop (mobile requires card templates)</li>
</ul>
<p><b>Families:</b> Light 🌕, Nord ❄️, Balanced ⭐, Twilight 🌙, Dark 🪐</p>
"""
    showInfo(info, title="JoplinSync Themes", textFormat="rich")

# ==============================================================================
# INITIALIZATION
# ==============================================================================
def initialize_addon():
    """Initialize the addon when Anki starts"""
    try:
        # Set up Anki's night mode based on current theme
        theme = get_theme()
        needs_dark = is_dark_theme(theme)
        
        try:
            from aqt.theme import theme_manager
            theme_manager.night_mode = needs_dark
        except:
            pass
        
        # Create the menu
        create_theme_menu()
        
        print(f"[JoplinSync] Theme system initialized. Current theme: {theme}")
        
    except Exception as e:
        print(f"[JoplinSync] Initialization error: {e}")

# ==============================================================================
# REGISTER HOOKS
# ==============================================================================
# The most important hook - this makes themes actually work
gui_hooks.card_will_show.append(inject_theme_into_card)

# Initialize on startup
gui_hooks.main_window_did_init.append(initialize_addon)

# Reinitialize when profile opens
gui_hooks.profile_did_open.append(initialize_addon)

print("[JoplinSync] Theme addon loaded")

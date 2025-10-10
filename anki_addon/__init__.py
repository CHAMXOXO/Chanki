# __init__.py - Fixed Version for Anki 25.09.2
# -*- coding: utf-8 -*-

from aqt import mw, gui_hooks
from aqt.qt import QAction, QMenu
from aqt.utils import tooltip
from typing import Any, List, Dict
import json

# ==============================================================================
# CONFIGURATION
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

# Define which themes need dark mode for optimal text contrast
DARK_MODE_THEMES = {
    'nord-stormy-sky', 'nord-polar-night',
    'balanced-star', 'balanced-nebula', 'balanced-galaxy',
    'twilight-crescent-moon', 'twilight-city-night', 
    'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk',
    'dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 
    'dark-black-hole', 'dark-starless-sky'
}

# ==============================================================================
# THEME CSS - Complete with all gradients
# ==============================================================================
THEME_CSS = """
/* Base Reset */
body.card {
    margin: 0 !important;
    padding: 20px !important;
    min-height: 100vh !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

/* Light Family */
body.theme-light-full-moon { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important; }
body.theme-light-waning-gibbous { background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%) !important; }
body.theme-light-last-quarter { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%) !important; }
body.theme-light-waning-crescent { background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%) !important; }
body.theme-light-new-moon { background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%) !important; }

/* Nord Family */
body.theme-nord-bright-sun { background: linear-gradient(135deg, #ECEFF4 0%, #D8DEE9 100%) !important; }
body.theme-nord-overcast-day { background: linear-gradient(135deg, #E5E9F0 0%, #D8DEE9 50%, #ECEFF4 100%) !important; }
body.theme-nord-stormy-sky { background: linear-gradient(135deg, #4C566A 0%, #434C5E 50%, #3B4252 100%) !important; }
body.theme-nord-aurora { background: linear-gradient(135deg, #BF616A 0%, #D08770 25%, #EBCB8B 50%, #A3BE8C 75%, #B48EAD 100%) !important; }
body.theme-nord-polar-night { background: linear-gradient(135deg, #2E3440 0%, #3B4252 50%, #434C5E 100%) !important; }

/* Balanced Family */
body.theme-balanced-star { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; }
body.theme-balanced-nebula { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important; }
body.theme-balanced-supernova { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%) !important; }
body.theme-balanced-galaxy { background: linear-gradient(135deg, #30cfd0 0%, #330867 100%) !important; }
body.theme-balanced-comet { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%) !important; }

/* Twilight Family */
body.theme-twilight-crescent-moon { background: linear-gradient(135deg, #2D3748 0%, #1A202C 100%) !important; }
body.theme-twilight-city-night { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important; }
body.theme-twilight-deep-forest { background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%) !important; }
body.theme-twilight-moonlit-ocean { background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%) !important; }
body.theme-twilight-dusk { background: linear-gradient(135deg, #141e30 0%, #243b55 100%) !important; }

/* Dark Family */
body.theme-dark-saturn { background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%) !important; }
body.theme-dark-mars-rover { background: linear-gradient(135deg, #200122 0%, #6f0000 100%) !important; }
body.theme-dark-neptune-deep { background: linear-gradient(135deg, #051937 0%, #004d7a 50%, #008793 100%) !important; }
body.theme-dark-black-hole { background: radial-gradient(circle at center, #0a0a0a 0%, #000000 100%) !important; }
body.theme-dark-starless-sky { background: linear-gradient(135deg, #000000 0%, #0a0a0a 100%) !important; }

/* Container Styles */
.card-container, .cloze-container, .mcq-container, .image-container {
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(12px) !important;
    color: #433865 !important;
    border: 1px solid rgba(226, 232, 240, 0.9) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07) !important;
}

/* Dark theme containers */
body.theme-nord-stormy-sky .card-container,
body.theme-nord-polar-night .card-container,
body.theme-balanced-star .card-container,
body.theme-balanced-nebula .card-container,
body.theme-balanced-galaxy .card-container,
body.theme-twilight-crescent-moon .card-container,
body.theme-twilight-city-night .card-container,
body.theme-twilight-deep-forest .card-container,
body.theme-twilight-moonlit-ocean .card-container,
body.theme-twilight-dusk .card-container,
body.theme-dark-saturn .card-container,
body.theme-dark-mars-rover .card-container,
body.theme-dark-neptune-deep .card-container,
body.theme-dark-black-hole .card-container,
body.theme-dark-starless-sky .card-container,
body.theme-nord-stormy-sky .cloze-container,
body.theme-nord-polar-night .cloze-container,
body.theme-balanced-star .cloze-container,
body.theme-balanced-nebula .cloze-container,
body.theme-balanced-galaxy .cloze-container,
body.theme-twilight-crescent-moon .cloze-container,
body.theme-twilight-city-night .cloze-container,
body.theme-twilight-deep-forest .cloze-container,
body.theme-twilight-moonlit-ocean .cloze-container,
body.theme-twilight-dusk .cloze-container,
body.theme-dark-saturn .cloze-container,
body.theme-dark-mars-rover .cloze-container,
body.theme-dark-neptune-deep .cloze-container,
body.theme-dark-black-hole .cloze-container,
body.theme-dark-starless-sky .cloze-container {
    background: rgba(30, 30, 40, 0.95) !important;
    color: #e0e0e0 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
"""

# ==============================================================================
# THEME JAVASCRIPT
# ==============================================================================
THEME_SCRIPT = """
(function() {
    'use strict';
    
    const THEME_KEY = 'JoplinSyncSuite_Theme_v1';
    const ALL_THEMES = [
        'light-full-moon', 'light-waning-gibbous', 'light-last-quarter', 'light-waning-crescent', 'light-new-moon',
        'nord-bright-sun', 'nord-overcast-day', 'nord-stormy-sky', 'nord-aurora', 'nord-polar-night',
        'balanced-star', 'balanced-nebula', 'balanced-supernova', 'balanced-galaxy', 'balanced-comet',
        'twilight-crescent-moon', 'twilight-city-night', 'twilight-deep-forest', 'twilight-moonlit-ocean', 'twilight-dusk',
        'dark-saturn', 'dark-mars-rover', 'dark-neptune-deep', 'dark-black-hole', 'dark-starless-sky'
    ];
    
    function applyTheme(theme) {
        if (!theme || !ALL_THEMES.includes(theme)) {
            theme = 'light-full-moon';
        }
        
        // Remove all theme classes
        document.body.className = document.body.className
            .split(' ')
            .filter(c => !c.startsWith('theme-'))
            .join(' ');
        
        // Add new theme
        document.body.classList.add('card', 'theme-' + theme);
        
        // Save to localStorage for persistence
        try {
            localStorage.setItem(THEME_KEY, theme);
        } catch(e) {}
    }
    
    function loadTheme() {
        // Check meta tag first (from Python)
        const metaTheme = document.querySelector('meta[name="anki-theme"]');
        if (metaTheme && metaTheme.content) {
            return metaTheme.content;
        }
        
        // Fallback to localStorage
        try {
            return localStorage.getItem(THEME_KEY) || 'light-full-moon';
        } catch(e) {
            return 'light-full-moon';
        }
    }
    
    // Make applyTheme global for Python to call
    window.applyTheme = applyTheme;
    
    // Initialize immediately
    const theme = loadTheme();
    applyTheme(theme);
    
    // Also on various events
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => applyTheme(theme));
    }
    window.addEventListener('load', () => applyTheme(theme));
    
    // Anki-specific
    if (window.ankiCardShown) {
        window.addEventListener('ankiCardShown', () => applyTheme(loadTheme()));
    }
})();
"""

# ==============================================================================
# MAIN WINDOW CSS - This is the KEY to system-wide theming
# ==============================================================================
def get_main_window_css(theme: str) -> str:
    """Generate CSS to override Anki's main window theme"""
    
    # Map themes to background colors
    theme_backgrounds = {
        'light-full-moon': 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        'light-waning-gibbous': 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
        'light-last-quarter': 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
        'light-waning-crescent': 'linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)',
        'light-new-moon': 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)',
        'nord-bright-sun': 'linear-gradient(135deg, #ECEFF4 0%, #D8DEE9 100%)',
        'nord-overcast-day': 'linear-gradient(135deg, #E5E9F0 0%, #D8DEE9 50%, #ECEFF4 100%)',
        'nord-stormy-sky': 'linear-gradient(135deg, #4C566A 0%, #434C5E 50%, #3B4252 100%)',
        'nord-aurora': 'linear-gradient(135deg, #BF616A 0%, #D08770 25%, #EBCB8B 50%, #A3BE8C 75%, #B48EAD 100%)',
        'nord-polar-night': 'linear-gradient(135deg, #2E3440 0%, #3B4252 50%, #434C5E 100%)',
        'balanced-star': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'balanced-nebula': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'balanced-supernova': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        'balanced-galaxy': 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
        'balanced-comet': 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
        'twilight-crescent-moon': 'linear-gradient(135deg, #2D3748 0%, #1A202C 100%)',
        'twilight-city-night': 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
        'twilight-deep-forest': 'linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%)',
        'twilight-moonlit-ocean': 'linear-gradient(135deg, #2b5876 0%, #4e4376 100%)',
        'twilight-dusk': 'linear-gradient(135deg, #141e30 0%, #243b55 100%)',
        'dark-saturn': 'linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%)',
        'dark-mars-rover': 'linear-gradient(135deg, #200122 0%, #6f0000 100%)',
        'dark-neptune-deep': 'linear-gradient(135deg, #051937 0%, #004d7a 50%, #008793 100%)',
        'dark-black-hole': 'radial-gradient(circle at center, #0a0a0a 0%, #000000 100%)',
        'dark-starless-sky': 'linear-gradient(135deg, #000000 0%, #0a0a0a 100%)',
    }
    
    bg = theme_backgrounds.get(theme, theme_backgrounds['light-full-moon'])
    is_dark = theme in DARK_MODE_THEMES
    text_color = '#e0e0e0' if is_dark else '#2d3748'
    
    return f"""
    <style id="joplin-main-theme">
    /* Override Anki's main window background */
    QMainWindow, QWidget {{
        background: {bg.replace('linear-gradient', 'qlineargradient').replace('135deg,', 'x1:0, y1:0, x2:1, y2:1,')
                      .replace('0%', 'stop:0').replace('50%', 'stop:0.5').replace('100%', 'stop:1')
                      .replace('25%', 'stop:0.25').replace('75%', 'stop:0.75')} !important;
        color: {text_color} !important;
    }}
    
    /* Center area - where cards are shown */
    #mainText, .review {{
        background: transparent !important;
    }}
    </style>
    """

# ==============================================================================
# CORE FUNCTIONS
# ==============================================================================
def get_theme() -> str:
    """Get saved theme from multiple sources"""
    # Try profile config first
    if hasattr(mw, 'pm') and hasattr(mw.pm, 'profile'):
        try:
            theme = mw.pm.profile.get('joplin_theme', None)
            if theme and theme in THEMES:
                return theme
        except (AttributeError, TypeError):
            pass
    
    # Try collection config
    if mw.col:
        try:
            theme = mw.col.conf.get(THEME_KEY, 'light-full-moon')
            if theme in THEMES:
                return theme
        except (AttributeError, TypeError):
            pass
    
    return 'light-full-moon'

def save_theme(theme: str):
    """Save theme to multiple locations for redundancy"""
    if theme not in THEMES:
        return
    
    # Save to profile (persists across collection changes)
    if hasattr(mw, 'pm') and hasattr(mw.pm, 'profile'):
        try:
            mw.pm.profile['joplin_theme'] = theme
            mw.pm.save()
        except (AttributeError, TypeError):
            pass
    
    # Save to collection
    if mw.col:
        try:
            mw.col.conf[THEME_KEY] = theme
            mw.col.setMod()
        except (AttributeError, TypeError):
            pass

def is_dark_theme(theme: str) -> bool:
    """Check if theme needs dark mode"""
    return theme in DARK_MODE_THEMES

def apply_theme_to_main_window(theme: str):
    """Apply theme styling to the main Anki window"""
    if not hasattr(mw, 'web'):
        return
    
    # Inject CSS into main window
    css = get_main_window_css(theme)
    mw.web.eval(f"""
        (function() {{
            const oldStyle = document.getElementById('joplin-main-theme');
            if (oldStyle) oldStyle.remove();
            
            const div = document.createElement('div');
            div.innerHTML = `{css.replace('`', '\\`')}`;
            document.head.appendChild(div.firstChild);
        }})();
    """)

def apply_global_theme(theme_name: str):
    """Apply theme globally across Anki"""
    if theme_name not in THEMES:
        return
    
    save_theme(theme_name)
    
    # Set Anki's native dark/light mode for UI consistency
    needs_dark = is_dark_theme(theme_name)
    try:
        from aqt.theme import theme_manager
        if theme_manager.night_mode != needs_dark:
            theme_manager.night_mode = needs_dark
    except:
        if hasattr(mw, 'pm'):
            mw.pm.set_night_mode(needs_dark)
    
    # Apply to main window
    apply_theme_to_main_window(theme_name)
    
    # Refresh reviewer if active
    if mw.state == "review" and hasattr(mw, 'reviewer'):
        mw.reviewer.refresh()
    
    # Force card webview update
    if hasattr(mw, 'reviewer') and hasattr(mw.reviewer, 'web'):
        mw.reviewer.web.eval(f"""
            if (typeof applyTheme === 'function') {{
                applyTheme('{theme_name}');
            }}
        """)
    
    tooltip(f"✨ Theme: {theme_name.replace('-', ' ').title()}", period=2000)

# ==============================================================================
# HOOKS
# ==============================================================================
def inject_card_theme(html: str, card: Any, context: Any) -> str:
    """Inject theme assets into each card"""
    theme = get_theme()
    
    injection = f'''
<meta name="anki-theme" content="{theme}">
<style>{THEME_CSS}</style>
<script>{THEME_SCRIPT}</script>
'''
    
    if "</head>" in html:
        return html.replace("</head>", f"{injection}</head>", 1)
    else:
        return injection + html

def on_webview_will_set_content(web_content, context):
    """Inject theme into all webviews"""
    try:
        theme = get_theme()
        css_injection = f"<style>{THEME_CSS}</style>"
        
        if hasattr(web_content, 'head'):
            web_content.head += css_injection
        elif hasattr(web_content, 'body'):
            web_content.body = css_injection + web_content.body
    except Exception:
        pass  # Silently fail to prevent startup crashes

# ==============================================================================
# MENU
# ==============================================================================
def setup_theme_menu():
    """Create theme selection menu"""
    theme_families = {
        'Light 🌕': [t for t in THEMES if t.startswith('light-')],
        'Nord ❄️': [t for t in THEMES if t.startswith('nord-')],
        'Balanced ⭐': [t for t in THEMES if t.startswith('balanced-')],
        'Twilight 🌙': [t for t in THEMES if t.startswith('twilight-')],
        'Dark 🪐': [t for t in THEMES if t.startswith('dark-')]
    }
    
    main_menu = QMenu("🎨 Themes", mw)
    current = get_theme()
    
    # Current theme indicator
    current_action = QAction(f"→ {current.replace('-', ' ').title()}", mw)
    current_action.setEnabled(False)
    main_menu.addAction(current_action)
    main_menu.addSeparator()
    
    # Add theme families
    for family, themes in theme_families.items():
        sub_menu = QMenu(family, mw)
        for theme in themes:
            display = theme.split('-', 1)[1].replace('-', ' ').title()
            action = QAction(display, mw)
            if theme == current:
                action.setCheckable(True)
                action.setChecked(True)
            action.triggered.connect(lambda _, t=theme: apply_global_theme(t))
            sub_menu.addAction(action)
        main_menu.addMenu(sub_menu)
    
    # Add to Tools menu
    mw.form.menuTools.addSeparator()
    mw.form.menuTools.addMenu(main_menu)

# ==============================================================================
# INITIALIZATION
# ==============================================================================
def init_addon():
    """Initialize addon on startup"""
    try:
        theme = get_theme()
        
        # Set Anki's base mode
        needs_dark = is_dark_theme(theme)
        try:
            from aqt.theme import theme_manager
            theme_manager.night_mode = needs_dark
        except:
            if hasattr(mw, 'pm'):
                try:
                    mw.pm.set_night_mode(needs_dark)
                except:
                    pass
        
        # Apply to main window
        apply_theme_to_main_window(theme)
        
        # Setup menu
        setup_theme_menu()
    except Exception as e:
        print(f"JoplinSync Theme initialization error: {e}")
        # Continue anyway to prevent Anki crash

# Register hooks with error protection
try:
    gui_hooks.card_will_show.append(inject_card_theme)
except Exception as e:
    print(f"Failed to register card_will_show hook: {e}")

try:
    gui_hooks.main_window_did_init.append(init_addon)
except Exception as e:
    print(f"Failed to register main_window_did_init hook: {e}")

try:
    gui_hooks.profile_did_open.append(lambda: apply_theme_to_main_window(get_theme()))
except Exception as e:
    print(f"Failed to register profile_did_open hook: {e}")

try:
    gui_hooks.webview_will_set_content.append(on_webview_will_set_content)
except Exception as e:
    print(f"Failed to register webview_will_set_content hook: {e}")

try:
    gui_hooks.state_did_change.append(lambda new_state, old_state: apply_theme_to_main_window(get_theme()))
except Exception as e:
    print(f"Failed to register state_did_change hook: {e}")

# __init__.py (FINAL VERSION - Fixes Persistence Issues)
# -*- coding: utf-8 -*-

# --- IMPORTS ---
import os
from aqt import mw, gui_hooks
from aqt.qt import QAction, QMenu
from aqt.theme import UserTheme, theme_manager
from aqt.utils import tooltip, showInfo
from typing import Optional

# ==============================================================================
# ========================  STEP 1: CENTRAL CONFIGURATION ======================
# ==============================================================================
ADDON_NAME = "JoplinSyncSuite"
CONFIG_KEY = f"{ADDON_NAME}_selected_theme"
ADDON_PATH = os.path.dirname(__file__)
THEMES_PATH = os.path.join(ADDON_PATH, "themes")

# Dynamically find all available themes by scanning the themes folder
try:
    THEMES = sorted([d for d in os.listdir(THEMES_PATH) if os.path.isdir(os.path.join(THEMES_PATH, d))])
except FileNotFoundError:
    showInfo(f"The 'themes' folder for {ADDON_NAME} is missing. Please create it at: {THEMES_PATH}")
    THEMES = []

# ==============================================================================
# =======================  STEP 2: CORE THEME LOGIC ============================
# ==============================================================================

def get_current_theme_name() -> str:
    """Gets the saved theme name from Anki's configuration."""
    default_theme = 'light-full-moon' if 'light-full-moon' in THEMES else (THEMES[0] if THEMES else None)
    return mw.col.conf.get(CONFIG_KEY, default_theme)

def build_theme_from_name(theme_name: str) -> Optional[UserTheme]:
    """Builds a UserTheme object from a theme folder."""
    if theme_name not in THEMES:
        return None

    theme_path = os.path.join(THEMES_PATH, theme_name)
    
    # Determine if the theme is dark or light
    dark_indicators = ["dark", "twilight", "polar", "abyss"]
    is_dark = any(indicator in theme_name for indicator in dark_indicators)

    return UserTheme(
        name=theme_name,
        long_name=theme_name.replace('-', ' ').title(),
        folder=theme_path,
        is_dark=is_dark,
    )

def apply_and_save_theme(theme_name: str):
    """
    Builds, registers, and applies a theme across the entire Anki UI,
    ensuring it persists through all operations.
    """
    theme = build_theme_from_name(theme_name)
    if not theme:
        tooltip(f"Theme '{theme_name}' could not be loaded.")
        return

    # 1. Save the selected theme to the config
    mw.col.conf[CONFIG_KEY] = theme_name
    mw.col.setMod()

    # 2. Register the theme with Anki's theme manager. This is the crucial step
    #    that makes the theme "official" and persistent.
    theme_manager.register_user_theme(theme)

    # 3. Set our theme as the active user theme.
    theme_manager.set_user_theme(theme.name)

    # 4. Apply the theme and reload the UI.
    #    set_user_theme already handles the necessary updates,
    #    but mw.reset() ensures all components redraw correctly.
    mw.reset()

    tooltip(f"Theme changed to: {theme.long_name}")

# ==============================================================================
# =======================  STEP 3: CREATE THE GLOBAL UI ========================
# ==============================================================================

def setup_theme_menu():
    """Builds and adds the 'Themes' menu to Anki's Tools menu."""
    if not THEMES:
        return # Don't create a menu if no themes were found

    main_menu = QMenu("Change Theme", mw)

    theme_families = {
        'Light 🌕': [t for t in THEMES if t.startswith('light-')],
        'Nord ☀️': [t for t in THEMES if t.startswith('nord-')],
        'Balanced ⭐': [t for t in THEMES if t.startswith('balanced-')],
        'Twilight 🌙': [t for t in THEMES if t.startswith('twilight-')],
        'Dark 🪐': [t for t in THEMES if t.startswith('dark-')]
    }

    for family_name, theme_list in theme_families.items():
        if not theme_list: continue
        sub_menu = QMenu(family_name, mw)
        for theme_name in theme_list:
            display_name = theme_name.split('-', 1)[1].replace('-', ' ').title()
            action = QAction(display_name, mw)
            # Use the new persistent apply function
            action.triggered.connect(lambda checked, name=theme_name: apply_and_save_theme(name))
            sub_menu.addAction(action)
        main_menu.addMenu(sub_menu)

    mw.form.menuTools.addMenu(main_menu)

# ==============================================================================
# ==========================  STEP 4: INITIALIZATION ===========================
# ==============================================================================

def on_profile_open():
    """
    Called when a user profile is loaded. This is the correct time to
    apply the theme on startup.
    """
    theme_name = get_current_theme_name()
    if not theme_name:
        return

    theme = build_theme_from_name(theme_name)
    if theme:
        # On startup, we just need to register and set the theme.
        # Anki will handle the application itself.
        theme_manager.register_user_theme(theme)
        theme_manager.set_user_theme(theme.name)
        # A full mw.reset() on startup can be disruptive, so we let
        # Anki's own startup sequence handle the styling.
        # If styles don't apply correctly on first load, uncommenting the line below
        # might be necessary, but it's best to avoid if possible.
        # mw.reset()

# This hook ensures the theme menu is added once the main window UI is ready.
gui_hooks.main_window_did_init.append(setup_theme_menu)
# This hook ensures the saved theme is applied as soon as the user profile is loaded.
gui_hooks.profile_did_open.append(on_profile_open)

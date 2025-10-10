# -*- coding: utf-8 -*-
from aqt import mw, gui_hooks
from aqt.reviewer import Reviewer
from typing import Any

# --- CONFIGURATION ---
THEME_KEY = 'joplinAnkiTheme_v3'

# IMPORTANT: This list must now include all 20 theme names for validation.
THEMES = [
    # Light Family
    'light-full-moon', 'light-waning-gibbous', 'light-last-quarter', 'light-waning-crescent', 'light-new-moon',
    # Nord Family
    'nord-bright-sun', 'nord-sun-behind-cloud', 'nord-sun-behind-large-cloud', 'nord-sun-behind-rain-cloud', 'nord-sun-behind-storm',
    # Balanced Family
    'balanced-star', 'balanced-glowing-star', 'balanced-sparkles', 'balanced-dizzy-star', 'balanced-shooting-star',
    # Twilight Family
    'twilight-crescent-moon', 'twilight-first-quarter-face', 'twilight-last-quarter-face', 'twilight-new-moon-face', 'twilight-full-moon-face',
    # Dark Family
    'dark-saturn', 'dark-milky-way', 'dark-black-moon', 'dark-comet', 'dark-spiral-galaxy'
]

# --- Core Logic ---
# No changes needed here. The logic is perfectly scalable.
def get_theme():
    """Gets the saved theme from Anki's configuration."""
    return mw.col.conf.get(THEME_KEY, 'light-full-moon') # Default to the first theme

def save_theme(theme):
    """Saves the selected theme to Anki's configuration if it's valid."""
    if theme in THEMES:
        mw.col.conf[THEME_KEY] = theme
        mw.col.setMod()

def handle_theme_message(message: str) -> bool:
    """Parses messages from the webview to save the theme."""
    prefix = f"ankiconfig:{THEME_KEY}:"
    if message.startswith(prefix):
        theme = message[len(prefix):]
        save_theme(theme)
        return True
    return False

# --- Hook for Modern Anki Desktop ---
# No changes needed.
def on_js_message(handled: tuple[bool, Any], message: str, context: Any) -> tuple[bool, Any]:
    """Catches theme change messages from the webview."""
    if handle_theme_message(message):
        return (True, None)
    return handled

# --- Hook for injecting the theme meta tag ---
# No changes needed.
def on_card_will_show(html: str, card, context) -> str:
    """Injects a meta tag with the current theme for faster initial loading."""
    theme = get_theme()
    meta_tag = f'<meta name="anki-theme" content="{theme}">'
    # Inject after <head> if it exists, otherwise prepend.
    if '<head>' in html:
        html = html.replace('<head>', f'<head>{meta_tag}', 1)
    else:
        html = f"{meta_tag}" + html
    return html

# --- The Stable Monkey-Patch for Legacy/Mobile ---
# No changes needed here. This ensures cross-platform compatibility.
# 1. Store a reference to the original function
original_link_handler = Reviewer._linkHandler

def joplin_theme_link_handler(reviewer: Reviewer, url: str):
    """
    Custom link handler that intercepts theme messages before passing
    other links to the original Anki handler.
    """
    # 2. Check if the command is for us. If so, handle it and stop.
    if handle_theme_message(url):
        return
    # 3. If the command was not for us, call the original Anki function.
    return original_link_handler(reviewer, url)

# 4. Replace Anki's function with our new, extended one.
Reviewer._linkHandler = joplin_theme_link_handler

# --- Register the necessary hooks ---
gui_hooks.webview_did_receive_js_message.append(on_js_message)
gui_hooks.card_will_show.append(on_card_will_show)

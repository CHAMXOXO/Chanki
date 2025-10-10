# -*- coding: utf-8 -*-
# Joplin Anki Theme Persistence Add-on (v2 - Production Ready)
# Implements suggestions for robustness and configurability.

from aqt import mw, gui_hooks
from aqt.reviewer import Reviewer
from typing import Any

# --- Improvement 1: Centralized Configuration ---
# Load the configuration from config.json. This is the modern Anki standard.
# It makes your add-on cleaner and easier for you or others to manage.
config = mw.addonManager.getConfig(__name__)
THEME_KEY = config.get('theme_key', 'joplinAnkiTheme_v4') # Default to v4 if not set

# --- Core Logic ---
def get_current_theme():
    """Retrieves the saved theme from Anki's collection configuration."""
    return mw.col.conf.get(THEME_KEY, config.get('default_theme', 'sun-1'))

def save_theme_from_webview(theme: str):
    """Saves the theme received from the webview to the configuration."""
    # A simple check to ensure the theme string is valid before saving.
    if theme and '-' in theme and len(theme) > 2:
        mw.col.conf[THEME_KEY] = theme
        mw.col.setMod()
        # --- Improvement 2: Enhanced Logging ---
        # This message will appear in Anki's console when you change themes,
        # making it very easy to debug.
        print(f"Joplin Theme Add-on: Saved theme -> {theme}")

def handle_js_message(message: str) -> bool:
    """Checks if a message from the webview is intended for this add-on."""
    prefix = f"ankiconfig:{THEME_KEY}:"
    if message.startswith(prefix):
        theme_to_save = message[len(prefix):]
        save_theme_from_webview(theme_to_save)
        return True
    return False

# --- Hook Implementations ---

# Hook for modern Anki Desktop (2.1.50+)
def on_webview_js_message(handled: tuple[bool, Any], message: str, context: Any) -> tuple[bool, Any]:
    """Catches messages sent from the card's JavaScript."""
    if handle_js_message(message):
        return (True, None)
    return handled

# Hook for injecting the theme meta tag before a card is displayed.
def on_card_will_show(html: str, card, context) -> str:
    """Injects the current theme as a meta tag into the card's HTML head."""
    theme = get_current_theme()
    meta_tag = f'<meta name="anki-theme" content="{theme}">'
    if '<head>' in html:
        return html.replace('<head>', f'<head>{meta_tag}', 1)
    else:
        return f"<head>{meta_tag}</head>" + html

# --- Improvement 3: Future-Proof Monkey-Patch for Legacy/Mobile ---
def apply_legacy_link_handler():
    """
    Safely patches the reviewer's link handler for compatibility with
    AnkiMobile, AnkiDroid, and older Anki desktop versions.
    """
    try:
        original_link_handler = Reviewer._linkHandler
        
        def joplin_theme_link_handler(reviewer: Reviewer, url: str):
            """
            Our custom link handler that first checks for our theme message
            before passing control back to Anki's original handler.
            """
            if handle_js_message(url):
                return
            return original_link_handler(reviewer, url)
        
        Reviewer._linkHandler = joplin_theme_link_handler
        print("Joplin Theme Add-on: Successfully applied legacy link handler.")
    except AttributeError:
        print("Joplin Theme Add-on: Could not apply legacy link handler (not needed in this Anki version).")

# --- Final Registration ---
def initialize_addon():
    """Registers all necessary hooks and applies patches."""
    gui_hooks.webview_did_receive_js_message.append(on_webview_js_message)
    gui_hooks.card_will_show.append(on_card_will_show)
    apply_legacy_link_handler()

# Initialize the add-on when Anki starts.
initialize_addon()

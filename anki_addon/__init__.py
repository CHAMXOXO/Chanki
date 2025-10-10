# -*- coding: utf-8 -*-

from aqt import mw, gui_hooks
from aqt.reviewer import Reviewer
from typing import Any

THEME_KEY = 'joplinAnkiTheme_v3'
THEMES = ['light', 'light-dark', 'balanced', 'dark-light', 'true-dark']

# --- Core Logic ---
def get_theme():
    return mw.col.conf.get(THEME_KEY, 'light')

def save_theme(theme):
    if theme in THEMES:
        mw.col.conf[THEME_KEY] = theme
        mw.col.setMod()

def handle_theme_message(message: str) -> bool:
    prefix = f"ankiconfig:{THEME_KEY}:"
    if message.startswith(prefix):
        theme = message[len(prefix):]
        save_theme(theme)
        return True
    return False

# --- Hook for Modern Anki Desktop ---
def on_js_message(handled: tuple[bool, Any], message: str, context: Any) -> tuple[bool, Any]:
    if handle_theme_message(message):
        return (True, None)
    return handled

# --- Hook for injecting the theme meta tag ---
def on_card_will_show(html: str, card, context) -> str:
    theme = get_theme()
    meta_tag = f'<meta name="anki-theme" content="{theme}">'
    if '<head>' in html:
        html = html.replace('<head>', f'<head>{meta_tag}', 1)
    else:
        html = f"<head>{meta_tag}</head>" + html
    return html

# --- The Stable Monkey-Patch for Legacy/Mobile ---
# This replaces the 'wrap' function, which was causing the crash.

# 1. Store a reference to the original function
original_link_handler = Reviewer._linkHandler

def joplin_theme_link_handler(reviewer: Reviewer, url: str):
    """
    This is our custom link handler. It runs first.
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


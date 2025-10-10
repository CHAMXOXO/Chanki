# __init__.py (FINAL CORRECTED VERSION for Anki 24.09+)
# -*- coding: utf-8 -*-

# --- IMPORTS ---
from aqt import mw, gui_hooks
from aqt.qt import QAction, QMenu
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
/* 1.2: light-waning-gibbous (Sepia/Paper) */
body.theme-light-waning-gibbous{background:#fdf6e3}
.theme-light-waning-gibbous .card-container,.theme-light-waning-gibbous .cloze-container,.theme-light-waning-gibbous .mcq-container,.theme-light-waning-gibbous .image-container{background:rgba(253,246,227,0.9);backdrop-filter:none;color:#586e75;border:1px solid #eee8d5}
.theme-light-waning-gibbous .meta-header,.theme-light-waning-gibbous .header,.theme-light-waning-gibbous .cloze-header,.theme-light-waning-gibbous .mcq-header,.theme-light-waning-gibbous .image-header{background:linear-gradient(135deg,#cb4b16 0%,#dc322f 100%)}
.theme-light-waning-gibbous .card-type,.theme-light-waning-gibbous .cloze-title,.theme-light-waning-gibbous .mcq-title,.theme-light-waning-gibbous .image-title,.theme-light-waning-gibbous .header-text{color:#fdf6e3!important}
.theme-light-waning-gibbous .question-text,.theme-light-waning-gibbous .question-section{color:#859900!important}
.theme-light-waning-gibbous .answer-text,.theme-light-waning-gibbous .cloze-content{color:#268bd2!important}
.theme-light-waning-gibbous .cloze{background:linear-gradient(135deg,#2aa198,#268bd2)!important;color:#fdf6e3}
.theme-light-waning-gibbous .explanation-block,.theme-light-waning-gibbous .explanation-section,.theme-light-waning-gibbous .explanation-info{background:#f5fff5;border-left:5px solid #859900}
.theme-light-waning-gibbous .correlation-block,.theme-light-waning-gibbous .correlation-section,.theme-light-waning-gibbous .correlation-info{background:#f0f8ff;border-left:5px solid #268bd2}
.theme-light-waning-gibbous .extra-info,.theme-light-waning-gibbous .comments-block{background:#fff5f5;border-left:5px solid #dc322f}
/* 1.3: light-last-quarter (Cool Mint) */
body.theme-light-last-quarter{background:linear-gradient(135deg,#E0F2F1 0%,#B2DFDB 100%)}
.theme-light-last-quarter .card-container,.theme-light-last-quarter .cloze-container,.theme-light-last-quarter .mcq-container,.theme-light-last-quarter .image-container{background:rgba(255,255,255,0.8);backdrop-filter:blur(10px);color:#004D40;border:1px solid #80CBC4}
.theme-light-last-quarter .meta-header,.theme-light-last-quarter .header,.theme-light-last-quarter .cloze-header,.theme-light-last-quarter .mcq-header,.theme-light-last-quarter .image-header{background:linear-gradient(135deg,#00796B 0%,#009688 100%)}
.theme-light-last-quarter .card-type,.theme-light-last-quarter .cloze-title,.theme-light-last-quarter .mcq-title,.theme-light-last-quarter .image-title,.theme-light-last-quarter .header-text{color:#E0F2F1!important}
.theme-light-last-quarter .question-text,.theme-light-last-quarter .question-section{color:#00695C!important}
.theme-light-last-quarter .answer-text,.theme-light-last-quarter .cloze-content{color:#3949AB!important}
.theme-light-last-quarter .cloze{background:linear-gradient(135deg,#00897B,#4DB6AC)!important;color:#fff}
.theme-light-last-quarter .explanation-block,.theme-light-last-quarter .explanation-section,.theme-light-last-quarter .explanation-info{background:#E8F5E9;border-left:5px solid #4CAF50}
.theme-light-last-quarter .correlation-block,.theme-light-last-quarter .correlation-section,.theme-light-last-quarter .correlation-info{background:#E3F2FD;border-left:5px solid #2196F3}
.theme-light-last-quarter .extra-info,.theme-light-last-quarter .comments-block{background:#FBE9E7;border-left:5px solid #FF5722}
/* 1.4: light-waning-crescent (Soft Lavender) */
body.theme-light-waning-crescent{background:#f3e5f5}
.theme-light-waning-crescent .card-container,.theme-light-waning-crescent .cloze-container,.theme-light-waning-crescent .mcq-container,.theme-light-waning-crescent .image-container{background:rgba(243,229,245,0.85);backdrop-filter:none;color:#4A148C;border:1px solid #CE93D8}
.theme-light-waning-crescent .meta-header,.theme-light-waning-crescent .header,.theme-light-waning-crescent .cloze-header,.theme-light-waning-crescent .mcq-header,.theme-light-waning-crescent .image-header{background:linear-gradient(135deg,#8E24AA 0%,#AB47BC 100%)}
.theme-light-waning-crescent .card-type,.theme-light-waning-crescent .cloze-title,.theme-light-waning-crescent .mcq-title,.theme-light-waning-crescent .image-title,.theme-light-waning-crescent .header-text{color:#F3E5F5!important}
.theme-light-waning-crescent .question-text,.theme-light-waning-crescent .question-section{color:#6A1B9A!important}
.theme-light-waning-crescent .answer-text,.theme-light-waning-crescent .cloze-content{color:#AD1457!important}
.theme-light-waning-crescent .cloze{background:linear-gradient(135deg,#7B1FA2,#9C27B0)!important;color:#fff}
.theme-light-waning-crescent .explanation-block,.theme-light-waning-crescent .explanation-section,.theme-light-waning-crescent .explanation-info{background:#FCE4EC;border-left:5px solid #EC407A}
.theme-light-waning-crescent .correlation-block,.theme-light-waning-crescent .correlation-section,.theme-light-waning-crescent .correlation-info{background:#E1F5FE;border-left:5px solid #03A9F4}
.theme-light-waning-crescent .extra-info,.theme-light-waning-crescent .comments-block{background:#FFFDE7;border-left:5px solid #FBC02D}
/* 1.5: light-new-moon (Minimalist White) */
body.theme-light-new-moon{background:#f8f9fa}
.theme-light-new-moon .card-container,.theme-light-new-moon .cloze-container,.theme-light-new-moon .mcq-container,.theme-light-new-moon .image-container{background:#fff;backdrop-filter:none;color:#212529;border:1px solid #dee2e6}
.theme-light-new-moon .meta-header,.theme-light-new-moon .header,.theme-light-new-moon .cloze-header,.theme-light-new-moon .mcq-header,.theme-light-new-moon .image-header{background:#343a40}
.theme-light-new-moon .card-type,.theme-light-new-moon .cloze-title,.theme-light-new-moon .mcq-title,.theme-light-new-moon .image-title,.theme-light-new-moon .header-text{color:#f8f9fa!important}
.theme-light-new-moon .question-text,.theme-light-new-moon .question-section{color:#007bff!important}
.theme-light-new-moon .answer-text,.theme-light-new-moon .cloze-content{color:#28a745!important}
.theme-light-new-moon .cloze{background:#007bff!important;color:#fff}
.theme-light-new-moon .explanation-block,.theme-light-new-moon .explanation-section,.theme-light-new-moon .explanation-info{background:#e9ecef;border-left:5px solid #6c757d}
.theme-light-new-moon .correlation-block,.theme-light-new-moon .correlation-section,.theme-light-new-moon .correlation-info{background:#e2e3e5;border-left:5px solid #343a40}
.theme-light-new-moon .extra-info,.theme-light-new-moon .comments-block{background:#fff3cd;border-left:5px solid #ffc107}
/* =================================================================== */
/* =================== ☀️ FAMILY: NORD THEMES ======================== */
/* =================================================================== */
/* 2.1: nord-bright-sun (Original Light-Dark) */
body.theme-nord-bright-sun{background:linear-gradient(to top,#30cfd0 0%,#330867 100%)}
.theme-nord-bright-sun .card-container,.theme-nord-bright-sun .cloze-container,.theme-nord-bright-sun .mcq-container,.theme-nord-bright-sun .image-container{background:rgba(45,55,72,0.85);backdrop-filter:blur(12px);color:#A0AEC0;border:1px solid rgba(113,128,150,0.8)}
.theme-nord-bright-sun .meta-header,.theme-nord-bright-sun .header,.theme-nord-bright-sun .cloze-header,.theme-nord-bright-sun .mcq-header,.theme-nord-bright-sun .image-header{background:linear-gradient(135deg,#06b6d4 0%,#3b82f6 100%)}
.theme-nord-bright-sun .card-type,.theme-nord-bright-sun .cloze-title,.theme-nord-bright-sun .mcq-title,.theme-nord-bright-sun .image-title,.theme-nord-bright-sun .header-text{color:#E0F2FE!important}
.theme-nord-bright-sun .question-text,.theme-nord-bright-sun .question-section{color:#90CDF4!important}
.theme-nord-bright-sun .answer-text,.theme-nord-bright-sun .cloze-content{color:#81E6D9!important}
.theme-nord-bright-sun .cloze{background:linear-gradient(135deg,#06b6d4,#81E6D9)!important;color:#1A202C}
.theme-nord-bright-sun .explanation-block,.theme-nord-bright-sun .explanation-section,.theme-nord-bright-sun .explanation-info{background:rgba(49,151,149,0.2);border-left:5px solid #38B2AC}
.theme-nord-bright-sun .correlation-block,.theme-nord-bright-sun .correlation-section,.theme-nord-bright-sun .correlation-info{background:rgba(66,153,225,0.2);border-left:5px solid #4299E1}
.theme-nord-bright-sun .extra-info,.theme-nord-bright-sun .comments-block{background:rgba(213,63,140,0.2);border-left:5px solid #D53F8C}
/* 2.2: nord-overcast-day (Cool Gray/Blue) */
body.theme-nord-overcast-day{background:linear-gradient(135deg,#BCC6CC 0%,#94A3B8 100%)}
.theme-nord-overcast-day .card-container,.theme-nord-overcast-day .cloze-container,.theme-nord-overcast-day .mcq-container,.theme-nord-overcast-day .image-container{background:rgba(255,255,255,0.7);backdrop-filter:blur(8px);color:#334155;border:1px solid rgba(226,232,240,0.9)}
.theme-nord-overcast-day .meta-header,.theme-nord-overcast-day .header,.theme-nord-overcast-day .cloze-header,.theme-nord-overcast-day .mcq-header,.theme-nord-overcast-day .image-header{background:linear-gradient(135deg,#64748B 0%,#475569 100%)}
.theme-nord-overcast-day .card-type,.theme-nord-overcast-day .cloze-title,.theme-nord-overcast-day .mcq-title,.theme-nord-overcast-day .image-title,.theme-nord-overcast-day .header-text{color:#F1F5F9!important}
.theme-nord-overcast-day .question-text,.theme-nord-overcast-day .question-section{color:#0F172A!important}
.theme-nord-overcast-day .answer-text,.theme-nord-overcast-day .cloze-content{color:#1E40AF!important}
.theme-nord-overcast-day .cloze{background:linear-gradient(135deg,#475569,#1E293B)!important;color:#F8FAFC}
.theme-nord-overcast-day .explanation-block,.theme-nord-overcast-day .explanation-section,.theme-nord-overcast-day .explanation-info{background:#E2E8F0;border-left:5px solid #94A3B8}
.theme-nord-overcast-day .correlation-block,.theme-nord-overcast-day .correlation-section,.theme-nord-overcast-day .correlation-info{background:#DBEAFE;border-left:5px solid #60A5FA}
.theme-nord-overcast-day .extra-info,.theme-nord-overcast-day .comments-block{background:#FEF3C7;border-left:5px solid #F59E0B}
/* 2.3: nord-stormy-sky (Deep Blue/Gray with Yellow flash) */
body.theme-nord-stormy-sky{background:linear-gradient(135deg,#4A5568 0%,#1A202C 100%)}
.theme-nord-stormy-sky .card-container,.theme-nord-stormy-sky .cloze-container,.theme-nord-stormy-sky .mcq-container,.theme-nord-stormy-sky .image-container{background:rgba(45,55,72,0.8);backdrop-filter:blur(10px);color:#E2E8F0;border:1px solid #718096}
.theme-nord-stormy-sky .meta-header,.theme-nord-stormy-sky .header,.theme-nord-stormy-sky .cloze-header,.theme-nord-stormy-sky .mcq-header,.theme-nord-stormy-sky .image-header{background:linear-gradient(135deg,#FBBF24 0%,#F59E0B 100%)}
.theme-nord-stormy-sky .card-type,.theme-nord-stormy-sky .cloze-title,.theme-nord-stormy-sky .mcq-title,.theme-nord-stormy-sky .image-title,.theme-nord-stormy-sky .header-text{color:#422006!important}
.theme-nord-stormy-sky .question-text,.theme-nord-stormy-sky .question-section{color:#FCD34D!important}
.theme-nord-stormy-sky .answer-text,.theme-nord-stormy-sky .cloze-content{color:#93C5FD!important}
.theme-nord-stormy-sky .cloze{background:linear-gradient(135deg,#1E40AF,#3B82F6)!important;color:#EFF6FF}
.theme-nord-stormy-sky .explanation-block,.theme-nord-stormy-sky .explanation-section,.theme-nord-stormy-sky .explanation-info{background:rgba(147,197,253,0.1);border-left:5px solid #60A5FA}
.theme-nord-stormy-sky .correlation-block,.theme-nord-stormy-sky .correlation-section,.theme-nord-stormy-sky .correlation-info{background:rgba(252,211,77,0.1);border-left:5px solid #FBBF24}
.theme-nord-stormy-sky .extra-info,.theme-nord-stormy-sky .comments-block{background:rgba(248,113,113,0.1);border-left:5px solid #F87171}
/* 2.4: nord-aurora (Dark blue with green/cyan glows) */
body.theme-nord-aurora{background:linear-gradient(-45deg,#02042b,#0f172a,#02042b)}
.theme-nord-aurora .card-container,.theme-nord-aurora .cloze-container,.theme-nord-aurora .mcq-container,.theme-nord-aurora .image-container{background:rgba(15,23,42,0.8);backdrop-filter:blur(12px);color:#94A3B8;border:1px solid #334155}
.theme-nord-aurora .meta-header,.theme-nord-aurora .header,.theme-nord-aurora .cloze-header,.theme-nord-aurora .mcq-header,.theme-nord-aurora .image-header{background:linear-gradient(135deg,#10B981 0%,#2DD4BF 100%)}
.theme-nord-aurora .card-type,.theme-nord-aurora .cloze-title,.theme-nord-aurora .mcq-title,.theme-nord-aurora .image-title,.theme-nord-aurora .header-text{color:#064E3B!important}
.theme-nord-aurora .question-text,.theme-nord-aurora .question-section{color:#6EE7B7!important}
.theme-nord-aurora .answer-text,.theme-nord-aurora .cloze-content{color:#5EEAD4!important}
.theme-nord-aurora .cloze{background:linear-gradient(135deg,#059669,#14B8A6)!important;color:#F0FDFA}
.theme-nord-aurora .explanation-block,.theme-nord-aurora .explanation-section,.theme-nord-aurora .explanation-info{background:rgba(20,184,166,0.1);border-left:5px solid #14B8A6}
.theme-nord-aurora .correlation-block,.theme-nord-aurora .correlation-section,.theme-nord-aurora .correlation-info{background:rgba(139,92,246,0.1);border-left:5px solid #8B5CF6}
.theme-nord-aurora .extra-info,.theme-nord-aurora .comments-block{background:rgba(236,72,153,0.1);border-left:5px solid #EC4899}
/* 2.5: nord-polar-night (Very Dark Nord) */
body.theme-nord-polar-night{background:#2E3440}
.theme-nord-polar-night .card-container,.theme-nord-polar-night .cloze-container,.theme-nord-polar-night .mcq-container,.theme-nord-polar-night .image-container{background:#3B4252;backdrop-filter:none;color:#D8DEE9;border:1px solid #4C566A}
.theme-nord-polar-night .meta-header,.theme-nord-polar-night .header,.theme-nord-polar-night .cloze-header,.theme-nord-polar-night .mcq-header,.theme-nord-polar-night .image-header{background:#5E81AC}
.theme-nord-polar-night .card-type,.theme-nord-polar-night .cloze-title,.theme-nord-polar-night .mcq-title,.theme-nord-polar-night .image-title,.theme-nord-polar-night .header-text{color:#ECEFF4!important}
.theme-nord-polar-night .question-text,.theme-nord-polar-night .question-section{color:#88C0D0!important}
.theme-nord-polar-night .answer-text,.theme-nord-polar-night .cloze-content{color:#A3BE8C!important}
.theme-nord-polar-night .cloze{background:#81A1C1!important;color:#2E3440}
.theme-nord-polar-night .explanation-block,.theme-nord-polar-night .explanation-section,.theme-nord-polar-night .explanation-info{background:#434C5E;border-left:5px solid #A3BE8C}
.theme-nord-polar-night .correlation-block,.theme-nord-polar-night .correlation-section,.theme-nord-polar-night .correlation-info{background:#434C5E;border-left:5px solid #EBCB8B}
.theme-nord-polar-night .extra-info,.theme-nord-polar-night .comments-block{background:#434C5E;border-left:5px solid #BF616A}
/* =================================================================== */
/* ================== ⭐ FAMILY: BALANCED THEMES ===================== */
/* =================================================================== */
/* 3.1: balanced-star (Original Balanced) */
body.theme-balanced-star{background:linear-gradient(to right,#434343 0%,black 100%)}
.theme-balanced-star .card-container,.theme-balanced-star .cloze-container,.theme-balanced-star .mcq-container,.theme-balanced-star .image-container{background:rgba(55,65,81,0.7);backdrop-filter:blur(14px);color:#D1D5DB;border:1px solid #9CA3AF}
.theme-balanced-star .meta-header,.theme-balanced-star .header,.theme-balanced-star .cloze-header,.theme-balanced-star .mcq-header,.theme-balanced-star .image-header{background:linear-gradient(135deg,#a18cd1 0%,#fbc2eb 100%)}
.theme-balanced-star .card-type,.theme-balanced-star .cloze-title,.theme-balanced-star .mcq-title,.theme-balanced-star .image-title,.theme-balanced-star .header-text{color:#3730A3!important}
.theme-balanced-star .question-text,.theme-balanced-star .question-section{color:#FBCFE8!important}
.theme-balanced-star .answer-text,.theme-balanced-star .cloze-content{color:#C4B5FD!important}
.theme-balanced-star .cloze{background:linear-gradient(135deg,#a18cd1,#fbc2eb)!important;color:#4B5563}
.theme-balanced-star .explanation-block,.theme-balanced-star .explanation-section,.theme-balanced-star .explanation-info{background:rgba(196,181,253,0.1);border-left:5px solid #A78BFA}
.theme-balanced-star .correlation-block,.theme-balanced-star .correlation-section,.theme-balanced-star .correlation-info{background:rgba(251,207,232,0.1);border-left:5px solid #F472B6}
.theme-balanced-star .extra-info,.theme-balanced-star .comments-block{background:rgba(134,239,172,0.1);border-left:5px solid #4ADE80}
/* 3.2: balanced-nebula (Deep Purples and Pinks) */
body.theme-balanced-nebula{background:linear-gradient(135deg,#23074d 0%,#cc5333 100%)}
.theme-balanced-nebula .card-container,.theme-balanced-nebula .cloze-container,.theme-balanced-nebula .mcq-container,.theme-balanced-nebula .image-container{background:rgba(30,27,58,0.8);backdrop-filter:blur(12px);color:#D9CFFC;border:1px solid #6D28D9}
.theme-balanced-nebula .meta-header,.theme-balanced-nebula .header,.theme-balanced-nebula .cloze-header,.theme-balanced-nebula .mcq-header,.theme-balanced-nebula .image-header{background:linear-gradient(135deg,#BE185D 0%,#E11D48 100%)}
.theme-balanced-nebula .card-type,.theme-balanced-nebula .cloze-title,.theme-balanced-nebula .mcq-title,.theme-balanced-nebula .image-title,.theme-balanced-nebula .header-text{color:#FDF2F8!important}
.theme-balanced-nebula .question-text,.theme-balanced-nebula .question-section{color:#F472B6!important}
.theme-balanced-nebula .answer-text,.theme-balanced-nebula .cloze-content{color:#A5B4FC!important}
.theme-balanced-nebula .cloze{background:linear-gradient(135deg,#9D174D,#BE185D)!important;color:#FFE4E6}
.theme-balanced-nebula .explanation-block,.theme-balanced-nebula .explanation-section,.theme-balanced-nebula .explanation-info{background:rgba(165,180,252,0.1);border-left:5px solid #818CF8}
.theme-balanced-nebula .correlation-block,.theme-balanced-nebula .correlation-section,.theme-balanced-nebula .correlation-info{background:rgba(244,114,182,0.1);border-left:5px solid #F472B6}
.theme-balanced-nebula .extra-info,.theme-balanced-nebula .comments-block{background:rgba(251,146,60,0.1);border-left:5px solid #FB923C}
/* 3.3: balanced-supernova (Bright Oranges and Reds) */
body.theme-balanced-supernova{background:linear-gradient(135deg,#ff4e50 0%,#f9d423 100%)}
.theme-balanced-supernova .card-container,.theme-balanced-supernova .cloze-container,.theme-balanced-supernova .mcq-container,.theme-balanced-supernova .image-container{background:rgba(40,10,5,0.8);backdrop-filter:blur(10px);color:#FDE68A;border:1px solid #F97316}
.theme-balanced-supernova .meta-header,.theme-balanced-supernova .header,.theme-balanced-supernova .cloze-header,.theme-balanced-supernova .mcq-header,.theme-balanced-supernova .image-header{background:linear-gradient(135deg,#DC2626 0%,#F59E0B 100%)}
.theme-balanced-supernova .card-type,.theme-balanced-supernova .cloze-title,.theme-balanced-supernova .mcq-title,.theme-balanced-supernova .image-title,.theme-balanced-supernova .header-text{color:#FFFBEB!important}
.theme-balanced-supernova .question-text,.theme-balanced-supernova .question-section{color:#F87171!important}
.theme-balanced-supernova .answer-text,.theme-balanced-supernova .cloze-content{color:#FCD34D!important}
.theme-balanced-supernova .cloze{background:linear-gradient(135deg,#D97706,#F97316)!important;color:#FFEDD5}
.theme-balanced-supernova .explanation-block,.theme-balanced-supernova .explanation-section,.theme-balanced-supernova .explanation-info{background:rgba(252,211,77,0.1);border-left:5px solid #FBBF24}
.theme-balanced-supernova .correlation-block,.theme-balanced-supernova .correlation-section,.theme-balanced-supernova .correlation-info{background:rgba(248,113,113,0.1);border-left:5px solid #EF4444}
.theme-balanced-supernova .extra-info,.theme-balanced-supernova .comments-block{background:rgba(240,253,244,0.1);border-left:5px solid #A3E635}
/* 3.4: balanced-galaxy (Deep Indigo and Silver) */
body.theme-balanced-galaxy{background:linear-gradient(135deg,#16222A 0%,#3A6073 100%)}
.theme-balanced-galaxy .card-container,.theme-balanced-galaxy .cloze-container,.theme-balanced-galaxy .mcq-container,.theme-balanced-galaxy .image-container{background:rgba(23,37,84,0.8);backdrop-filter:blur(12px);color:#E0E7FF;border:1px solid #4338CA}
.theme-balanced-galaxy .meta-header,.theme-balanced-galaxy .header,.theme-balanced-galaxy .cloze-header,.theme-balanced-galaxy .mcq-header,.theme-balanced-galaxy .image-header{background:linear-gradient(135deg,#9CA3AF 0%,#E5E7EB 100%)}
.theme-balanced-galaxy .card-type,.theme-balanced-galaxy .cloze-title,.theme-balanced-galaxy .mcq-title,.theme-balanced-galaxy .image-title,.theme-balanced-galaxy .header-text{color:#1F2937!important}
.theme-balanced-galaxy .question-text,.theme-balanced-galaxy .question-section{color:#C7D2FE!important}
.theme-balanced-galaxy .answer-text,.theme-balanced-galaxy .cloze-content{color:#A5F3FC!important}
.theme-balanced-galaxy .cloze{background:linear-gradient(135deg,#4F46E5,#6366F1)!important;color:#EEF2FF}
.theme-balanced-galaxy .explanation-block,.theme-balanced-galaxy .explanation-section,.theme-balanced-galaxy .explanation-info{background:rgba(165,243,252,0.1);border-left:5px solid #22D3EE}
.theme-balanced-galaxy .correlation-block,.theme-balanced-galaxy .correlation-section,.theme-balanced-galaxy .correlation-info{background:rgba(199,210,254,0.1);border-left:5px solid #A5B4FC}
.theme-balanced-galaxy .extra-info,.theme-balanced-galaxy .comments-block{background:rgba(209,213,219,0.1);border-left:5px solid #9CA3AF}
/* 3.5: balanced-comet (Icy Cyan on Dark Blue) */
body.theme-balanced-comet{background:linear-gradient(135deg,#0f2027 0%,#203a43 100%)}
.theme-balanced-comet .card-container,.theme-balanced-comet .cloze-container,.theme-balanced-comet .mcq-container,.theme-balanced-comet .image-container{background:rgba(4,22,37,0.8);backdrop-filter:blur(10px);color:#CFFAFE;border:1px solid #0E7490}
.theme-balanced-comet .meta-header,.theme-balanced-comet .header,.theme-balanced-comet .cloze-header,.theme-balanced-comet .mcq-header,.theme-balanced-comet .image-header{background:linear-gradient(135deg,#06B6D4 0%,#67E8F9 100%)}
.theme-balanced-comet .card-type,.theme-balanced-comet .cloze-title,.theme-balanced-comet .mcq-title,.theme-balanced-comet .image-title,.theme-balanced-comet .header-text{color:#155E75!important}
.theme-balanced-comet .question-text,.theme-balanced-comet .question-section{color:#22D3EE!important}
.theme-balanced-comet .answer-text,.theme-balanced-comet .cloze-content{color:#A7F3D0!important}
.theme-balanced-comet .cloze{background:linear-gradient(135deg,#0891B2,#22D3EE)!important;color:#F0FDF4}
.theme-balanced-comet .explanation-block,.theme-balanced-comet .explanation-section,.theme-balanced-comet .explanation-info{background:rgba(167,243,208,0.1);border-left:5px solid #6EE7B7}
.theme-balanced-comet .correlation-block,.theme-balanced-comet .correlation-section,.theme-balanced-comet .correlation-info{background:rgba(165,243,252,0.1);border-left:5px solid #67E8F9}
.theme-balanced-comet .extra-info,.theme-balanced-comet .comments-block{background:rgba(199,210,254,0.1);border-left:5px solid #A5B4FC}
/* =================================================================== */
/* ================= 🌙 FAMILY: TWILIGHT THEMES ===================== */
/* =================================================================== */
/* 4.1: twilight-crescent-moon (Original Dark-Light) */
body.theme-twilight-crescent-moon{background:linear-gradient(-225deg,#222222 0%,#24292e 100%)}
.theme-twilight-crescent-moon .card-container,.theme-twilight-crescent-moon .cloze-container,.theme-twilight-crescent-moon .mcq-container,.theme-twilight-crescent-moon .image-container{background:rgba(31,41,55,0.7);backdrop-filter:blur(14px);color:#E5E7EB;border:1px solid #6B7280}
.theme-twilight-crescent-moon .meta-header,.theme-twilight-crescent-moon .header,.theme-twilight-crescent-moon .cloze-header,.theme-twilight-crescent-moon .mcq-header,.theme-twilight-crescent-moon .image-header{background:linear-gradient(135deg,#868F96 0%,#596164 100%)}
.theme-twilight-crescent-moon .card-type,.theme-twilight-crescent-moon .cloze-title,.theme-twilight-crescent-moon .mcq-title,.theme-twilight-crescent-moon .image-title,.theme-twilight-crescent-moon .header-text{color:#1F2937!important}
.theme-twilight-crescent-moon .question-text,.theme-twilight-crescent-moon .question-section{color:#BAE6FD!important}
.theme-twilight-crescent-moon .answer-text,.theme-twilight-crescent-moon .cloze-content{color:#D9F99D!important}
.theme-twilight-crescent-moon .cloze{background:linear-gradient(135deg,#0EA5E9,#84CC16)!important;color:#F0F9FF}
.theme-twilight-crescent-moon .explanation-block,.theme-twilight-crescent-moon .explanation-section,.theme-twilight-crescent-moon .explanation-info{background:rgba(217,249,157,0.1);border-left:5px solid #A3E635}
.theme-twilight-crescent-moon .correlation-block,.theme-twilight-crescent-moon .correlation-section,.theme-twilight-crescent-moon .correlation-info{background:rgba(186,230,253,0.1);border-left:5px solid #38BDF8}
.theme-twilight-crescent-moon .extra-info,.theme-twilight-crescent-moon .comments-block{background:rgba(252,211,77,0.1);border-left:5px solid #FBBF24}
/* 4.2: twilight-city-night (Neon on Charcoal) */
body.theme-twilight-city-night{background:linear-gradient(135deg,#35373B 0%,#191919 100%)}
.theme-twilight-city-night .card-container,.theme-twilight-city-night .cloze-container,.theme-twilight-city-night .mcq-container,.theme-twilight-city-night .image-container{background:rgba(30,30,30,0.8);backdrop-filter:blur(10px);color:#F5F5F5;border:1px solid #525252}
.theme-twilight-city-night .meta-header,.theme-twilight-city-night .header,.theme-twilight-city-night .cloze-header,.theme-twilight-city-night .mcq-header,.theme-twilight-city-night .image-header{background:linear-gradient(135deg,#EC4899 0%,#D946EF 100%)}
.theme-twilight-city-night .card-type,.theme-twilight-city-night .cloze-title,.theme-twilight-city-night .mcq-title,.theme-twilight-city-night .image-title,.theme-twilight-city-night .header-text{color:#FCE7F3!important}
.theme-twilight-city-night .question-text,.theme-twilight-city-night .question-section{color:#A5F3FC!important}
.theme-twilight-city-night .answer-text,.theme-twilight-city-night .cloze-content{color:#F9A8D4!important}
.theme-twilight-city-night .cloze{background:linear-gradient(135deg,#0EA5E9,#22D3EE)!important;color:#F0F9FF}
.theme-twilight-city-night .explanation-block,.theme-twilight-city-night .explanation-section,.theme-twilight-city-night .explanation-info{background:rgba(249,168,212,0.1);border-left:5px solid #F472B6}
.theme-twilight-city-night .correlation-block,.theme-twilight-city-night .correlation-section,.theme-twilight-city-night .correlation-info{background:rgba(165,243,252,0.1);border-left:5px solid #67E8F9}
.theme-twilight-city-night .extra-info,.theme-twilight-city-night .comments-block{background:rgba(167,243,208,0.1);border-left:5px solid #34D399}
/* 4.3: twilight-deep-forest (Earthy dark greens/browns) */
body.theme-twilight-deep-forest{background:linear-gradient(135deg,#29323c 0%,#485563 100%)}
.theme-twilight-deep-forest .card-container,.theme-twilight-deep-forest .cloze-container,.theme-twilight-deep-forest .mcq-container,.theme-twilight-deep-forest .image-container{background:rgba(21,32,23,0.8);backdrop-filter:blur(10px);color:#D4D4D2;border:1px solid #22C55E}
.theme-twilight-deep-forest .meta-header,.theme-twilight-deep-forest .header,.theme-twilight-deep-forest .cloze-header,.theme-twilight-deep-forest .mcq-header,.theme-twilight-deep-forest .image-header{background:linear-gradient(135deg,#16A34A 0%,#22C55E 100%)}
.theme-twilight-deep-forest .card-type,.theme-twilight-deep-forest .cloze-title,.theme-twilight-deep-forest .mcq-title,.theme-twilight-deep-forest .image-title,.theme-twilight-deep-forest .header-text{color:#DCFCE7!important}
.theme-twilight-deep-forest .question-text,.theme-twilight-deep-forest .question-section{color:#BEF264!important}
.theme-twilight-deep-forest .answer-text,.theme-twilight-deep-forest .cloze-content{color:#FDE68A!important}
.theme-twilight-deep-forest .cloze{background:linear-gradient(135deg,#65A30D,#A3E635)!important;color:#F7FEE7}
.theme-twilight-deep-forest .explanation-block,.theme-twilight-deep-forest .explanation-section,.theme-twilight-deep-forest .explanation-info{background:rgba(253,230,138,0.1);border-left:5px solid #FACC15}
.theme-twilight-deep-forest .correlation-block,.theme-twilight-deep-forest .correlation-section,.theme-twilight-deep-forest .correlation-info{background:rgba(190,242,100,0.1);border-left:5px solid #A3E635}
.theme-twilight-deep-forest .extra-info,.theme-twilight-deep-forest .comments-block{background:rgba(252,165,165,0.1);border-left:5px solid #F87171}
/* 4.4: twilight-moonlit-ocean (Silver/Pale Blue on Deep Navy) */
body.theme-twilight-moonlit-ocean{background:linear-gradient(135deg,#00122e 0%,#00285d 100%)}
.theme-twilight-moonlit-ocean .card-container,.theme-twilight-moonlit-ocean .cloze-container,.theme-twilight-moonlit-ocean .mcq-container,.theme-twilight-moonlit-ocean .image-container{background:rgba(0,25,60,0.8);backdrop-filter:blur(12px);color:#B0C4DE;border:1px solid #7B95B4}
.theme-twilight-moonlit-ocean .meta-header,.theme-twilight-moonlit-ocean .header,.theme-twilight-moonlit-ocean .cloze-header,.theme-twilight-moonlit-ocean .mcq-header,.theme-twilight-moonlit-ocean .image-header{background:linear-gradient(135deg,#B0C4DE 0%,#E6E6FA 100%)}
.theme-twilight-moonlit-ocean .card-type,.theme-twilight-moonlit-ocean .cloze-title,.theme-twilight-moonlit-ocean .mcq-title,.theme-twilight-moonlit-ocean .image-title,.theme-twilight-moonlit-ocean .header-text{color:#1E293B!important}
.theme-twilight-moonlit-ocean .question-text,.theme-twilight-moonlit-ocean .question-section{color:#ADD8E6!important}
.theme-twilight-moonlit-ocean .answer-text,.theme-twilight-moonlit-ocean .cloze-content{color:#E6E6FA!important}
.theme-twilight-moonlit-ocean .cloze{background:linear-gradient(135deg,#778899,#B0C4DE)!important;color:#00122e}
.theme-twilight-moonlit-ocean .explanation-block,.theme-twilight-moonlit-ocean .explanation-section,.theme-twilight-moonlit-ocean .explanation-info{background:rgba(230,230,250,0.1);border-left:5px solid #E6E6FA}
.theme-twilight-moonlit-ocean .correlation-block,.theme-twilight-moonlit-ocean .correlation-section,.theme-twilight-moonlit-ocean .correlation-info{background:rgba(173,216,230,0.1);border-left:5px solid #ADD8E6}
.theme-twilight-moonlit-ocean .extra-info,.theme-twilight-moonlit-ocean .comments-block{background:rgba(135,206,250,0.1);border-left:5px solid #87CEFA}
/* 4.5: twilight-dusk (Warm Oranges and Deep Purples) */
body.theme-twilight-dusk{background:linear-gradient(135deg,#2B1055 0%,#7597DE 100%)}
.theme-twilight-dusk .card-container,.theme-twilight-dusk .cloze-container,.theme-twilight-dusk .mcq-container,.theme-twilight-dusk .image-container{background:rgba(43,16,85,0.75);backdrop-filter:blur(10px);color:#F3E8FF;border:1px solid #C084FC}
.theme-twilight-dusk .meta-header,.theme-twilight-dusk .header,.theme-twilight-dusk .cloze-header,.theme-twilight-dusk .mcq-header,.theme-twilight-dusk .image-header{background:linear-gradient(135deg,#F97316 0%,#EA580C 100%)}
.theme-twilight-dusk .card-type,.theme-twilight-dusk .cloze-title,.theme-twilight-dusk .mcq-title,.theme-twilight-dusk .image-title,.theme-twilight-dusk .header-text{color:#FFEDD5!important}
.theme-twilight-dusk .question-text,.theme-twilight-dusk .question-section{color:#F0ABFC!important}
.theme-twilight-dusk .answer-text,.theme-twilight-dusk .cloze-content{color:#FDBA74!important}
.theme-twilight-dusk .cloze{background:linear-gradient(135deg,#D946EF,#C084FC)!important;color:#FAE8FF}
.theme-twilight-dusk .explanation-block,.theme-twilight-dusk .explanation-section,.theme-twilight-dusk .explanation-info{background:rgba(253,186,116,0.1);border-left:5px solid #FB923C}
.theme-twilight-dusk .correlation-block,.theme-twilight-dusk .correlation-section,.theme-twilight-dusk .correlation-info{background:rgba(240,171,252,0.1);border-left:5px solid #E879F9}
.theme-twilight-dusk .extra-info,.theme-twilight-dusk .comments-block{background:rgba(187,247,208,0.1);border-left:5px solid #86EFAC}
/* =================================================================== */
/* ==================== 🪐 FAMILY: DARK THEMES ======================= */
/* =================================================================== */
/* 5.1: dark-saturn (Original Dark) */
body.theme-dark-saturn{background:linear-gradient(-225deg,#201c27 0%,#000000 100%)}
.theme-dark-saturn .card-container,.theme-dark-saturn .cloze-container,.theme-dark-saturn .mcq-container,.theme-dark-saturn .image-container{background:rgba(17,24,39,0.7);backdrop-filter:blur(16px);color:#F3F4F6;border:1px solid #4B5563}
.theme-dark-saturn .meta-header,.theme-dark-saturn .header,.theme-dark-saturn .cloze-header,.theme-dark-saturn .mcq-header,.theme-dark-saturn .image-header{background:linear-gradient(135deg,#F43F5E 0%,#A21CAF 100%)}
.theme-dark-saturn .card-type,.theme-dark-saturn .cloze-title,.theme-dark-saturn .mcq-title,.theme-dark-saturn .image-title,.theme-dark-saturn .header-text{color:#FFF1F2!important}
.theme-dark-saturn .question-text,.theme-dark-saturn .question-section{color:#F9A8D4!important}
.theme-dark-saturn .answer-text,.theme-dark-saturn .cloze-content{color:#F0ABFC!important}
.theme-dark-saturn .cloze{background:linear-gradient(135deg,#EC4899,#D946EF)!important;color:#FDF2F8}
.theme-dark-saturn .explanation-block,.theme-dark-saturn .explanation-section,.theme-dark-saturn .explanation-info{background:rgba(240,171,252,0.1);border-left:5px solid #E879F9}
.theme-dark-saturn .correlation-block,.theme-dark-saturn .correlation-section,.theme-dark-saturn .correlation-info{background:rgba(249,168,212,0.1);border-left:5px solid #F472B6}
.theme-dark-saturn .extra-info,.theme-dark-saturn .comments-block{background:rgba(165,243,252,0.1);border-left:5px solid #67E8F9}
/* 5.2: dark-mars-rover (Rusty Reds on Black) */
body.theme-dark-mars-rover{background:#000}
.theme-dark-mars-rover .card-container,.theme-dark-mars-rover .cloze-container,.theme-dark-mars-rover .mcq-container,.theme-dark-mars-rover .image-container{background:rgba(10,5,5,0.8);backdrop-filter:blur(10px);color:#FFDBCB;border:1px solid #B91C1C}
.theme-dark-mars-rover .meta-header,.theme-dark-mars-rover .header,.theme-dark-mars-rover .cloze-header,.theme-dark-mars-rover .mcq-header,.theme-dark-mars-rover .image-header{background:linear-gradient(135deg,#991B1B 0%,#B91C1C 100%)}
.theme-dark-mars-rover .card-type,.theme-dark-mars-rover .cloze-title,.theme-dark-mars-rover .mcq-title,.theme-dark-mars-rover .image-title,.theme-dark-mars-rover .header-text{color:#FEF2F2!important}
.theme-dark-mars-rover .question-text,.theme-dark-mars-rover .question-section{color:#FCA5A5!important}
.theme-dark-mars-rover .answer-text,.theme-dark-mars-rover .cloze-content{color:#FED7AA!important}
.theme-dark-mars-rover .cloze{background:linear-gradient(135deg,#B45309,#D97706)!important;color:#FFF7ED}
.theme-dark-mars-rover .explanation-block,.theme-dark-mars-rover .explanation-section,.theme-dark-mars-rover .explanation-info{background:rgba(254,215,170,0.1);border-left:5px solid #FDBA74}
.theme-dark-mars-rover .correlation-block,.theme-dark-mars-rover .correlation-section,.theme-dark-mars-rover .correlation-info{background:rgba(252,165,165,0.1);border-left:5px solid #FCA5A5}
.theme-dark-mars-rover .extra-info,.theme-dark-mars-rover .comments-block{background:rgba(217,217,217,0.1);border-left:5px solid #A8A29E}
/* 5.3: dark-neptune-deep (Deep Blues on Black) */
body.theme-dark-neptune-deep{background:#000}
.theme-dark-neptune-deep .card-container,.theme-dark-neptune-deep .cloze-container,.theme-dark-neptune-deep .mcq-container,.theme-dark-neptune-deep .image-container{background:rgba(5,10,20,0.8);backdrop-filter:blur(10px);color:#DBEAFE;border:1px solid #1D4ED8}
.theme-dark-neptune-deep .meta-header,.theme-dark-neptune-deep .header,.theme-dark-neptune-deep .cloze-header,.theme-dark-neptune-deep .mcq-header,.theme-dark-neptune-deep .image-header{background:linear-gradient(135deg,#1E40AF 0%,#2563EB 100%)}
.theme-dark-neptune-deep .card-type,.theme-dark-neptune-deep .cloze-title,.theme-dark-neptune-deep .mcq-title,.theme-dark-neptune-deep .image-title,.theme-dark-neptune-deep .header-text{color:#EFF6FF!important}
.theme-dark-neptune-deep .question-text,.theme-dark-neptune-deep .question-section{color:#93C5FD!important}
.theme-dark-neptune-deep .answer-text,.theme-dark-neptune-deep .cloze-content{color:#A5F3FC!important}
.theme-dark-neptune-deep .cloze{background:linear-gradient(135deg,#0C4A6E,#0369A1)!important;color:#E0F2FE}
.theme-dark-neptune-deep .explanation-block,.theme-dark-neptune-deep .explanation-section,.theme-dark-neptune-deep .explanation-info{background:rgba(165,243,252,0.1);border-left:5px solid #22D3EE}
.theme-dark-neptune-deep .correlation-block,.theme-dark-neptune-deep .correlation-section,.theme-dark-neptune-deep .correlation-info{background:rgba(147,197,253,0.1);border-left:5px solid #93C5FD}
.theme-dark-neptune-deep .extra-info,.theme-dark-neptune-deep .comments-block{background:rgba(199,210,254,0.1);border-left:5px solid #C7D2FE}
/* 5.4: dark-black-hole (Monochrome) */
body.theme-dark-black-hole{background:#000}
.theme-dark-black-hole .card-container,.theme-dark-black-hole .cloze-container,.theme-dark-black-hole .mcq-container,.theme-dark-black-hole .image-container{background:rgba(10,10,10,0.8);backdrop-filter:blur(10px);color:#D4D4D4;border:1px solid #404040}
.theme-dark-black-hole .meta-header,.theme-dark-black-hole .header,.theme-dark-black-hole .cloze-header,.theme-dark-black-hole .mcq-header,.theme-dark-black-hole .image-header{background:#262626}
.theme-dark-black-hole .card-type,.theme-dark-black-hole .cloze-title,.theme-dark-black-hole .mcq-title,.theme-dark-black-hole .image-title,.theme-dark-black-hole .header-text{color:#FAFAFA!important}
.theme-dark-black-hole .question-text,.theme-dark-black-hole .question-section{color:#A3A3A3!important}
.theme-dark-black-hole .answer-text,.theme-dark-black-hole .cloze-content{color:#E5E5E5!important}
.theme-dark-black-hole .cloze{background:#737373!important;color:#171717}
.theme-dark-black-hole .explanation-block,.theme-dark-black-hole .explanation-section,.theme-dark-black-hole .explanation-info{background:#171717;border-left:5px solid #525252}
.theme-dark-black-hole .correlation-block,.theme-dark-black-hole .correlation-section,.theme-dark-black-hole .correlation-info{background:#171717;border-left:5px solid #A3A3A3}
.theme-dark-black-hole .extra-info,.theme-dark-black-hole .comments-block{background:#171717;border-left:5px solid #737373}
/* 5.5: dark-starless-sky (Pure Black/OLED) */
body.theme-dark-starless-sky{background:#000}
.theme-dark-starless-sky .card-container,.theme-dark-starless-sky .cloze-container,.theme-dark-starless-sky .mcq-container,.theme-dark-starless-sky .image-container{background:#000;backdrop-filter:none;color:#A1A1AA;border:1px solid #2727A}
.theme-dark-starless-sky .meta-header,.theme-dark-starless-sky .header,.theme-dark-starless-sky .cloze-header,.theme-dark-starless-sky .mcq-header,.theme-dark-starless-sky .image-header{background:#18181B}
.theme-dark-starless-sky .card-type,.theme-dark-starless-sky .cloze-title,.theme-dark-starless-sky .mcq-title,.theme-dark-starless-sky .image-title,.theme-dark-starless-sky .header-text{color:#E4E4E7!important}
.theme-dark-starless-sky .question-text,.theme-dark-starless-sky .question-section{color:#4ADE80!important}
.theme-dark-starless-sky .answer-text,.theme-dark-starless-sky .cloze-content{color:#38BDF8!important}
.theme-dark-starless-sky .cloze{background:linear-gradient(135deg,#22C55E,#4ADE80)!important;color:#052E16}
.theme-dark-starless-sky .explanation-block,.theme-dark-starless-sky .explanation-section,.theme-dark-starless-sky .explanation-info{background:#09090B;border-left:5px solid #38BDF8}
.theme-dark-starless-sky .correlation-block,.theme-dark-starless-sky .correlation-section,.theme-dark-starless-sky .correlation-info{background:#09090B;border-left:5px solid #4ADE80}
.theme-dark-starless-sky .extra-info,.theme-dark-starless-sky .comments-block{background:#09090B;border-left:5px solid #A855F7}
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
    
    if is_dark != mw.pm.night_mode():
        mw.pm.toggle_night_mode()
        
    if mw.state == "review":
        mw.reviewer.refresh()
    
    mw.tooltip(f"Theme set to {theme_name.replace('-', ' ').title()}")

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
    
    # Gracefully remove the old menu if the add-on is reloaded
    # FIX: Use mw.toolbar instead of mw.form.mainToolBar for modern Anki versions
    for action in mw.toolbar.actions():
        if action.objectName() == action_name:
            mw.toolbar.removeAction(action)
            break

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
    
    # FIX: Use mw.toolbar instead of mw.form.mainToolBar for modern Anki versions
    mw.toolbar.addAction(main_toolbar_action)

# ==============================================================================
# ==========================  STEP 5: INITIALIZATION ===========================
# ==============================================================================
gui_hooks.main_window_did_init.append(setup_theme_menu)

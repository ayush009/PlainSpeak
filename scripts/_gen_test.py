# -*- coding: utf-8 -*-
"""Generate a polished PDF from PlainSpeak-Technical-Documentation.md"""
from __future__ import annotations
from pathlib import Path
import re

MD  = Path(__file__).resolve().parent.parent / "PlainSpeak-Technical-Documentation.md"
OUT = Path(__file__).resolve().parent.parent / "PlainSpeak-Technical-Documentation.pdf"

_SUBS = [
    ("—", " - "), ("–", "-"),
    ("‘", "'"), ("’", "'"),
    ("“", """), ("”", """),
    ("°", " deg"),
    ("ä", "a"), ("ö", "o"), ("ü", "u"),
    ("é", "e"), ("è", "e"), ("ê", "e"),
    ("à", "a"), ("â", "a"),
    ("→", "->"), ("←", "<-"), ("↔", "<->"),
    ("↓", "v"), ("↑", "^"),
    ("▼", "v"), ("►", ">"), ("◄", "<"),
    ("├", "|--"), ("└", "`--"),
    ("┐", "|"), ("┘", "|"),
    ("─", "-"), ("│", "|"),
    ("·", "."), ("█", "#"),
]

def _s(t):
    for a, b in _SUBS:
        t = t.replace(a, b)
    return t

def _strip_md(txt):
    txt = re.sub(r"`(.+?)`", r"", txt)
    txt = re.sub(r"\*\*(.+?)\*\*", r"", txt)
    txt = re.sub(r"\*(.+?)\*", r"", txt)
    return txt


# -*- coding: utf-8 -*-
"""Generate a polished PDF from PlainSpeak-Technical-Documentation.md"""
from __future__ import annotations
from pathlib import Path
import re

MD  = Path(__file__).resolve().parent.parent / "PlainSpeak-Technical-Documentation.md"
OUT = Path(__file__).resolve().parent.parent / "PlainSpeak-Tech-Doc-v3.pdf"

# \uXXXX escapes keep source ASCII-safe
_SUBS = [
    ("—", " - "), ("–", "-"),
    ("‘", "'"),   ("’", "'"),
    ("“", '"'),   ("”", '"'),
    ("°", " deg"),
    ("ä", "a"),   ("ö", "o"),   ("ü", "u"),
    ("é", "e"),   ("è", "e"),   ("ê", "e"),
    ("à", "a"),   ("â", "a"),
    ("→", "->"),  ("←", "<-"),  ("↔", "<->"),
    ("↓", "v"),   ("↑", "^"),
    ("▼", "v"),   ("►", ">"),   ("◄", "<"),
    ("├", "|--"), ("└", "`--"),
    ("┐", "|"),   ("┘", "|"),
    ("─", "-"),   ("│", "|"),
    ("·", "."),   ("█", "#"),
]


def _s(t: str) -> str:
    for a, b in _SUBS:
        t = t.replace(a, b)
    return t


def _md(txt: str) -> str:
    txt = re.sub(r"`(.+?)`", r"\1", txt)
    txt = re.sub(r"\*\*(.+?)\*\*", r"\1", txt)
    txt = re.sub(r"\*(.+?)\*", r"\1", txt)
    return txt


def make() -> None:
    try:
        from fpdf import FPDF
    except ModuleNotFoundError:
        print("fpdf2 not installed.  Run: uv sync")
        return

    # ── palette ──────────────────────────────────────────────────────────────
    NAVY    = (18,  50,  79)
    VIOLET  = (75,  85, 175)
    MINT    = (16, 148, 140)
    GREY    = (88, 102, 116)
    LGREY   = (155, 165, 178)
    BLACK   = (22,  26,  32)
    WHITE   = (255, 255, 255)
    CODBG   = (240, 243, 248)
    CODTXT  = (40,  50, 120)
    TBLHDR  = (220, 230, 242)
    TBLALT  = (246, 249, 253)
    CALLBG  = (235, 245, 253)

    # ── doc class ─────────────────────────────────────────────────────────────
    class Doc(FPDF):
        def header(self):
            if self.page_no() == 1:
                return
            self.set_fill_color(*NAVY)
            self.rect(0, 0, self.w, 12, style="F")
            self.set_y(2.5)
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*WHITE)
            self.cell(0, 6, "  PlainSpeak  -  Technical Documentation",
                      align="L", new_x="LMARGIN", new_y="TOP")
            self.cell(0, 6, f"Page {self.page_no()}  ",
                      align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(*BLACK)

        def footer(self):
            self.set_y(-12)
            self.set_draw_color(*LGREY)
            self.set_line_width(0.2)
            self.line(self.l_margin, self.get_y(),
                      self.w - self.r_margin, self.get_y())
            self.ln(1.5)
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(*LGREY)
            self.cell(0, 5,
                f"PlainSpeak MVP  |  Synthetic-data demo  "
                f"|  Page {self.page_no()} of {{nb}}",
                align="C")
            self.set_text_color(*BLACK)

    pdf = Doc()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(True, 18)
    pdf.set_margins(20, 18, 20)
    CW = pdf.w - pdf.l_margin - pdf.r_margin   # ~170 mm

    # ── render helpers ────────────────────────────────────────────────────────

    def h1(txt: str) -> None:
        y = pdf.get_y()
        pdf.set_fill_color(*NAVY)
        pdf.rect(pdf.l_margin, y, CW, 12, style="F")
        # violet accent strip at left
        pdf.set_fill_color(*VIOLET)
        pdf.rect(pdf.l_margin, y, 4, 12, style="F")
        pdf.set_xy(pdf.l_margin + 8, y + 2)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*WHITE)
        pdf.multi_cell(CW - 8, 8, _s(txt), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*BLACK)
        pdf.ln(3)

    def h2(txt: str) -> None:
        pdf.ln(4)
        y = pdf.get_y()
        pdf.set_fill_color(*VIOLET)
        pdf.rect(pdf.l_margin, y, 3.5, 7.5, style="F")
        pdf.set_xy(pdf.l_margin + 7, y + 0.5)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*NAVY)
        pdf.multi_cell(CW - 7, 6.5, _s(txt), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*BLACK)
        pdf.ln(1.5)

    def h3(txt: str) -> None:
        pdf.ln(2.5)
        y = pdf.get_y()
        pdf.set_fill_color(*MINT)
        pdf.rect(pdf.l_margin, y, 2.5, 6.5, style="F")
        pdf.set_xy(pdf.l_margin + 6, y)
        pdf.set_font("Helvetica", "BI", 9.5)
        pdf.set_text_color(*GREY)
        pdf.multi_cell(CW - 6, 6.5, _s(txt), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*BLACK)
        pdf.ln(1)

    def body(txt: str, size: float = 9.5) -> None:
        if not txt.strip():
            return
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", size)
        pdf.set_text_color(*BLACK)
        pdf.multi_cell(CW, 5.3, _s(txt), new_x="LMARGIN", new_y="NEXT")

    def bullet(txt: str) -> None:
        if not txt.strip():
            return
        pdf.set_x(pdf.l_margin + 5)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*VIOLET)
        pdf.cell(4, 5.3, "-", new_x="RIGHT", new_y="TOP")
        pdf.set_x(pdf.l_margin + 10)
        pdf.set_text_color(*BLACK)
        pdf.multi_cell(CW - 10, 5.3, _s(txt), new_x="LMARGIN", new_y="NEXT")

    def code_block(block_lines: list[str]) -> None:
        """
        Render a fenced code block.
        Uses multi_cell with fill=True so page-breaks work correctly —
        no measure-then-redraw, no giant empty boxes.
        """
        if not block_lines:
            return
        txt = "\n".join(_s(ln) for ln in block_lines)
        if not txt.strip():
            return
        pdf.ln(1.5)
        # Left violet accent bar (3 mm) + grey code area
        x0 = pdf.l_margin
        # We render the code in a column starting at x0+3, width CW-3
        # The grey background is achieved with fill=True on multi_cell.
        # The violet stripe is a thin rect whose height we read AFTER rendering.
        y_before = pdf.get_y()
        pdf.set_x(x0 + 5)
        pdf.set_fill_color(*CODBG)
        pdf.set_draw_color(200, 208, 220)
        pdf.set_line_width(0.15)
        pdf.set_font("Courier", "", 7.8)
        pdf.set_text_color(*CODTXT)
        # render with fill — handles page breaks natively
        pdf.multi_cell(CW - 5, 4.8, txt,
                       border=0, fill=True,
                       new_x="LMARGIN", new_y="NEXT")
        y_after = pdf.get_y()
        # Only draw violet stripe if all content stayed on the same page.
        # (If a page break happened, y_after < y_before due to new page.)
        if y_after > y_before:
            h = y_after - y_before
            pdf.set_fill_color(*VIOLET)
            pdf.rect(x0, y_before, 3, h, style="F")
            # thin right border
            pdf.set_draw_color(200, 208, 220)
            pdf.set_line_width(0.15)
            pdf.rect(x0 + 3, y_before, CW - 3, h, style="D")
        pdf.set_text_color(*BLACK)
        pdf.ln(2)

    def table(headers: list[str], rows: list[list[str]]) -> None:
        if not headers:
            return
        n = len(headers)
        if n == 2:
            col_ws = [CW * 0.30, CW * 0.70]
        elif n == 3:
            col_ws = [CW * 0.22, CW * 0.42, CW * 0.36]
        elif n == 4:
            col_ws = [CW * 0.18, CW * 0.20, CW * 0.34, CW * 0.28]
        else:
            col_ws = [CW / n] * n

        pdf.ln(1)
        # header
        pdf.set_x(pdf.l_margin)
        pdf.set_fill_color(*TBLHDR)
        pdf.set_draw_color(*LGREY)
        pdf.set_line_width(0.15)
        for hdr, cw in zip(headers, col_ws):
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*NAVY)
            pdf.cell(cw, 7, "  " + _s(hdr), border=1, fill=True,
                     new_x="RIGHT", new_y="TOP")
        pdf.ln()
        # rows
        for ri, row in enumerate(rows):
            pdf.set_x(pdf.l_margin)
            alt = ri % 2 == 1
            if alt:
                pdf.set_fill_color(*TBLALT)
            for ci, (cell, cw) in enumerate(zip(row, col_ws)):
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*BLACK)
                pdf.cell(cw, 5.8, "  " + _s(str(cell)), border=1,
                         fill=alt, new_x="RIGHT", new_y="TOP")
            pdf.ln()
        pdf.ln(2)

    # ── cover page ───────────────────────────────────────────────────────────
    pdf.add_page()

    # Navy band
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, pdf.w, 75, style="F")
    # Violet accent
    pdf.set_fill_color(*VIOLET)
    pdf.rect(0, 73, pdf.w, 6, style="F")
    # Mint thin line
    pdf.set_fill_color(*MINT)
    pdf.rect(0, 77, pdf.w, 1.5, style="F")

    # Title
    pdf.set_xy(pdf.l_margin, 16)
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 20, "PlainSpeak", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(pdf.l_margin, pdf.get_y())
    pdf.set_font("Helvetica", "", 15)
    pdf.set_text_color(170, 190, 225)
    pdf.cell(0, 11, "Technical Documentation", new_x="LMARGIN", new_y="NEXT")

    # Meta rows
    pdf.set_xy(pdf.l_margin, 85)
    for label, value in [
        ("VERSION", "MVP  -  latest commit 7d508f8"),
        ("STACK",   "Python 3.12  FastAPI  Anthropic Claude  Reson8  pypdf  uv"),
        ("NOTE",    "Synthetic-data demo only  |  all patient data is fictional"),
    ]:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*GREY)
        pdf.cell(28, 6, label, new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*BLACK)
        pdf.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(pdf.l_margin)

    pdf.ln(7)
    pdf.set_draw_color(*LGREY)
    pdf.set_line_width(0.2)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, "SECTIONS IN THIS DOCUMENT", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    toc = [
        ("1",  "System Architecture"),
        ("2",  "Data Model"),
        ("3",  "Storage Layer"),
        ("4",  "HTTP API"),
        ("5",  "PDF Extraction"),
        ("6",  "Transcript Import"),
        ("7",  "AI Subsystem"),
        ("8",  "Voice / Speech"),
        ("9",  "Frontend Architecture"),
        ("10", "Workflow State Machine"),
        ("11", "Demo Fixtures"),
        ("12", "Configuration"),
        ("13", "Testing"),
        ("14", "Security Notes"),
    ]
    col_w = CW / 2
    y_toc = pdf.get_y()
    for ci, col_items in enumerate([toc[:7], toc[7:]]):
        pdf.set_xy(pdf.l_margin + ci * col_w, y_toc)
        for num, title in col_items:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*VIOLET)
            pdf.cell(12, 6.5, num + ".", new_x="RIGHT", new_y="TOP")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*BLACK)
            pdf.cell(col_w - 14, 6.5, title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_x(pdf.l_margin + ci * col_w)

    # ── parse and render markdown ─────────────────────────────────────────────
    text = MD.read_text(encoding="utf-8")
    md_lines = text.splitlines()
    i = 0
    last_blank = False

    while i < len(md_lines):
        line = md_lines[i]

        if line.strip() == "---":
            i += 1
            continue

        # doc title line
        if re.match(r"^# [^#]", line):
            i += 1
            continue

        # front-matter bold lines (**Version:** ...)
        if re.match(r"^\*\*", line) and i < 5:
            i += 1
            continue

        # H2 -> new page
        if re.match(r"^## ", line):
            sec = line[3:].strip()
            pdf.add_page()
            pdf.start_section(sec)
            h1(sec)
            last_blank = False
            i += 1
            continue

        # H3
        if re.match(r"^### ", line):
            h2(line[4:].strip())
            last_blank = False
            i += 1
            continue

        # H4
        if re.match(r"^#### ", line):
            h3(line[5:].strip())
            last_blank = False
            i += 1
            continue

        # fenced code block
        if line.strip().startswith("```"):
            i += 1
            block: list[str] = []
            while i < len(md_lines) and not md_lines[i].strip().startswith("```"):
                block.append(md_lines[i])
                i += 1
            i += 1
            if block:
                code_block(block)
            last_blank = False
            continue

        # table
        if line.startswith("|"):
            tbl: list[str] = []
            while i < len(md_lines) and md_lines[i].startswith("|"):
                tbl.append(md_lines[i])
                i += 1
            rows_raw = [
                [c.strip() for c in ln.strip().strip("|").split("|")]
                for ln in tbl
                if not re.match(r"^\|[-| :]+\|$", ln.strip())
            ]
            if rows_raw:
                table(rows_raw[0], rows_raw[1:])
            last_blank = False
            continue

        # blank line — collapse multiples into one small gap
        if not line.strip():
            if not last_blank:
                pdf.ln(2)
            last_blank = True
            i += 1
            continue

        last_blank = False

        # bullet
        if re.match(r"^[-*] ", line):
            txt = _md(line[2:].strip())
            i += 1
            while i < len(md_lines) and re.match(r"^  ", md_lines[i]):
                txt += " " + _md(md_lines[i].strip())
                i += 1
            bullet(txt)
            continue

        # plain paragraph
        para: list[str] = []
        while i < len(md_lines):
            ln = md_lines[i]
            if (not ln.strip()
                    or ln.startswith("#")
                    or ln.startswith("|")
                    or ln.strip().startswith("```")
                    or ln.strip() == "---"
                    or re.match(r"^[-*] ", ln)):
                break
            para.append(_md(ln))
            i += 1
        if para:
            body(" ".join(para))
        continue

    # ── output ────────────────────────────────────────────────────────────────
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    print(f"Written -> {OUT}  ({OUT.stat().st_size:,} bytes, {pdf.page_no()} pages)")


if __name__ == "__main__":
    make()

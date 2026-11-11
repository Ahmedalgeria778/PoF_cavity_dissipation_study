# -*- coding: utf-8 -*-
r"""Write the Word version of the supplementary material.

AIP needs a Word file of the supplement next to its .tex source. This turns
supplementary/supplementary_final.tex, with the appendix tables it pulls through
\input, into supplementary/supplementary_final.docx: headings, paragraphs, lists,
tables, figures, captions, cross-references and the bibliography come from the same
source pdflatex reads, display equations are set with the Computer Modern mathtext
fonts, and every label number is cross-checked against the .aux of that build. The
script fails rather than writing a silently lossy document: unmapped control
sequences, label numbers that disagree with the .aux and prose tokens that do not
reach the .docx are all fatal.

Usage: py scripts/make_supplementary_docx.py
"""
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
SUP = os.path.join(REPO, "supplementary")
TEX = os.path.join(SUP, "supplementary_final.tex")
AUX = os.path.join(REPO, "build", "supplementary_final.aux")
MEDIA = os.path.join(REPO, "build", "docx_media")
OUT = os.path.join(SUP, "supplementary_final.docx")

TEXT_WIDTH_IN = 6.5
EQ_DPI = 300
EQ_PTS = 11.5
FIG_DPI = 220

UNMAPPED = set()
NOTES = []

# --------------------------------------------------------------------------- latex

SYMBOLS = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ϵ",
    "varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ",
    "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
    "pi": "π", "rho": "ρ", "varrho": "ϱ", "sigma": "σ", "tau": "τ",
    "upsilon": "υ", "phi": "φ", "varphi": "φ", "chi": "χ", "psi": "ψ",
    "omega": "ω", "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ",
    "Xi": "Ξ", "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ",
    "Psi": "Ψ", "Omega": "Ω",
    "times": "×", "cdot": "·", "div": "÷", "pm": "±", "mp": "∓", "ast": "∗",
    "star": "⋆", "circ": "∘", "bullet": "∙", "otimes": "⊗", "oplus": "⊕",
    "ominus": "⊖", "dagger": "†", "ddagger": "‡", "nabla": "∇",
    "partial": "∂", "infty": "∞", "ell": "ℓ", "hbar": "ℏ", "surd": "√",
    "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "ne": "≠", "neq": "≠",
    "ll": "≪", "gg": "≫", "approx": "≈", "asymp": "≍", "equiv": "≡",
    "sim": "∼", "simeq": "≃", "propto": "∝", "perp": "⊥", "parallel": "∥",
    "subset": "⊂", "supset": "⊃", "subseteq": "⊆", "supseteq": "⊇",
    "in": "∈", "notin": "∉", "ni": "∋", "cup": "∪", "cap": "∩",
    "setminus": "∖", "emptyset": "∅", "varnothing": "∅", "forall": "∀",
    "exists": "∃", "neg": "¬", "lnot": "¬", "land": "∧", "wedge": "∧",
    "lor": "∨", "vee": "∨", "Rightarrow": "⇒", "Leftarrow": "⇐",
    "leftrightarrow": "↔", "Leftrightarrow": "⇔", "rightarrow": "→",
    "to": "→", "leftarrow": "←", "mapsto": "↦", "implies": "⟹",
    "sum": "∑", "prod": "∏", "int": "∫", "iint": "∬", "oint": "∮",
    "bigcup": "⋃", "bigcap": "⋂", "coprod": "∐",
    "langle": "⟨", "rangle": "⟩", "lfloor": "⌊", "rfloor": "⌋",
    "vert": "|", "lvert": "|", "rvert": "|",
    "lVert": "‖", "rVert": "‖", "Vert": "‖", "mid": "∣",
    "dots": "…", "ldots": "…", "cdots": "⋯", "vdots": "⋮", "ddots": "⋱",
    "backslash": "\\", "degree": "°", "checkmark": "✓",
    "P": "ℙ", "R": "ℝ", "Q": "ℚ", "Z": "ℤ", "N": "ℕ", "C": "ℂ",
}
for _k in ("mathbb",):
    pass

SCRIPT = {}
for _i, _c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    SCRIPT[_c] = chr(0x1D49C + _i) if _i not in (1, 4, 5, 7, 8, 11, 12, 17, 20) else {
        1: "ℬ", 4: "ℰ", 5: "ℱ", 7: "ℋ", 8: "ℐ", 11: "ℒ", 12: "ℳ",
        17: "ℛ", 20: "𝒮"}[_i]

FUNCNAMES = {"log", "ln", "exp", "max", "min", "sin", "cos", "tan", "tanh",
             "cosh", "sinh", "arctan", "arg", "det", "dim", "gcd", "ker", "lim",
             "sup", "inf", "var", "mod", "Pr", "sgn", "Tr", "deg"}

ACCENT = {"overline": "̄", "bar": "̄", "widetilde": "̃", "tilde": "̃",
          "widehat": "̂", "hat": "̂", "vec": "⃗", "dot": "̇", "check": "̌",
          "breve": "̆"}

SPACES = {",": " ", ";": " ", ":": " ", "!": "", " ": " ", "quad": "  ",
          "qquad": "    "}

STYLE = {"textbf": "b", "bfseries": "b", "emph": "i", "textit": "i",
         "textsf": "s", "textsc": "sc", "underline": "u"}

INLINE_OUTFIT = {"mathrm", "textrm", "text", "textnormal", "operatorname",
                 "mathup", "mbox"}


def read_group(src, i):
    """src[i] is '{'; return (content, index after the closing brace)."""
    depth = 0
    j = i
    while j < len(src):
        c = src[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[i + 1:j], j + 1
        j += 1
    UNMAPPED.add("<unbalanced brace>")
    return src[i + 1:], len(src)


def read_arg(src, i):
    """Read one LaTeX argument: a braced group, a control sequence, or a single char.

    Math macros accept \\bar q and \\tfrac12 as well as \\bar{q}, so the argument
    has to be read in all three shapes or the command falls through as unmapped.
    """
    n = len(src)
    while i < n and src[i] in " \t":
        i += 1
    if i >= n:
        return "", i
    if src[i] == "{":
        return read_group(src, i)
    m = CTRL.match(src, i)
    if m:
        j = m.end()
        if j < n and src[j] == "{":
            g, j2 = read_group(src, j)
            return "\\" + m.group(1) + "{" + g + "}", j2
        return "\\" + m.group(1), j
    return src[i], i + 1


def split_top(src, seps):
    """Split on the given separators, ignoring those inside braces or math."""
    out, buf, i, depth, math = [], [], 0, 0, 0
    n = len(src)
    while i < n:
        c = src[i]
        if depth == 0 and math == 0:
            hit = None
            for s in seps:
                if src.startswith(s, i):
                    hit = s
                    break
            if hit:
                out.append("".join(buf))
                buf = []
                i += len(hit)
                continue
        if c == "\\" and i + 1 < n:
            two = src[i:i + 2]
            if two == "\\(":
                math += 1
            elif two == "\\)":
                math -= 1
            buf.append(two)
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "$":
            math += 1 if math == 0 else -1
        buf.append(c)
        i += 1
    out.append("".join(buf))
    return out


CTRL = re.compile(r"\\([a-zA-Z]+)(\*?)\s*")
ESC = re.compile(r"\\([^a-zA-Z])")


def strip_comments(text):
    out = []
    for line in text.split("\n"):
        k, cut = 0, None
        while True:
            k = line.find("%", k)
            if k < 0:
                break
            nbs, p = 0, k - 1
            while p >= 0 and line[p] == "\\":
                nbs += 1
                p -= 1
            if nbs % 2 == 0:
                cut = k
                break
            k += 1
        if cut is None:
            out.append(line)
        elif line[:cut].strip() == "":
            out.append("")
        else:
            out.append(line[:cut])
            out[-1] = line[:cut] + "\0"
    txt = "".join(l + "\n" for l in out)
    return txt.replace("\0\n", "").replace("\0", "")


# --------------------------------------------------------------------- text tokens

def tok(src, fmt=None, math=0):
    """LaTeX source fragment -> list of (text, flags) runs. math: 0 text, 1 inline."""
    fmt = fmt or {}
    out = []
    buf = []
    i, n = 0, len(src)

    def emit(t, **kw):
        """Append a run, putting any buffered prose in front of it first.

        Commands emit as soon as they are read, while ordinary characters wait in
        buf; without this flush here the styled run would land before the text
        that precedes it in the source.
        """
        if buf:
            out.append(("".join(buf), dict(fmt)))
            del buf[:]
        if not t:
            return
        f = dict(fmt)
        f.update(kw)
        out.append((t, f))

    def flush():
        if buf:
            out.append(("".join(buf), dict(fmt)))
            del buf[:]

    def sub(s2, f2, m2):
        for t, ff in tok(s2, f2, m2):
            emit(t, **ff)

    while i < n:
        c = src[i]
        if c == "\\":
            m = CTRL.match(src, i)
            if m:
                name, star = m.group(1), m.group(2)
                j = m.end()
                if name == "(":
                    k = src.find("\\)", j)
                    k = n if k < 0 else k
                    sub(src[j:k], fmt, 1)
                    i = k + 2
                    continue
                if name == ")":
                    i = j
                    continue
                if name in STYLE:
                    if j < n and src[j] == "{":
                        g, j2 = read_group(src, j)
                        sub(g, dict(fmt, **{STYLE[name]: True}), math)
                        i = j2
                        continue
                    emit("")
                    i = j
                    continue
                if name in ("textnormal", "mbox", "textsf"):
                    if j < n and src[j] == "{":
                        g, j2 = read_group(src, j)
                        sub(g, fmt, math)
                        i = j2
                        continue
                if name == "texttt":
                    if j < n and src[j] == "{":
                        g, j2 = read_group(src, j)
                        sub(g, dict(fmt, m=True), math)
                        i = j2
                        continue
                if name in ("textsuperscript",):
                    if j < n and src[j] == "{":
                        g, j2 = read_group(src, j)
                        sub(g, dict(fmt, sup=True), math)
                        i = j2
                        continue
                if name in ("textsubscript",):
                    if j < n and src[j] == "{":
                        g, j2 = read_group(src, j)
                        sub(g, dict(fmt, sub=True), math)
                        i = j2
                        continue
                if name == "url":
                    if j < n and src[j] == "{":
                        g, j2 = read_group(src, j)
                        emit(g.strip(), link=g.strip())
                        i = j2
                        continue
                if name == "href":
                    if j < n and src[j] == "{":
                        u, j2 = read_group(src, j)
                        if j2 < n and src[j2] == "{":
                            g, j3 = read_group(src, j2)
                        else:
                            g, j3 = u, j2
                        emit(g.strip(), link=u.strip())
                        i = j3
                        continue
                if name in ("ref", "eqref", "pageref", "autoref"):
                    if j < n and src[j] == "{":
                        g, j2 = read_group(src, j)
                        lbl = g.strip()
                        num = LABELS.get(lbl, "?")
                        emit("(%s)" % num if name == "eqref" else num)
                        NOTES.append("ref %s -> %s" % (lbl, num))
                        i = j2
                        continue
                if name in ("cite", "citep", "citet"):
                    if j < n and src[j] == "{":
                        g, j2 = read_group(src, j)
                        keys = [k.strip() for k in g.split(",") if k.strip()]
                        emit("[" + ",".join(str(BIB.get(k, "?")) for k in keys) + "]")
                        i = j2
                        continue
                if name == "label":
                    if j < n and src[j] == "{":
                        _, j = read_group(src, j)
                    i = j
                    continue
                if name in ("input",):
                    if j < n and src[j] == "{":
                        _, j = read_group(src, j)
                    i = j
                    continue
                if name in SPACES and math:
                    emit(SPACES[name])
                    i = j
                    continue
                if name in ("hspace", "vspace", "setlength", "addtolength",
                            "includegraphics", "centering", "raggedright",
                            "raggedbottom", "small", "footnotesize", "scriptsize",
                            "normalsize", "large", "Large", "noindent", "newline",
                            "newpage", "clearpage", "pagebreak", "emergencystretch",
                            "maketitle", "tableofcontents", "item", "hfill",
                            "toprule", "midrule", "bottomrule", "hline", "cline",
                            "arraystretch", "tabcolsep", "parskip", "parindent",
                            "graphicspath", "sloppy", "protect", "phantom",
                            "ensuremath", "arraybackslash", "noalign",
                            "centering", "raggedright"):
                    if name in ("hspace", "vspace", "setlength", "addtolength",
                                "includegraphics", "newline", "hfill",
                                "emergencystretch", "item", "noalign"):
                        k = j
                        while k < n and src[k] in " \t*[":
                            k += 1
                        if k < n and src[k] == "{":
                            _, j = read_group(src, k)
                        elif name == "includegraphics":
                            while j < n and src[j] != "{":
                                j += 1
                            if j < n:
                                _, j = read_group(src, j)
                        i = j
                        continue
                    if name == "newline":
                        emit("\n")
                    i = j
                    continue
                if math and name in ACCENT:
                    g, j2 = read_arg(src, j)
                    runs = tok(g, fmt, 1)
                    text = "".join(t for t, _ in runs)
                    emit(text + "".join(ACCENT[name] for _ in text))
                    i = j2
                    continue
                if math and name in ("frac", "tfrac", "dfrac", "cfrac"):
                    a, j2 = read_arg(src, j)
                    b, j3 = read_arg(src, j2)
                    num, den = tok(a, fmt, 1), tok(b, fmt, 1)
                    sn = plain(num)
                    sd = plain(den)
                    lp = "(" if needs_group(sn) else ""
                    rp = ")" if needs_group(sn) else ""
                    lq = "(" if needs_group(sd) else ""
                    rq = ")" if needs_group(sd) else ""
                    emit(lp)
                    for t, ff in num:
                        emit(t, **ff)
                    emit(rp + "/" + lq)
                    for t, ff in den:
                        emit(t, **ff)
                    emit(rq)
                    i = j3
                    continue
                if math and name == "sqrt":
                    g, j2 = read_arg(src, j)
                    runs = tok(g, fmt, 1)
                    s = plain(runs)
                    emit("√" + ("(" + s + ")" if needs_group(s) else s))
                    i = j2
                    continue
                if math and name == "mathcal":
                    g, j2 = read_arg(src, j)
                    emit("".join(SCRIPT.get(ch, ch) for ch in g.strip()))
                    i = j2
                    continue
                if math and name == "mathbf":
                    g, j2 = read_arg(src, j)
                    sub(g, dict(fmt, b=True, up=True), 1)
                    i = j2
                    continue
                if math and name in INLINE_OUTFIT:
                    g, j2 = read_arg(src, j)
                    sub(g, dict(fmt, up=True), 1)
                    i = j2
                    continue
                if math and name in ("left", "right", "big", "Big", "bigg",
                                     "Bigg", "bigl", "bigr", "Bigl", "Bigr",
                                     "displaystyle", "textstyle", "limits",
                                     "nolimits"):
                    i = j
                    continue
                if name in ("begin", "end"):
                    emit("")
                    i = j
                    continue
                if name == "and":
                    emit(", ")
                    i = j
                    continue
                if name in SYMBOLS and (math or name in ("pm", "times", "infty")):
                    flush()
                    emit(SYMBOLS[name])
                    i = j
                    continue
                if name in FUNCNAMES and math:
                    flush()
                    emit(name, up=True)
                    i = j
                    continue
                if not math and name in ("LaTeX", "TeX", "ldots"):
                    flush()
                    emit({"LaTeX": "LaTeX", "TeX": "TeX", "ldots": "…"}[name])
                    i = j
                    continue
                UNMAPPED.add("\\" + name)
                i = j
                continue
            m = ESC.match(src, i)
            if m:
                ch = m.group(1)
                if ch == "(":
                    k = src.find("\\)", m.end())
                    k = n if k < 0 else k
                    sub(src[m.end():k], fmt, 1)
                    i = k + 2
                    continue
                if ch == ")":
                    i = m.end()
                    continue
                if ch == "\\":
                    emit("\n")
                    i = m.end()
                    continue
                if ch in ",;:! ":
                    emit(SPACES[ch] if math else (" " if ch != "!" else ""))
                    i = m.end()
                    continue
                emit(ch)
                i = m.end()
                continue
            UNMAPPED.add(src[i:i + 2])
            i += 1
            continue
        if c == "$":
            j = i + 1
            while j < n and not (src[j] == "$" and src[j - 1:j] != "\\"):
                j += 1
            sub(src[i + 1:j], fmt, 1)
            i = j + 1
            continue
        if c == "{":
            g, j = read_group(src, i)
            sub(g, fmt, math)
            i = j
            continue
        if c == "}":
            i += 1
            continue
        if c == "~":
            buf.append(" ")
            i += 1
            continue
        if src.startswith("``", i):
            buf.append("“")
            i += 2
            continue
        if src.startswith("''", i):
            buf.append("”")
            i += 2
            continue
        if src.startswith("---", i):
            buf.append("—")
            i += 3
            continue
        if src.startswith("--", i):
            buf.append("–")
            i += 2
            continue
        if c == "'":
            buf.append("’")
            i += 1
            continue
        if c == "\n":
            buf.append(" ")
            i += 1
            continue
        buf.append(c)
        i += 1
    flush()
    return collapse(out)


def plain(runs):
    return "".join(t for t, _ in runs)


def needs_group(s):
    return bool(re.search(r"[+=\s]", s)) or len(s) > 3


def collapse(runs):
    out = []
    for t, f in runs:
        if not t:
            continue
        if out and out[-1][1] == f:
            out[-1][0] += t
        else:
            out.append([t, f])
    return [(t, dict(f)) for t, f in out]


# ---------------------------------------------------------------------- rendering

import docx  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Inches, Mm, Pt, RGBColor  # noqa: E402

BLACK = RGBColor(0, 0, 0)
BLUE = RGBColor(0x0B, 0x39, 0x7A)
FONT = "Times New Roman"


def setup(doc):
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    pf = st.paragraph_format
    pf.space_after = Pt(6)
    pf.line_spacing = 1.15
    for name, size, bold, before, after in (
            ("Heading 1", 13, True, 14, 6),
            ("Heading 2", 11.5, True, 12, 4),
            ("Heading 3", 11, True, 10, 4)):
        s = doc.styles[name]
        s.font.name = FONT
        s.font.size = Pt(size)
        s.font.bold = bold
        s.font.color.rgb = BLACK
        s.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        s.paragraph_format.space_before = Pt(before)
        s.paragraph_format.space_after = Pt(after)
        s.paragraph_format.keep_with_next = True
    t = doc.styles["Title"]
    t.font.name = FONT
    t.font.size = Pt(15)
    t.font.bold = True
    t.font.color.rgb = BLACK
    t.paragraph_format.space_after = Pt(6)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    for a in ("left_margin", "right_margin"):
        setattr(sec, a, Mm(22))
    sec.top_margin = sec.bottom_margin = Mm(24)


def add_runs(p, runs, size=None):
    for t, f in runs:
        if f.get("link"):
            add_link(p, f["link"], t)
            continue
        r = p.add_run(t)
        r.bold = bool(f.get("b"))
        r.italic = bool(f.get("i")) and not f.get("up")
        r.underline = bool(f.get("u"))
        r.font.superscript = bool(f.get("sup"))
        r.font.subscript = bool(f.get("sub"))
        if f.get("sc"):
            r.font.small_caps = True
        if f.get("m"):
            r.font.name = "Consolas"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        elif f.get("up") and not f.get("b"):
            r.italic = False
        if size:
            r.font.size = Pt(size)


def add_link(p, url, text):
    part = p.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK,
                          is_external=True)
    hl = docx.oxml.shared.OxmlElement("w:hyperlink")
    hl.set(qn("r:id"), r_id)
    run = docx.oxml.shared.OxmlElement("w:r")
    rpr = docx.oxml.shared.OxmlElement("w:rPr")
    for tag, val in (("w:color", {"w:val": "0563C1"}), ("w:u", {"w:val": "single"})):
        el = docx.oxml.shared.OxmlElement(tag)
        for k, v in val.items():
            el.set(qn(k), v)
        rpr.append(el)
    run.append(rpr)
    t = docx.oxml.shared.OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    run.append(t)
    hl.append(run)
    p._p.append(hl)


def footer_page_numbers(doc):
    p = doc.sections[0].footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fld = docx.oxml.shared.OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    p._p.append(fld)


# ------------------------------------------------------------- equation images

def mathtext_png(tex_src, name, fontsize=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(MEDIA, exist_ok=True)
    path = os.path.join(MEDIA, name + ".png")
    fig = plt.figure(figsize=(4, 0.8), dpi=EQ_DPI)
    fig.text(0.02, 0.5, "$%s$" % tex_src, fontsize=fontsize or EQ_PTS,
             ha="left", va="center", color="k")
    fig.savefig(path, dpi=EQ_DPI, bbox_inches="tight", pad_inches=0.03,
                facecolor="white")
    plt.close(fig)
    from PIL import Image
    w, h = Image.open(path).size
    return path, w / float(EQ_DPI), h / float(EQ_DPI)


def mathtext_prep(src):
    s = src
    s = re.sub(r"\\(?:tfrac|dfrac|cfrac)", r"\\frac", s)
    s = re.sub(r"\\operatorname", r"\\mathrm", s)
    s = re.sub(r"\\(?:text|textrm|textnormal|mbox)", r"\\mathrm", s)
    s = re.sub(r"\\(?:displaystyle|textstyle|limits|nolimits)", "", s)
    s = s.replace("\\!", "")
    s = re.sub(r"\\(?:quad|qquad)", "\\\\", s)
    s = re.sub(r"\\(?:hphantom|vphantom)\{[^}]*\}", "", s)
    return s


def render_eq(src, name):
    try:
        return mathtext_png(mathtext_prep(src), name)
    except Exception as exc:
        NOTES.append("mathtext failed on [%s]: %s"
                     % (src[:60].replace("\n", " "), exc))
        return None


def grid_image(cells, aligns, name, colw_in=None, hgap_in=0.10, vgap_in=0.06):
    """cells: rows of (path,w_in,h_in) or None, laid out on a shared grid."""
    from PIL import Image
    os.makedirs(MEDIA, exist_ok=True)
    ncol = max(len(r) for r in cells)
    rows = [list(r) + [None] * (ncol - len(r)) for r in cells]
    imgs = [[Image.open(c[0]) if c else None for c in row] for row in rows]
    if colw_in:
        colw = [int(v * EQ_DPI) for v in colw_in]
    else:
        colw = [max([imgs[i][j].width for i in range(len(rows)) if imgs[i][j]] or [0])
                for j in range(ncol)]
    rowh = [max([im.height for im in row if im] or [0]) for row in imgs]
    hgap, vgap = int(hgap_in * EQ_DPI), int(vgap_in * EQ_DPI)
    total_w = sum(colw) + hgap * (ncol - 1)
    total_h = sum(rowh) + vgap * (len(rows) - 1)
    canvas = Image.new("RGB", (max(total_w, 1), max(total_h, 1)), "white")
    y = 0
    for row, rh in zip(imgs, rowh):
        x = 0
        for j, im in enumerate(row):
            if im:
                if aligns[j] == "right":
                    dx = colw[j] - im.width
                elif aligns[j] == "center":
                    dx = (colw[j] - im.width) // 2
                else:
                    dx = 0
                canvas.paste(im, (x + dx, y + (rh - im.height) // 2))
            x += colw[j] + hgap
        y += rh + vgap
    path = os.path.join(MEDIA, name + ".png")
    canvas.save(path, dpi=(EQ_DPI, EQ_DPI))
    return path, total_w / float(EQ_DPI), total_h / float(EQ_DPI)


def stack_rows(row_images, name, gap_in=0.10, brace=True, lhs=None):
    """Cases layout: lhs centred on a brace opening the stacked rows.

    Everything below is in pixels; inches only reappear on the return, so a
    PIL width and a mathtext_png width can never be added together.
    """
    from PIL import Image
    os.makedirs(MEDIA, exist_ok=True)
    if any(x is None for x in row_images):
        return None
    ims = [Image.open(p) for p, _, _ in row_images]
    gap = int(gap_in * EQ_DPI)
    body_h = sum(im.height for im in ims) + gap * (len(ims) - 1)
    body_w = max(im.width for im in ims)
    brace_im = lhs_im = None
    if brace:
        brace_im = Image.open(mathtext_png("\\{", name + "_brace",
                                           fontsize=EQ_PTS * 2.6)[0])
    if lhs:
        lhs_im = Image.open(mathtext_png(lhs, name + "_lhs")[0])
    pad_l = lhs_im.width + 8 if lhs_im else 0
    pad_b = brace_im.width + 4 if brace_im else 0
    total_w = int(pad_l + pad_b + body_w)
    canvas = Image.new("RGB", (total_w, max(body_h, brace_im.height if brace_im else 0)),
                       "white")
    x = 0
    if lhs_im:
        canvas.paste(lhs_im, (x, (canvas.height - lhs_im.height) // 2))
        x += lhs_im.width + 8
    if brace_im:
        canvas.paste(brace_im, (x, (canvas.height - brace_im.height) // 2))
        x += brace_im.width + 4
    y = 0
    for im in ims:
        canvas.paste(im, (x, y))
        y += im.height + gap
    path = os.path.join(MEDIA, name + ".png")
    canvas.save(path, dpi=(EQ_DPI, EQ_DPI))
    return path, total_w / float(EQ_DPI), canvas.height / float(EQ_DPI)


def add_equation(doc, img, number, text_runs):
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = [Inches(TEXT_WIDTH_IN - 0.7), Inches(0.7)]
    for row in tbl.rows:
        for cell, ww in zip(row.cells, widths):
            cell.width = ww
    p0 = tbl.rows[0].cells[0].paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p0.paragraph_format.space_after = Pt(2)
    if img:
        w = min(img[1], TEXT_WIDTH_IN - 0.7)
        p0.add_run().add_picture(img[0], width=Inches(w))
    else:
        add_runs(p0, text_runs)
    p1 = tbl.rows[0].cells[1].paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_after = Pt(2)
    p1.add_run("(%s)" % number if number else "")
    doc.add_paragraph()


def add_figure_image(doc, path, width_spec):
    from PIL import Image
    frac = 1.0
    m = re.match(r"([0-9.]+)\\textwidth", width_spec or "")
    if m:
        frac = float(m.group(1))
    elif width_spec and "columnwidth" in width_spec:
        frac = 0.48
    with Image.open(path) as im:
        w = min(TEXT_WIDTH_IN * frac, TEXT_WIDTH_IN)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(path, width=Inches(w))


def pdf_to_png(pdf, name):
    os.makedirs(MEDIA, exist_ok=True)
    out = os.path.join(MEDIA, name + ".png")
    if os.path.isfile(out):
        return out
    import fitz
    doc = fitz.open(pdf)
    page = doc[0]
    pix = page.get_pixmap(dpi=FIG_DPI)
    pix.save(out)
    doc.close()
    return out


# ------------------------------------------------------------------ the document

LABELS = {}
BIB = {}
COUNTS = {"head1": 0, "head2": 0, "head3": 0, "para": 0, "table": 0,
          "figure": 0, "equation": 0, "bibitem": 0, "item": 0}


class Counters(object):
    def __init__(self):
        self.section = 0
        self.sub = 0
        self.eq = 0
        self.tab = 0
        self.fig = 0

    def sec(self):
        self.section += 1
        self.sub = 0
        return "S%d" % self.section

    def subsec(self):
        self.sub += 1
        return "S%d.%d" % (self.section, self.sub)

    def eqn(self):
        self.eq += 1
        return str(self.eq)

    def table(self):
        self.tab += 1
        return "S%d" % self.tab

    def figure(self):
        self.fig += 1
        return "S%d" % self.fig


CNT = Counters()
HEADINGS = []


class Src(object):
    def __init__(self, path, depth=0):
        self.path = path
        self.base = os.path.dirname(path)
        with open(path, encoding="utf-8") as fh:
            self.text = strip_comments(fh.read())
        self.body = self.split_body()

    def split_body(self):
        m = re.search(r"\\begin\{document\}", self.text)
        head = self.text[:m.start()] if m else ""
        rest = self.text[m.end():] if m else self.text
        rest = re.split(r"\\end\{document\}", rest)[0]
        self.preamble = head
        return rest


def arg_at(src, i):
    """Skip spaces and an optional [...] group, then read {...} if present."""
    n = len(src)
    while i < n and src[i] in " \t\n":
        i += 1
    if i < n and src[i] == "[":
        j = src.find("]", i)
        i = (j + 1) if j > 0 else (i + 1)
        while i < n and src[i] in " \t\n":
            i += 1
    if i < n and src[i] == "{":
        return read_group(src, i)
    return "", i


ENV_RE = re.compile(r"\\(?:section\*?|subsection\*?|subsubsection\*?|begin\{[^}]*\}"
                    r"|input\{[^}]*\}|tableofcontents|newpage|clearpage)")


def env_span(text, i, name):
    """i points at the backslash of \\begin{name}; returns (inner, end index)."""
    tokre = re.compile(r"\\(begin|end)\{([^}]*)\}")
    first = tokre.match(text, i)
    if not first:
        raise SystemExit("expected \\begin{%s} at %d" % (name, i))
    inner_start = first.end()
    depth, pos = 1, inner_start
    while True:
        m = tokre.search(text, pos)
        if not m:
            return text[inner_start:], len(text)
        if m.group(2) == name:
            depth += 1 if m.group(1) == "begin" else -1
            if depth == 0:
                return text[inner_start:m.start()], m.end()
        pos = m.end()


def trailing_label(src, i, num):
    m = re.match(r"\s*\\label\{([^}]*)\}", src[i:])
    if m:
        LABELS[m.group(1)] = num
        return i + m.end()
    return i


def walk(doc, src):
    """Emit docx blocks for a latex fragment."""
    i, n = 0, len(src)
    while i < n:
        m = ENV_RE.search(src, i)
        if m is None:
            emit_prose(doc, src[i:])
            return
        emit_prose(doc, src[i:m.start()])
        tag = m.group(0)
        j = m.end()
        if tag.startswith(("\\section", "\\subsection", "\\subsubsection")):
            level = (3 if tag.startswith("\\subsubsection") else
                     2 if tag.startswith("\\subsection") else 1)
            star = tag.endswith("*")
            title, j = arg_at(src, j)
            num = "" if star else (CNT.sec() if level == 1 else CNT.subsec())
            j = trailing_label(src, j, num)
            head(doc, title, level, num)
        elif tag.startswith("\\input"):
            name, j = read_group(src, src.index("{", m.start()))
            p = os.path.join(SUP, name if name.endswith(".tex") else name + ".tex")
            if not os.path.isfile(p):
                raise SystemExit("input not found: " + p)
            with open(p, encoding="utf-8") as fh:
                walk(doc, strip_comments(fh.read()))
        elif tag.startswith("\\tableofcontents"):
            contents(doc)
        elif not tag.startswith("\\begin"):
            pass
        else:
            name = re.match(r"\\begin\{([^}]*)\}", tag).group(1)
            inner, j = env_span(src, m.start(), name)
            handle_env(doc, name, inner)
        i = j


PENDING_STYLE = [None]


def emit_prose(doc, frag):
    frag = frag.strip("\n")
    if not frag.strip():
        return
    for para in re.split(r"\n[ \t]*\n", frag):
        para = para.strip()
        if not para:
            continue
        if re.match(r"^%.*$", para):
            continue
        if PENDING_STYLE[0]:
            p = doc.add_paragraph(style=PENDING_STYLE[0])
            p.paragraph_format.space_after = Pt(3)
            PENDING_STYLE[0] = None
        else:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        add_runs(p, tok(para))
        COUNTS["para"] += 1


def head(doc, title, level, num):
    t = tok(title)
    p = doc.add_heading("", level=level)
    label = (num + "  " if num else "")
    r = p.add_run(label)
    r.bold = True
    add_runs(p, t)
    for run in p.runs:
        run.font.color.rgb = BLACK
        if run.font.name is None:
            run.font.name = FONT
    COUNTS["head%d" % level] += 1
    HEADINGS.append((level, (num + " " if num else "") + plain(t)))


TOC_ANCHOR = []


def contents(doc):
    TOC_ANCHOR.append(doc.add_paragraph())


def fill_contents():
    """The table of contents is written after the body, once the headings exist."""
    if not TOC_ANCHOR:
        return
    anchor = TOC_ANCHOR[0]
    p = anchor.insert_paragraph_before()
    r = p.add_run("Contents")
    r.bold = True
    r.font.size = Pt(12)
    for level, text in HEADINGS:
        q = anchor.insert_paragraph_before()
        q.paragraph_format.space_after = Pt(1)
        q.paragraph_format.left_indent = Inches(0.0 if level == 1 else 0.28)
        run = q.add_run(text)
        run.font.size = Pt(10)
        run.bold = level == 1
    anchor._p.getparent().remove(anchor._p)


def handle_env(doc, name, inner):
    if name in ("equation", "equation*", "align", "align*"):
        display(doc, name, inner)
    elif name in ("table", "table*"):
        table_env(doc, inner)
    elif name == "figure":
        figure_env(doc, inner)
    elif name == "itemize":
        items(doc, inner, "List Bullet")
    elif name == "enumerate":
        items(doc, inner, "List Number")
    elif name == "thebibliography":
        bibliography(doc, inner)
    elif name in ("center", "quote", "quotation", "flushleft", "flushright"):
        emit_prose(doc, inner)
    elif name == "tabular":
        pass
    else:
        UNMAPPED.add("\\begin{%s}" % name)
        emit_prose(doc, inner)


def display(doc, name, inner):
    body = strip_labels(inner)
    m = re.search(r"\\label\{([^}]*)\}", inner)
    label = m.group(1) if m else None
    star = name.endswith("*")
    tag = "eq%d" % (CNT.eq + 1)
    if name.startswith("align"):
        rows = [r for r in split_top(body, ["\\\\"]) if r.strip()]
        numbers = [None] * len(rows) if star else [CNT.eqn() for _ in rows]
        cells = []
        for k, r in enumerate(rows):
            parts = split_top(r, ["&"])[:2]
            cells.append([render_eq(p, "%s_r%dc%d" % (tag, k, c)) if p.strip() else None
                          for c, p in enumerate(parts)])
        colw = []
        for j in range(2):
            ws = [row[j][1] for row in cells if len(row) > j and row[j]]
            colw.append(max(ws) if ws else 0.0)
        for k, row in enumerate(cells):
            img = grid_image([row], ["right", "left"], "%s_r%d" % (tag, k),
                             colw_in=colw)
            if label and k == 0:
                LABELS[label] = numbers[0] or ""
            COUNTS["equation"] += 1 if numbers[k] else 0
            add_equation(doc, img, numbers[k] or "", tok(rows[k], {}, 1))
        return
    if "\\begin{cases}" in body:
        numbers = [None] if star else [CNT.eqn()]
        lhs, rest = body.split("\\begin{cases}", 1)
        cbody = rest.split("\\end{cases}")[0]
        rows = []
        for r in split_top(cbody, ["\\\\"]):
            if r.strip():
                rows.append("   ".join(p.strip() for p in split_top(r, ["&"])
                                       if p.strip()))
        imgs = [render_eq(x, "%s_case%d" % (tag, k)) for k, x in enumerate(rows)]
        img = stack_rows(imgs, tag + "_cases", lhs=mathtext_prep(lhs.strip()))
        text_runs = tok(body.replace("\\begin{cases}", " ")
                        .replace("\\end{cases}", " ").replace("&", ","), {}, 1)
    else:
        numbers = [None] if star else [CNT.eqn()]
        img = render_eq(body, tag)
        text_runs = tok(body, {}, 1)
    if label:
        LABELS[label] = numbers[0] or ""
    COUNTS["equation"] += 1 if numbers[0] else 0
    add_equation(doc, img, numbers[0] or "", text_runs)


def strip_labels(s):
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    s = re.sub(r"\\notag|\\nonumber", "", s)
    return s


def table_env(doc, inner):
    cap = None
    m = re.search(r"\\caption\s*(\[[^\]]*\])?\{", inner)
    if m:
        cap, _ = read_group(inner, inner.index("{", m.end() - 1))
    lab = re.search(r"\\label\{([^}]*)\}", inner)
    num = CNT.table()
    if lab:
        LABELS[lab.group(1)] = num
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("TABLE %s. " % num)
    r.bold = True
    r.font.size = Pt(9.5)
    add_runs(p, tok(cap or ""), size=9.5)
    COUNTS["table"] += 1
    tb = re.search(r"\\begin\{tabular\}", inner)
    if not tb:
        return
    pre, j = arg_at(inner, tb.end())
    body, _ = env_span(inner, tb.start(), "tabular")
    rows, merges = parse_rows(body)
    if not rows:
        return
    ncol = max(len(r) for r in rows)
    tbl = doc.add_table(rows=len(rows), cols=ncol)
    tbl.style = "Table Grid"
    for ri, row in enumerate(rows):
        for ci in range(ncol):
            cell = tbl.rows[ri].cells[ci]
            text = row[ci] if ci < len(row) else ""
            cp = cell.paragraphs[0]
            cp.paragraph_format.space_after = Pt(1)
            cp.paragraph_format.line_spacing = 1.0
            add_runs(cp, tok(text), size=9)
    for (ri, ci, span) in merges:
        if ri < len(rows) and ci + span <= ncol:
            a = tbl.rows[ri].cells[ci]
            b = tbl.rows[ri].cells[ci + span - 1]
            a.merge(b)
    doc.add_paragraph()


def parse_rows(body):
    rows, merges = [], []
    for raw in split_top(body, ["\\\\"]):
        line = raw
        for cmd in ("\\toprule", "\\midrule", "\\bottomrule", "\\hline",
                    "\\centering", "\\small", "\\footnotesize", "\\scriptsize"):
            line = line.replace(cmd, "")
        line = re.sub(r"\\cmidrule(\([^)]*\))?\{[^}]*\}", "", line)
        cells = []
        for c in split_top(line, ["&"]):
            c = c.strip()
            mm = re.match(r"^\\multicolumn\{(\d+)\}\s*\{[^}]*\}", c)
            if mm:
                span = int(mm.group(1))
                content, _ = arg_at(c, mm.end())
                start = len(cells)
                cells.append(content)
                cells.extend([""] * (span - 1))
                merges.append((len(rows), start, span))
            else:
                cells.append(c)
        if any(x.strip() for x in cells):
            rows.append(cells)
    return rows, merges


def figure_env(doc, inner):
    lab = re.search(r"\\label\{([^}]*)\}", inner)
    num = CNT.figure()
    if lab:
        LABELS[lab.group(1)] = num
    m = re.search(r"\\includegraphics\s*(\[[^\]]*\])?\s*\{([^}]*)\}", inner)
    if m:
        spec = (m.group(1) or "")[1:-1]
        name = m.group(2)
        cands = [os.path.join(SUP, "figures", name),
                 os.path.join(REPO, "figures", name),
                 os.path.join(SUP, name)]
        path = next((c for c in cands if os.path.isfile(c)), None)
        if path is None:
            raise SystemExit("figure not found: " + name)
        if path.lower().endswith(".pdf"):
            path = pdf_to_png(path, os.path.splitext(os.path.basename(path))[0])
        add_figure_image(doc, path, spec)
    c = re.search(r"\\caption\s*(\[[^\]]*\])?\{", inner)
    if c:
        cap, _ = read_group(inner, inner.index("{", c.end() - 1))
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(2)
        r = p.add_run("FIGURE %s. " % num)
        r.bold = True
        r.font.size = Pt(9.5)
        add_runs(p, tok(cap), size=9.5)
    COUNTS["figure"] += 1
    doc.add_paragraph()


def items(doc, inner, style):
    parts = re.split(r"\\item(?:\s*\[[^\]]*\])?", inner)
    for chunk in parts[1:]:
        if not chunk.strip():
            continue
        COUNTS["item"] += 1
        PENDING_STYLE[0] = style
        walk(doc, chunk)
        PENDING_STYLE[0] = None


def bibliography(doc, inner):
    hits = list(re.finditer(r"\\bibitem(?:\s*\[[^\]]*\])?\s*\{([^}]*)\}", inner))
    for k, h in enumerate(hits):
        BIB[h.group(1)] = k + 1
        COUNTS["bibitem"] += 1
        stop = hits[k + 1].start() if k + 1 < len(hits) else len(inner)
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.35)
        p.paragraph_format.first_line_indent = Inches(-0.35)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run("[%d]  " % (k + 1))
        add_runs(p, tok(inner[h.end():stop]))


def build_title(doc, preamble):
    t = re.search(r"\\title\{(.*)\}\s*$", preamble, re.S | re.M)
    a = re.search(r"\\author\{(.*)\}\s*$", preamble, re.S | re.M)
    if t:
        body, _ = read_group(preamble, preamble.index("{", t.start() + 5))
        p = doc.add_paragraph(style="Title")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for k, seg in enumerate(body.split("\\\\")):
            runs = tok(seg)
            if k:
                p.add_run().add_break(WD_BREAK.LINE)
            add_runs(p, runs)
        for run in p.runs:
            run.font.color.rgb = BLACK
    if a:
        body, _ = read_group(preamble, preamble.index("{", a.start() + 6))
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(14)
        for k, seg in enumerate(body.split("\\\\")):
            if k:
                p.add_run().add_break(WD_BREAK.LINE)
            add_runs(p, tok(seg), size=10.5)


# ------------------------------------------------------------------------- checks

def aux_labels():
    if not os.path.isfile(AUX):
        return {}
    txt = open(AUX, "rb").read().decode("latin-1")
    return dict((m.group(1), m.group(2)) for m in re.finditer(
        r"\\newlabel\{([^}]*)\}\{\{([^}]*)\}", txt))


def aux_bibcites():
    """The reference numbers pdflatex wrote into the .aux, keyed by bibitem."""
    if not os.path.isfile(AUX):
        return {}
    txt = open(AUX, "rb").read().decode("latin-1")
    return dict((m.group(1), int(m.group(2))) for m in re.finditer(
        r"\\bibcite\{([^}]*)\}\{(\d+)\}", txt))


def docx_text(path):
    from docx import Document as D
    d = D(path)
    chunks = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                chunks.append(c.text)
    return "\n".join(chunks)


def source_tokens(src):
    s = src
    s = re.sub(r"\\begin\{(?:equation|align)\*?\}.*?\\end\{(?:equation|align)\*?\}",
               " ", s, flags=re.S)
    for cmd in ("label", "input", "includegraphics", "ref", "eqref", "cite",
                "bibitem", "graphicspath", "setlength", "renewcommand",
                "emergencystretch"):
        s = re.sub(r"\\" + cmd + r"\s*(\[[^\]]*\])?\{[^{}]*\}", " ", s)
    s = re.sub(r"\\(?:documentclass|usepackage|tableofcontents|maketitle|date)"
               r"[^\n]*", " ", s)
    s = re.sub(r"\\(?:begin|end)\{[^{}]*\}", " ", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)
    s = s.replace("\\", " ")
    s = re.sub(r"[{}]", " ", s)
    words = set(re.findall(r"[A-Za-z]{5,}", s))
    nums = set(re.findall(r"\d+(?:\.\d+)+|\d+", s))
    return words, nums


def order_windows(src, size=5):
    """Consecutive word runs of the source that nothing but whitespace separates.

    The token-coverage test only asks whether a word reached the document, so a
    run of prose emitted in the wrong order passes it. These windows come from
    markup-free stretches of the source, which the .docx must reproduce verbatim
    and in sequence, so a misplaced or repeated run is caught here.
    """
    s = re.sub(r"\\begin\{(?:equation|align|tabular|picture|tikzpicture)\*?\}"
               r".*?\\end\{(?:equation|align|tabular|picture|tikzpicture)\*?\}",
               " ", src, flags=re.S)
    runs, cur = [], []
    for m in re.finditer(r"[A-Za-z]{4,}", s):
        if cur and re.match(r"^\s*$", s[cur[-1][1]:m.start()]):
            cur.append((m.group(0), m.end()))
        else:
            if len(cur) >= size:
                runs.append(cur)
            cur = [(m.group(0), m.end())]
    if len(cur) >= size:
        runs.append(cur)
    out = []
    for run in runs:
        words = [w for w, _ in run]
        for k in range(0, len(words) - size + 1, size):
            out.append(" ".join(words[k:k + size]))
    return out


def missing_windows(src, have):
    flat = re.sub(r"\s+", " ", have).lower()
    return [w for w in order_windows(src) if w.lower() not in flat]


def reset_state(labels=False):
    """Clear the build state; labels=True also forgets the numbers collected so far."""
    if labels:
        LABELS.clear()
        BIB.clear()
    NOTES[:] = []
    HEADINGS[:] = []
    TOC_ANCHOR[:] = []
    UNMAPPED.clear()
    PENDING_STYLE[0] = None
    for k in COUNTS:
        COUNTS[k] = 0
    CNT.__init__()


def render(src_obj):
    doc = Document()
    setup(doc)
    build_title(doc, src_obj.preamble)
    walk(doc, src_obj.body)
    fill_contents()
    footer_page_numbers(doc)
    return doc


def main():
    if os.path.isdir(MEDIA):
        shutil.rmtree(MEDIA)
    os.makedirs(MEDIA)
    src_obj = Src(TEX)
    # LaTeX resolves a reference to a label defined further down because it reads
    # the file twice; the first pass here only numbers the floats, so that the
    # second pass can print those numbers instead of a question mark.
    reset_state()
    render(src_obj)
    reset_state()
    doc = render(src_obj)
    doc.save(OUT)

    # ---- report and gates
    print("wrote %s (%d bytes)" % (os.path.relpath(OUT, REPO),
                                   os.path.getsize(OUT)))
    print("headings=%d paragraphs=%d tables=%d figures=%d equations=%d "
          "items=%d bibitems=%d" % (COUNTS["head1"] + COUNTS["head2"],
                                    COUNTS["para"], COUNTS["table"],
                                    COUNTS["figure"], COUNTS["equation"],
                                    COUNTS["item"], COUNTS["bibitem"]))
    bad = 0
    if UNMAPPED:
        bad = 1
        print("UNMAPPED COMMANDS (%d): %s" % (len(UNMAPPED),
                                              ", ".join(sorted(UNMAPPED))))
    unresolved = sorted(set(n for n in NOTES if n.endswith("-> ?")))
    if unresolved:
        bad = 1
        print("UNRESOLVED CROSS-REFERENCES (%d):" % len(unresolved))
        for n in unresolved[:20]:
            print("  ", n)
    full = strip_comments(open(TEX, encoding="utf-8").read())
    full = re.sub(r"\\input\{([^}]*)\}",
                  lambda m: strip_comments(open(os.path.join(
                      SUP, m.group(1) if m.group(1).endswith(".tex")
                      else m.group(1) + ".tex"), encoding="utf-8").read())
                  if os.path.isfile(os.path.join(
                      SUP, m.group(1) if m.group(1).endswith(".tex")
                      else m.group(1) + ".tex")) else " ",
                  full, flags=re.S)
    body = full.split("\\begin{document}", 1)[1].split("\\end{document}")[0]
    words, nums = source_tokens(body)
    have = docx_text(OUT)
    missing_w = sorted(w for w in words if w not in have)
    missing_n = sorted(x for x in nums if x not in have)
    if missing_w or missing_n:
        bad = 1
        print("TEXT NOT IN THE DOCX: words=%d numbers=%d" %
              (len(missing_w), len(missing_n)))
        for w in missing_w[:25]:
            print("  word:", w)
        for x in missing_n[:25]:
            print("  number:", x)
    aux = aux_labels()
    clash = []
    for lab, num in aux.items():
        mine = LABELS.get(lab)
        if mine is None:
            clash.append((lab, "unresolved", num))
        elif str(mine) != str(num):
            clash.append((lab, mine, num))
    if clash:
        bad = 1
        print("LABEL NUMBERS DISAGREE WITH THE BUILD (%d):" % len(clash))
        for lab, mine, real in clash[:20]:
            print("  %s: docx=%s aux=%s" % (lab, mine, real))
    elif aux:
        print("label cross-check against build/supplementary_final.aux: %d labels ok"
              % len(aux))
    else:
        print("label cross-check skipped: no build/supplementary_final.aux")
    bibc = aux_bibcites()
    if bibc:
        wrong = sorted(k for k in bibc if BIB.get(k) != bibc[k])
        extra = len(BIB) - len(bibc)
        if wrong or extra:
            bad = 1
            print("BIBLIOGRAPHY DISAGREES WITH THE BUILD: %d numbered wrong, "
                  "%d entries written for %d in the aux" % (len(wrong), extra,
                                                            len(bibc)))
            for k in wrong[:12]:
                print("  %s: docx=%s aux=%s" % (k, BIB.get(k), bibc[k]))
        else:
            print("bibliography: %d entries numbered as in the aux" % len(bibc))
    gaps = missing_windows(body, have)
    if gaps:
        bad = 1
        print("PROSE DOES NOT READ LIKE THE SOURCE (%d runs):" % len(gaps))
        for w in gaps[:12]:
            print("  ", w)
    else:
        print("prose order: %d five-word runs of the source reproduced verbatim"
              % len(order_windows(body)))
    if bad:
        raise SystemExit(1)
    print("docx gate: ok")


if __name__ == "__main__":
    main()

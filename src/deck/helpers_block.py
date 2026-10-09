"""Update the Round 2 deck in place to the v2 (audited) results.
Design, layout and chrome are untouched; text, tables and chart images are replaced.
Every table number is read from smartbuy/outputs, not typed."""
import json
import re
from copy import deepcopy
from pathlib import Path

import pandas as pd
from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from pptx.util import Inches

SB = Path(DECK_ROOT)
SC = SB / "outputs/scorecards"
CH = SB / "outputs" / "deck" / "charts"
ACG, INK2, BUY, DEFER = "C8102E", "4A4D55", "0F6B3F", "8A5A00"

prs = Presentation(str(SB / "outputs" / "deck" / "_restructured.pptx"))
S = {i + 1: s for i, s in enumerate(prs.slides)}


def shp(sn, sid):
    for sh in S[sn].shapes:
        if sh.shape_id == sid:
            return sh
    raise KeyError(f"slide {sn} shape {sid}")


def _fill_body(txBody, paras, color=None):
    ps = list(txBody.findall(qn("a:p")))
    while len(ps) < len(paras):
        new = deepcopy(ps[-1]); ps[-1].addnext(new); ps.append(new)
    for extra in ps[len(paras):]:
        txBody.remove(extra)
    for p_el, content in zip(ps, paras):
        for tag in ("a:r", "a:br", "a:fld"):
            for el in p_el.findall(qn(tag)):
                p_el.remove(el)
        segs = [(content, None)] if isinstance(content, str) else content
        ppr = p_el.find(qn("a:pPr"))
        drp = ppr.find(qn("a:defRPr")) if ppr is not None else None
        if color and drp is not None:
            for c in drp.iter(qn("a:srgbClr")):
                c.set("val", color)
        endp = p_el.find(qn("a:endParaRPr"))
        for text, bold in segs:
            text = re.sub(r"(?<![\w])-(?=\d)", "\u2212", text)
            r = etree.Element(qn("a:r"))
            if bold is not None or color:
                if drp is not None:
                    rpr = deepcopy(drp); rpr.tag = qn("a:rPr")
                else:
                    rpr = etree.Element(qn("a:rPr"))
                if bold is not None:
                    rpr.set("b", "1" if bold else "0")
                if color:
                    for c in rpr.iter(qn("a:srgbClr")):
                        c.set("val", color)
                r.append(rpr)
            t = etree.SubElement(r, qn("a:t")); t.text = text
            if text != text.strip():
                t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            if endp is not None:
                endp.addprevious(r)
            else:
                p_el.append(r)


def T(sn, sid, *paras, color=None):
    _fill_body(shp(sn, sid).text_frame._txBody, list(paras), color)


def cell(sn, sid, r, c, text, color=None):
    _fill_body(shp(sn, sid).table.cell(r, c).text_frame._txBody, [text], color)


def pic(sn, sid, png, h=None, top=None):
    p = shp(sn, sid)
    rid = p._element.blipFill.find(qn("a:blip")).get(qn("r:embed"))
    p.part.related_part(rid)._blob = (CH / png).read_bytes()
    if top is not None:
        p.top = Inches(top)
    if h is not None:
        p.height = Inches(h)


def fill(sn, sid, hexcol):
    s = shp(sn, sid); s.fill.solid(); s.fill.fore_color.rgb = RGBColor.from_string(hexcol)


def pct(v, d=1, sign=True):
    return f"{v:+.{d}f}%" if sign else f"{v:.{d}f}%"


sc = {m: pd.read_csv(SC / f"{m}_scorecard.csv") for m in ("aluminium", "pvc")}
bands = {m: pd.read_csv(SC / f"{m}_bands.csv") for m in ("aluminium", "pvc")}
regs = {m: pd.read_csv(SC / f"{m}_regimes.csv").set_index("regime") for m in ("aluminium", "pvc")}
RP = json.loads((SB / "outputs/replay_summary.json").read_text())
FN = json.loads((SB / "outputs/forecast_now.json").read_text())
GATE = {1: 10, 2: 12, 3: 15, 4: 12, 5: 10, 6: 10}


def head(m, h, w="development"):
    s = sc[m]
    return s[(s.window == w) & (s.h == h) & (s.model == "gated_equal_weight")].iloc[0]



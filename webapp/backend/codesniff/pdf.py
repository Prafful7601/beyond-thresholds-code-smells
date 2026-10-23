"""PDF report of an analysis (reportlab)."""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .resources import PRIMARY, SMELLS


def _p(text, style):
    return Paragraph(str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style)


def report_pdf(result):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm, title="CodeSniff report")
    ss = getSampleStyleSheet()
    small = ss["BodyText"].clone("small", fontSize=7.5, leading=9.5)
    t, risk, s = result["target"], result["risk"], result["summary"]
    score = "n/a" if risk["score"] is None else f"{risk['score']:.1f}"
    story = [_p("CodeSniff: smell risk report", ss["Title"]),
             _p(f"{result['repo']} · {t['kind']} {t['sha'][:12]} · {t.get('title') or ''}", ss["BodyText"]),
             Spacer(1, 4 * mm),
             _p(f"Smell risk score: {score} / 100 ({risk['band']})"
                + (" · small sample: fewer methods than the threshold" if risk["small_sample"] else ""), ss["Heading2"]),
             _p(risk["disclaimer"], ss["BodyText"]), Spacer(1, 2 * mm)]
    story += [_p("How the score is calculated:", ss["Heading4"])] + [_p("• " + line, small) for line in risk["formula"]]
    story += [Spacer(1, 3 * mm), _p(f"Changed methods {s['changed_methods']} · introduced {s['introduced']} · worsened "
                                    f"{s['worsened']} · improved {s['improved']} · clean {s['clean']} · deleted {s['deleted']}",
                                    ss["BodyText"]), Spacer(1, 3 * mm)]
    head = ["File", "Method", "Change", "cc", "pc", "CM zone", "P(CM)", "LPL zone", "P(LPL)", "Status", "Points"]
    rows = [head]
    for m in result["methods"]:
        b, a = m["before"], m["after"]
        arrow = lambda k: f"{b[k] if b else '–'} → {a[k] if a else '–'}"  # noqa: E731
        rows.append([_p(m["file"], small), _p(m["name"], small), m["change_type"], arrow(PRIMARY["CM"]), arrow(PRIMARY["LPL"]),
                     m["smells"]["CM"]["zone"], f"{m['smells']['CM']['probability']:.2f}", m["smells"]["LPL"]["zone"],
                     f"{m['smells']['LPL']['probability']:.2f}", m["status"],
                     "–" if m["points"] is None else f"{m['points']:.2f}"])
    tbl = Table(rows, repeatRows=1, colWidths=[62 * mm, 38 * mm, 18 * mm, 16 * mm, 16 * mm, 20 * mm, 14 * mm, 20 * mm,
                                               14 * mm, 20 * mm, 14 * mm])
    tbl.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 7.5), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef9")),
                             ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c9c8c3")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [tbl, Spacer(1, 4 * mm), _p("Notes for borderline results (candidates to review, not verdicts)", ss["Heading4"])]
    seen = set()
    for m in result["methods"]:
        for sm in SMELLS:
            n = m["smells"][sm]
            if n["zone"] == "borderline" and (sm, n["note"]) not in seen:
                seen.add((sm, n["note"]))
                story.append(_p(f"{sm} · {m['name']}: {n['note']}", small))
    doc.build(story)
    return buf.getvalue()

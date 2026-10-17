"""Build the paper's PDF from its HTML.

    python3 build/render_pdf.py tiered-peer-critique-proposal.html tiered-peer-critique-proposal.pdf \
        --footer "George W. Lott, A Tiered Peer-Critique Architecture for AI Answers, working draft v1.3, DOI pending" \
        --subject "Working draft v1.3, October 2026, with results of a second pilot. DOI pending"

Run from the proposal/ folder. Needs playwright (pip install playwright; python -m playwright install chromium) and
pypdf. The page is rendered by Chromium at Letter size with print media, build/print.css layered on the paper's own
CSS (Bitstream Charter from build/fonts/, body 9.5pt), a running footer with the citation and "n of N", and the
PDF metadata set with pypdf. Nothing in the HTML is changed.
"""
import argparse, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

ap = argparse.ArgumentParser()
ap.add_argument("html"); ap.add_argument("pdf")
ap.add_argument("--footer", required=True); ap.add_argument("--subject", required=True)
ap.add_argument("--title", default="A Tiered Peer-Critique Architecture for AI Answers")
ap.add_argument("--author", default="George W. Lott")
a = ap.parse_args()

src = Path(a.html).resolve(); here = Path(__file__).resolve().parent
css = (here / "print.css").read_text(encoding="utf-8")
html = src.read_text(encoding="utf-8")
assert html.count("</style>") >= 1
html = html.replace("</style>", "\n" + css + "\n</style>", 1)
render = src.parent / (src.stem + ".render.html")  # beside the source so build/fonts/ resolves
render.write_text(html, encoding="utf-8")

footer_html = ('<div style="width:100%; font-family: Helvetica, Arial, sans-serif; font-size:7.5pt; color:#55657A; '
               'margin: 0 20mm; display:flex; justify-content:space-between; align-items:baseline;">'
               f'<span>{a.footer}</span><span><span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')
tmp = Path(tempfile.mkstemp(suffix=".pdf")[1])
with sync_playwright() as p:
    b = p.chromium.launch(); page = b.new_page()
    page.goto(render.as_uri(), wait_until="networkidle"); page.emulate_media(media="print")
    page.pdf(path=str(tmp), format="Letter", print_background=True,
             margin={"top": "18mm", "bottom": "20mm", "left": "20mm", "right": "20mm"},
             display_header_footer=True, header_template="<div></div>", footer_template=footer_html)
    b.close()
render.unlink()
r = PdfReader(str(tmp)); w = PdfWriter()
for pg in r.pages:
    w.add_page(pg)
w.add_metadata({"/Title": a.title, "/Author": a.author, "/Subject": a.subject,
                "/Keywords": "multi-agent debate, scalable oversight, LLM-as-a-judge, model routing, mixture of agents, peer critique"})
with open(a.pdf, "wb") as f:
    w.write(f)
tmp.unlink()
print(f"{len(r.pages)} pages -> {a.pdf}")

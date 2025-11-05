# converter.py  (fresh simple converter: text + basic tables, no OCR, no images)
import os, re
import pdfplumber

def _sanitize_text(s):
    if not s:
        return ""
    s = s.replace("\r", " ")
    s = re.sub(r"\s+\n", "\n", s)
    return s.strip()

def _heading_tag(font_size):
    # very simple heuristic: larger text becomes headings
    try:
        size = float(font_size)
    except Exception:
        size = 11.0
    if size >= 16: return "h1"
    if size >= 14: return "h2"
    if size >= 12.5: return "h3"
    return "p"

def convert_pdf_to_accessible_html(pdf_path, out_dir, out_html_path):
    os.makedirs(out_dir, exist_ok=True)

    sections = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            parts = [f'<section aria-label="Page {i+1}">']

            # Words to lines by similar font sizes
            words = page.extract_words(use_text_flow=True, keep_blank_chars=False, extra_attrs=["size"]) or []
            lines, cur, cur_size = [], [], None
            for w in words:
                size = w.get("size", 11)
                if cur_size is None:
                    cur_size = size
                # group words if close in font size
                if abs(size - cur_size) <= 0.6:
                    cur.append(w["text"])
                else:
                    if cur:
                        lines.append({"text": " ".join(cur), "size": cur_size})
                    cur, cur_size = [w["text"]], size
            if cur:
                lines.append({"text": " ".join(cur), "size": cur_size})

            # Render text lines with heading tags
            for ln in lines:
                tag = _heading_tag(ln["size"])
                text = _sanitize_text(ln["text"])
                if not text:
                    continue
                if tag == "p":
                    parts.append(f"<p>{text}</p>")
                else:
                    parts.append(f"<{tag}>{text}</{tag}>")

            # Very basic tables using pdfplumber
            try:
                table_data = page.extract_tables() or []
                t_idx = 1
                for table in table_data:
                    rows_html = []
                    for r_i, row in enumerate(table):
                        cells = [(c or "").strip() for c in row]
                        if r_i == 0:
                            ths = "".join(f"<th scope='col'>{c}</th>" for c in cells)
                            rows_html.append(f"<thead><tr>{ths}</tr></thead><tbody>")
                        else:
                            tds = "".join(f"<td>{c}</td>" for c in cells)
                            rows_html.append(f"<tr>{tds}</tr>")
                    rows_html.append("</tbody>")
                    caption = f"Add a descriptive caption for the table on page {i+1}."
                    parts.append(
                        f"<figure role='group' aria-label='Table {i+1}-{t_idx}'>"
                        f"<figcaption>{caption}</figcaption>"
                        f"<table>{''.join(rows_html)}</table>"
                        f"</figure>"
                    )
                    t_idx += 1
            except Exception:
                # ignore table errors in this minimal build
                pass

            parts.append("</section>")
            sections.append("\n".join(parts))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Converted PDF</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- Minimal, LMS-friendly; no external scripts -->
  <style>
    body {{ font-family: Arial, Helvetica, sans-serif; line-height: 1.6; margin: 1rem; }}
    h1, h2, h3 {{ line-height: 1.25; }}
    figure {{ margin: 1rem 0; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #999; padding: .4rem; text-align: left; }}
    thead th {{ background: #f2f2f2; }}
    .skip-link {{ position:absolute; left:-999px; top:auto; width:1px; height:1px; overflow:hidden; }}
    .skip-link:focus {{ position:static; width:auto; height:auto; padding:.5rem; background:#eee; }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
  <header role="banner">
    <h1>Converted Document</h1>
    <p>Auto-converted from PDF. Review headings, alt text, and table captions for WCAG conformance.</p>
  </header>
  <main id="main" role="main">
    {"".join(sections)}
  </main>
  <footer role="contentinfo">
    <p>Total pages: {len(sections)}</p>
  </footer>
</body>
</html>"""

    with open(out_html_path, "w", encoding="utf-8") as f:
        f.write(html)

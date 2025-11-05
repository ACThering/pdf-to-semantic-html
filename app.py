# app.py  (fresh minimal app that returns copyable HTML for Brightspace)
from flask import Flask, request, render_template_string
import os, uuid
from converter import convert_pdf_to_accessible_html

app = Flask(__name__)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

FORM_HTML = """
<h1>Convert PDF to Accessible HTML</h1>
<form action="/convert" method="post" enctype="multipart/form-data">
  <label for="pdf">Choose PDF</label>
  <input id="pdf" name="pdf" type="file" accept="application/pdf" required />
  <button type="submit">Convert</button>
</form>
"""

@app.route("/", methods=["GET"])
def index():
  return render_template_string(FORM_HTML)

@app.route("/convert", methods=["POST"])
def convert_route():
  if "pdf" not in request.files or request.files["pdf"].filename == "":
    return "No file uploaded", 400

  f = request.files["pdf"]
  job_id = str(uuid.uuid4())[:8]
  in_path = os.path.join(UPLOAD_DIR, f"{job_id}.pdf")
  out_dir = os.path.join(OUTPUT_DIR, job_id)
  os.makedirs(out_dir, exist_ok=True)
  out_html = os.path.join(out_dir, f"{job_id}.html")

  f.save(in_path)

  try:
    # run the simple converter (text + basic tables)
    convert_pdf_to_accessible_html(in_path, out_dir, out_html)
  except Exception as e:
    return f"<h2>Conversion error</h2><pre>{e}</pre>", 500

  with open(out_html, "r", encoding="utf-8") as fp:
    html_content = fp.read()

  page = f"""
  <h2>Copy this HTML code and paste it into Brightspace</h2>
  <div style="margin:.5rem 0;">
    <button id="copyBtn">Copy to clipboard</button>
    <button id="downloadBtn">Download .html file</button>
  </div>
  <textarea id="codeBox" rows="25" cols="120" style="width:100%;font-family:monospace;">{html_content}</textarea>
  <p><a href="/">Convert another PDF</a></p>

  <script>
    document.getElementById('copyBtn').addEventListener('click', async () => {{
      const ta = document.getElementById('codeBox');
      ta.focus(); ta.select();
      try {{
        await navigator.clipboard.writeText(ta.value);
        alert('HTML copied to clipboard!');
      }} catch (err) {{
        document.execCommand('copy');
        alert('Tried to copy. If it did not work, press Ctrl+C.');
      }}
    }});
    document.getElementById('downloadBtn').addEventListener('click', () => {{
      const ta = document.getElementById('codeBox');
      const blob = new Blob([ta.value], {{ type: 'text/html;charset=utf-8' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'converted.html';
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    }});
  </script>
  """
  return render_template_string(page)

if __name__ == "__main__":
  # using port 5055 so it does not conflict with anything else
  app.run(debug=True, port=5055)

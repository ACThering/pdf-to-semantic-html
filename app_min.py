from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Mini Test Server</h1>
    <p>If you see this, Flask is working.</p>
    <form action="/echo" method="post" enctype="multipart/form-data">
      <label for="pdf">Pick a PDF:</label>
      <input id="pdf" name="pdf" type="file" accept="application/pdf" required />
      <button type="submit">Upload (test)</button>
    </form>
    """

@app.route("/echo", methods=["POST"])
def echo():
    f = request.files.get("pdf")
    name = f.filename if f else "(none)"
    return f"<h2>Got file: {name}</h2><p>Server reachable on port 5055.</p>"

if __name__ == "__main__":
    app.run(debug=True, port=5055)

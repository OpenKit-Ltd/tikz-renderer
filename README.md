# TikZ to PNG Server

A simple Flask-based Python server that converts TikZ code into PNG images. This service is particularly useful for projects that need to render high-quality diagrams using TikZ (typically a LaTeX package) and cannot easily do so in the browser with JavaScript.

## ✨ Features

* **TikZ Rendering**: Accepts raw TikZ code via API and returns a rendered PNG.
* **Whitespace Trimming**: Automatically crops excessive whitespace from the final image for a cleaner presentation.
* **Lightweight API**: Minimalistic Flask app for easy integration and quick deployment.

## 📦 Requirements

* Python 3.7+
* LaTeX with TikZ (e.g., `texlive-full`)
* Required Python packages (install via `pip`):

```bash
pip install -r requirements.txt
```

You may also need:

```bash
sudo apt-get install poppler-utils # for pdf cropping
```

## 🚀 Usage

### 1. Start the server

```bash
python server.py
```

### 2. Send a request

Use a POST request to `/render` with your TikZ code in the JSON body:

```json
{
  "tikz_code": "\\begin{tikzpicture}...\\end{tikzpicture}"
}
```

#### Example using `curl`:

```bash
curl -X POST http://localhost:5000/render \
     -H "Content-Type: application/json" \
     -d '{"tikz_code": "\\begin{tikzpicture}\\draw (0,0) -- (1,1);\\end{tikzpicture}"}' \
     --output output.png
```

### 3. Receive the image

The server returns a cropped PNG image in response.

## 🧠 How It Works

1. TikZ code is embedded into a minimal LaTeX document.
2. The document is compiled to PDF using `pdflatex`.
3. The PDF is converted to a PNG using `pdftoppm`.
4. A helper function analyses the PNG and trims excess whitespace.
5. The final cropped PNG is returned to the client.

## 🧹 Cropping Logic

The image cropping is done using pixel intensity analysis to detect the bounding box of the actual content. This ensures the output image contains only what's necessary, with minimal margins.

## 📁 Project Structure

```
.
├── server.py            # Main Flask app
├── render.py            # Core TikZ rendering logic
├── crop.py              # Image cropping utilities
├── templates/
│   └── tikz_template.tex# LaTeX template for TikZ rendering
├── requirements.txt     # Python dependencies
```

## ⚠️ Notes

* Make sure LaTeX (with TikZ) is installed and accessible via the command line.
* This server is designed for local or trusted environments — **do not expose it publicly without proper sanitisation**, as LaTeX execution can be exploited.

## 📜 License

MIT License

---

Made with ❤️ by Reuben McQueen at [OpenKit](https://openkit.co.uk)
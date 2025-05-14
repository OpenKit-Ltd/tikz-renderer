from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import tempfile

from utils import compile_tex_to_pdf, convert_pdf_to_png

app = Flask(__name__)
CORS(app)


@app.route('/compile', methods=['POST'])
def compile_tikz():
    data = request.json

    if not data or 'tikz_code' not in data:
        return jsonify({'error': 'No Tikz code provided'}), 400

    output_format = data.get('format', 'png')
    tikz_code = data['tikz_code']

    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, "diagram.tex")
        pdf_path = os.path.join(temp_dir, "diagram.pdf")

        success, result = compile_tex_to_pdf(tikz_code, tex_path, pdf_path)

        if not success:
            return jsonify({'error': 'Compilation failed', 'details': result}), 500

        if output_format == 'pdf':
            return send_file(pdf_path,
                             mimetype='application/pdf',
                             as_attachment=True,
                             download_name='diagram.pdf')
        else:
            png_data, error = convert_pdf_to_png(pdf_path)
            if error:
                return jsonify({'error': 'PNG conversion failed', 'details': error}), 500

            return send_file(png_data,
                             mimetype='image/png',
                             as_attachment=True,
                             download_name='diagram.png')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

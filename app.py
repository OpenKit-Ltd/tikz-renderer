from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import tempfile

from utils import compile_tex_to_pdf_no_crop, crop_pdf_smart, convert_pdf_to_png

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

        # Compile without cropping
        success, result = compile_tex_to_pdf_no_crop(
            tikz_code, tex_path, pdf_path)

        if not success:
            return jsonify({'error': 'Compilation failed', 'details': result}), 500

        if output_format == 'pdf':
            # Return PDF without cropping
            return send_file(pdf_path,
                             mimetype='application/pdf',
                             as_attachment=True,
                             download_name='diagram.pdf')
        else:
            # For PNG, crop first then convert
            try:
                print("Smart cropping PDF for PNG output...")
                crop_pdf_smart(
                    pdf_path, pdf_path, bottom_padding_pixels=120, right_padding_pixels=100)
                print("Smart PDF Cropped successfully!")
            except Exception as e:
                print(f"Smart PDF cropping failed: {e}")
                # Continue with uncropped PDF if cropping fails

            png_data, error = convert_pdf_to_png(pdf_path)
            if error:
                return jsonify({'error': 'PNG conversion failed', 'details': error}), 500

            return send_file(png_data,
                             mimetype='image/png',
                             as_attachment=True,
                             download_name='diagram.png')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

import os
import subprocess
import io
from pypdf import PdfReader, PdfWriter
from pdf2image import convert_from_path


WHITE_THRESHOLD = 220


def is_pixel_white(pixel):
    r, g, b = pixel[:3]
    return r > WHITE_THRESHOLD and g > WHITE_THRESHOLD and b > WHITE_THRESHOLD


def is_row_white(image, y):
    width = image.width
    for x in range(width):
        pixel = image.getpixel((x, y))
        if not is_pixel_white(pixel):
            return False
    return True


def is_column_white(image, x):
    """Check if an entire column of pixels is white."""
    height = image.height
    for y in range(height):
        pixel = image.getpixel((x, y))
        if not is_pixel_white(pixel):
            return False
    return True


def detect_bottom_crop_pixels(image):
    height = image.height
    crop_pixels = 0
    for y in range(height - 1, -1, -1):
        if is_row_white(image, y):
            crop_pixels += 1
        else:
            break
    return crop_pixels


def detect_right_crop_pixels(image):
    """Detect the number of white pixels from the right side of the image."""
    width = image.width
    crop_pixels = 0
    for x in range(width - 1, -1, -1):
        if is_column_white(image, x):
            crop_pixels += 1
        else:
            break
    return crop_pixels


def convert_pdf_page_to_image(pdf_path):
    """Convert the first page of a PDF to a PIL Image object."""
    try:
        images = convert_from_path(
            pdf_path, dpi=300, first_page=1, last_page=1,
            single_file=True, transparent=True
        )
        if not images:
            return None, "Failed to convert PDF to image"
        return images[0], None
    except Exception as e:
        return None, str(e)


def crop_pdf_smart(input_pdf_path, output_pdf_path, bottom_padding_pixels=100, right_padding_pixels=100):
    """Crop whitespace from both bottom and right sides of the PDF with padding."""
    image, error = convert_pdf_page_to_image(input_pdf_path)
    if error:
        print(
            f"Warning: Could not convert PDF to image for smart crop. Error: {error}")
        return

    print(f"Debug: Image conversion successful")
    print(f"Debug: Image mode: {image.mode}, size: {image.size}")
    debug_image_path = "debug_image.png"
    image.save(debug_image_path)
    print(f"Debug PNG image saved to: {debug_image_path}")

    # Detect bottom crop pixels
    bottom_crop_pixels = detect_bottom_crop_pixels(image)
    print(
        f"Detected bottom_crop_pixels (before padding adjustment): {bottom_crop_pixels}")
    bottom_crop_pixels = max(0, bottom_crop_pixels - bottom_padding_pixels)
    print(
        f"Detected bottom_crop_pixels (after padding adjustment): {bottom_crop_pixels}")

    # Detect right crop pixels
    right_crop_pixels = detect_right_crop_pixels(image)
    print(
        f"Detected right_crop_pixels (before padding adjustment): {right_crop_pixels}")
    right_crop_pixels = max(0, right_crop_pixels - right_padding_pixels)
    print(
        f"Detected right_crop_pixels (after padding adjustment): {right_crop_pixels}")

    if bottom_crop_pixels == 0 and right_crop_pixels == 0:
        print("No whitespace detected for smart crop after padding adjustment.")
        return

    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    points_per_pixel = 72 / 300  # Convert from 300 DPI to points

    for page in reader.pages:
        page_height_points = float(page.mediabox.height)
        page_width_points = float(page.mediabox.width)

        # Calculate crop points
        bottom_crop_points = bottom_crop_pixels * points_per_pixel
        right_crop_points = right_crop_pixels * points_per_pixel
        print(f"Calculated bottom_crop_points: {bottom_crop_points:.2f}")
        print(f"Calculated right_crop_points: {right_crop_points:.2f}")

        # Get current mediabox coordinates
        lower_left_x = float(page.mediabox.lower_left[0])
        lower_left_y = float(page.mediabox.lower_left[1])
        upper_right_x = float(page.mediabox.upper_right[0])
        upper_right_y = float(page.mediabox.upper_right[1])

        # Adjust bottom (y coordinate)
        new_lower_left_y = lower_left_y + bottom_crop_points
        if new_lower_left_y > upper_right_y:
            new_lower_left_y = upper_right_y

        # Adjust right side (x coordinate)
        new_upper_right_x = upper_right_x - right_crop_points
        if new_upper_right_x < lower_left_x:
            new_upper_right_x = lower_left_x

        # Apply new coordinates to mediabox and cropbox
        page.mediabox.lower_left = (lower_left_x, new_lower_left_y)
        page.mediabox.upper_right = (new_upper_right_x, upper_right_y)
        page.cropbox.lower_left = (lower_left_x, new_lower_left_y)
        page.cropbox.upper_right = (new_upper_right_x, upper_right_y)

        writer.add_page(page)

    with open(output_pdf_path, "wb") as output_file:
        writer.write(output_file)

    print(
        f"Smart cropped PDF saved to: {output_pdf_path}\n"
        f"Bottom crop: {bottom_crop_pixels} pixels ({bottom_crop_points:.2f} points), Padding: {bottom_padding_pixels} pixels\n"
        f"Right crop: {right_crop_pixels} pixels ({right_crop_points:.2f} points), Padding: {right_padding_pixels} pixels"
    )


def compile_tex_to_pdf_no_crop(tex_code: str, tex_filename: str = "diagram.tex", pdf_filename: str = "diagram.pdf"):
    """Compile TeX code to PDF without any cropping."""
    if "\\documentclass" not in tex_code:
        full_tex_code = """\\documentclass[tikz, preview]{standalone}
\\usepackage{tikz}
\\begin{document}
""" + tex_code + """
\\end{document}"""
    else:
        full_tex_code = tex_code

    with open(tex_filename, "w") as f:
        f.write(full_tex_code)

    result = subprocess.run(
        ["tectonic", tex_filename],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print("Tectonic compilation failed:")
        print(result.stdout)
        print(result.stderr)
        return False, result.stderr
    else:
        print("PDF successfully generated!")
        base_name, _ = os.path.splitext(tex_filename)
        generated_pdf = base_name + ".pdf"
        if os.path.exists(generated_pdf) and generated_pdf != pdf_filename:
            os.rename(generated_pdf, pdf_filename)

        return True, pdf_filename


def compile_tex_to_pdf(tex_code: str, tex_filename: str = "diagram.tex", pdf_filename: str = "diagram.pdf"):
    """Legacy function - compiles TeX and crops (kept for backward compatibility)."""
    if "\\documentclass" not in tex_code:
        full_tex_code = """\\documentclass[tikz, preview]{standalone}
\\usepackage{tikz}
\\begin{document}
""" + tex_code + """
\\end{document}"""
    else:
        full_tex_code = tex_code

    with open(tex_filename, "w") as f:
        f.write(full_tex_code)

    result = subprocess.run(
        ["tectonic", tex_filename],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print("Tectonic compilation failed:")
        print(result.stdout)
        print(result.stderr)
        return False, result.stderr
    else:
        print("PDF successfully generated!")
        base_name, _ = os.path.splitext(tex_filename)
        generated_pdf = base_name + ".pdf"
        if os.path.exists(generated_pdf) and generated_pdf != pdf_filename:
            os.rename(generated_pdf, pdf_filename)

        # Smart crop using pixel analysis for both bottom and right
        try:
            print("Smart cropping PDF...")
            crop_pdf_smart(
                pdf_filename, pdf_filename, bottom_padding_pixels=120, right_padding_pixels=100)
            print("Smart PDF Cropped successfully!")
        except Exception as e:
            print(f"Smart PDF cropping failed: {e}")
            return True, pdf_filename

        return True, pdf_filename


# Keeping the old function for backward compatibility
def crop_pdf_bottom_smart(input_pdf_path, output_pdf_path, bottom_padding_pixels=100):
    """Legacy function that only crops the bottom whitespace."""
    crop_pdf_smart(input_pdf_path, output_pdf_path,
                   bottom_padding_pixels=bottom_padding_pixels, right_padding_pixels=0)


def convert_pdf_to_png(pdf_path):
    """Convert a PDF file to PNG image"""
    try:
        images = convert_from_path(
            pdf_path, dpi=300, first_page=1, last_page=1)
        if not images:
            return None, "Failed to convert PDF to image"

        image = images[0]
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr, None
    except Exception as e:
        return None, str(e)

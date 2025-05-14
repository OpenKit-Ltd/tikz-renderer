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


def detect_bottom_crop_pixels(image):
    height = image.height
    crop_pixels = 0
    for y in range(height - 1, -1, -1):
        if is_row_white(image, y):
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


# Added bottom_padding_pixels parameter with default 10
def crop_pdf_bottom_smart(input_pdf_path, output_pdf_path, bottom_padding_pixels=100):
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

    crop_pixels = detect_bottom_crop_pixels(image)
    print(f"Detected crop_pixels (before padding adjustment): {crop_pixels}")

    # Subtract padding, ensure not negative
    crop_pixels = max(0, crop_pixels - bottom_padding_pixels)
    print(f"Detected crop_pixels (after padding adjustment): {crop_pixels}")

    if crop_pixels == 0:
        print("No bottom whitespace detected for smart crop after padding adjustment.")
        return

    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        page_height_points = float(page.mediabox.height)
        page_width_points = float(page.mediabox.width)

        points_per_pixel = 72 / 300
        crop_points = crop_pixels * points_per_pixel
        print(f"Calculated crop_points: {crop_points:.2f}")

        lower_left_x = float(page.mediabox.lower_left[0])
        lower_left_y = float(page.mediabox.lower_left[1])
        upper_right_x = float(page.mediabox.upper_right[0])
        upper_right_y = float(page.mediabox.upper_right[1])

        new_lower_left_y = lower_left_y + crop_points
        if new_lower_left_y > upper_right_y:
            new_lower_left_y = upper_right_y

        page.mediabox.lower_left = (lower_left_x, new_lower_left_y)
        page.mediabox.upper_right = (upper_right_x, upper_right_y)
        page.cropbox.lower_left = (lower_left_x, new_lower_left_y)
        page.cropbox.upper_right = (upper_right_x, upper_right_y)

        writer.add_page(page)

    with open(output_pdf_path, "wb") as output_file:
        writer.write(output_file)
    # Added padding pixels to print
    print(
        f"Smart cropped PDF saved to: {output_pdf_path}, Cropped pixels: {crop_pixels}, Cropped points: {crop_points:.2f}, Padding pixels: {bottom_padding_pixels}")


def compile_tex_to_pdf(tex_code: str, tex_filename: str = "diagram.tex", pdf_filename: str = "diagram.pdf"):
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

        # Smart crop using pixel analysis
        try:
            print("Smart cropping PDF...")
            # Pass bottom_padding_pixels=10
            crop_pdf_bottom_smart(
                pdf_filename, pdf_filename, bottom_padding_pixels=120)
            print("Smart PDF Cropped successfully!")
        except Exception as e:
            print(f"Smart PDF cropping failed: {e}")
            return True, pdf_filename

        return True, pdf_filename


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

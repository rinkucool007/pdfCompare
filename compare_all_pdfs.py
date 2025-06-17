import os
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import img2pdf

# Configuration
OLD_FOLDER = "old"
NEW_FOLDER = "new"
OUTPUT_PDF_PATH = "output_report.pdf"

# Global list for collecting temporary image paths
all_temp_images = []

def pdf_to_images(pdf_path, dpi=200):
    """Convert PDF to list of PIL Images using PyMuPDF."""
    doc = fitz.open(pdf_path)
    images = []
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        images.append(img.convert("RGB"))
    doc.close()
    return images


def draw_red_boxes(img1, img2, page_number, filename):
    """Compare two PIL images and draw red rectangles on img2 where they differ."""
    # Convert to OpenCV format
    img1_cv = cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2BGR)
    img2_cv = cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2BGR)

    if img1_cv.shape != img2_cv.shape:
        height, width = max(img1_cv.shape[0], img2_cv.shape[0]), max(img1_cv.shape[1], img2_cv.shape[1])
        img1_cv = cv2.resize(img1_cv, (width, height))
        img2_cv = cv2.resize(img2_cv, (width, height))

    diff = cv2.absdiff(img1_cv, img2_cv)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    num_differences = len(contours)
    if num_differences > 0:
        print(f"{filename}, Page {page_number}: Found {num_differences} difference(s).")

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(img2_cv, (x, y), (x + w, y + h), (0, 0, 255), 2)

    return Image.fromarray(cv2.cvtColor(img2_cv, cv2.COLOR_BGR2RGB))


def create_side_by_side_image(img1, img2, title="Comparison"):
    w1, h1 = img1.size
    w2, h2 = img2.size
    combined_width = w1 + w2
    max_height = max(h1, h2)

    new_img = Image.new('RGB', (combined_width, max_height + 40), color=(255, 255, 255))
    new_img.paste(img1, (0, 40))
    new_img.paste(img2, (w1, 40))

    draw = ImageDraw.Draw(new_img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    draw.text((10, 5), title, fill="black", font=font)

    return new_img


def add_summary_page(summary_text, filename):
    """Generate a summary page listing findings for one file."""
    summary_img = Image.new('RGB', (1200, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(summary_img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
        body_font = ImageFont.truetype("arial.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    draw.text((50, 30), f"🔍 File: {filename}", fill="black", font=title_font)

    y = 80
    for line in summary_text:
        draw.text((70, y), f"• {line}", fill="black", font=body_font)
        y += 30

    temp_path = f"summary_{len(all_temp_images)}.jpg"
    summary_img.save(temp_path, "JPEG")
    return temp_path


def compare_pdf_pair(old_path, new_path, filename):
    print(f"\n🔄 Comparing: {filename}")
    images_old = pdf_to_images(old_path)
    images_new = pdf_to_images(new_path)

    temp_files = []
    summary = []

    min_pages = min(len(images_old), len(images_new))
    for i in range(min_pages):
        print(f"Processing page {i+1} of '{filename}'...")
        highlighted_img = draw_red_boxes(images_old[i], images_new[i], i+1, filename)
        combined_img = create_side_by_side_image(images_old[i], highlighted_img, f"Page {i+1} - {filename}")
        temp_path = f"temp_{len(all_temp_images) + i}.jpg"
        combined_img.save(temp_path, "JPEG")
        temp_files.append(temp_path)

        diff_count = np.sum(cv2.absdiff(cv2.cvtColor(np.array(images_old[i]), cv2.COLOR_RGB2GRAY),
                              cv2.cvtColor(np.array(images_new[i]), cv2.COLOR_RGB2GRAY)) > 30)
        if diff_count > 0:
            summary.append(f"Page {i+1}: {int(diff_count)} differences found.")

    if len(images_old) != len(images_new):
        summary.append(f"⚠️ Warning: Unequal number of pages ({len(images_old)} vs {len(images_new)})")

    if not summary:
        summary.append("✅ No differences found between the documents.")

    summary_file = add_summary_page(summary, filename)
    temp_files.append(summary_file)
    all_temp_images.extend(temp_files)


def compare_all_folders():
    old_files = set(f for f in os.listdir(OLD_FOLDER) if f.endswith(".pdf"))
    new_files = set(f for f in os.listdir(NEW_FOLDER) if f.endswith(".pdf"))

    common_files = sorted(old_files & new_files)

    if not common_files:
        print("❌ No matching PDFs found in both folders.")
        return

    print(f"\n📄 Found {len(common_files)} matching PDF files. Starting comparison...\n")

    for filename in common_files:
        old_path = os.path.join(OLD_FOLDER, filename)
        new_path = os.path.join(NEW_FOLDER, filename)
        compare_pdf_pair(old_path, new_path, filename)

    print("\n📦 Generating final output PDF...")
    with open(OUTPUT_PDF_PATH, "wb") as f:
        f.write(img2pdf.convert(all_temp_images))

    print(f"✅ Output saved to {OUTPUT_PDF_PATH}")

    print("🗑️ Cleaning up temporary image files...")
    for temp_file in all_temp_images:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    print("🎉 Done!")


if __name__ == "__main__":
    import io
    compare_all_folders()

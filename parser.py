import pdfplumber
import docx
import cv2
import numpy as np
import tempfile
from PIL import Image
from ocr_engine import extract_text_from_pdf, extract_text_from_image_array


def extract_text_from_image(image_file):
    import gc
    gc.collect()

    # Use OpenCV directly to avoid PIL double memory buffer overhead
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # If the image is extremely high-resolution, resize it to save RAM during OCR
    if image.shape[1] > 2000 or image.shape[0] > 2000:
        scale = 2000 / max(image.shape[0], image.shape[1])
        new_w = int(image.shape[1] * scale)
        new_h = int(image.shape[0] * scale)
        image = cv2.resize(image, (new_w, new_h))

    text = extract_text_from_image_array(image)

    return text


def parse_file(uploaded_file):

    name = uploaded_file.name.lower()

    # ---------------- PDF ----------------
    if name.endswith(".pdf"):

        text = ""

        try:
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text

        except:
            pass

        if text.strip() != "":
            return text

        uploaded_file.seek(0)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            temp_path = tmp.name

        return extract_text_from_pdf(temp_path)

    # ---------------- DOCX ----------------
    elif name.endswith(".docx"):

        doc = docx.Document(uploaded_file)

        text = "\n".join([p.text for p in doc.paragraphs])

        return text

    # ---------------- IMAGE ----------------
    elif name.endswith((".png", ".jpg", ".jpeg")):

        return extract_text_from_image(uploaded_file)

    # ---------------- TXT ----------------
    else:

        return uploaded_file.read().decode()

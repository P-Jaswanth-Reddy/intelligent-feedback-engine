import os
import easyocr
from pdf2image import convert_from_path
import numpy as np
import cv2
import streamlit as st

@st.cache_resource
def get_ocr_reader():
    import gc
    gc.collect()
    import torch
    torch.set_num_threads(1)
    # Initialize the EasyOCR reader without quantization to prevent peak memory spike
    return easyocr.Reader(['en'], gpu=False, quantize=False)


def preprocess_image(image):
    # 1. Grayscale Conversion (Eq 4.1)
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image

    # 2. Gaussian Blur and Convolutional Noise Reduction (Eq 4.2)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. Adaptive Binarization via Otsu's Thresholding Methodology (Eq 4.3)
    # Using THRESH_BINARY_INV temporarily for contour/skew calculations
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    # 4. Morphological Transformations and Skew Correction (Eq 4.4, 4.5)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) > 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        # Build the Affine geometric rotation matrix
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    else:
        rotated = gray

    # Final Otsu thresholding for Tesseract reading
    _, clean_binary = cv2.threshold(rotated, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    return clean_binary

def pdf_to_images(pdf_path):

    images = convert_from_path(pdf_path)

    return images

def extract_text_from_image_array(image_array):
    processed = preprocess_image(image_array)
    reader = get_ocr_reader()
    # detail=0 returns just the text, combining it with newlines
    results = reader.readtext(processed, detail=0)
    return "\n".join(results)

def extract_text_from_pdf(pdf_path):

    pages = pdf_to_images(pdf_path)

    full_text = ""

    for page in pages:

        # Convert PIL image to OpenCV format
        image = np.array(page)

        text = extract_text_from_image_array(image)

        full_text += text + "\n"

    return full_text
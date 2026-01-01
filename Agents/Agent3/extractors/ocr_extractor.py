# agents/agent3/extractors/ocr_extractor.py
import os
from PIL import Image
import pytesseract

# If Tesseract not on PATH, you can set pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_screenshots(screenshot_results):
    texts = []
    for item in screenshot_results:
        if "screenshot" not in item:
            continue
        path = item["screenshot"]
        if not os.path.exists(path):
            continue
        try:
            img = Image.open(path)
            txt = pytesseract.image_to_string(img)
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            texts.extend(lines)
        except Exception:
            continue
    return {"ui_visible_text": texts}

from typing import List, Dict
from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import re


def _normalize_text(s: str) -> str:
    s = s.replace("\u00ad", "")  # soft hyphen
    s = re.sub(r"-\n", "", s)    # join hyphen-lns
    s = re.sub(r"\s+\n", "\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


class PdfExtractor:
    def __init__(self, ocr_lang: str = "eng"):
        self.ocr_lang = ocr_lang

    def extract_pages(self, pdf_path: str) -> List[Dict]:
        reader = PdfReader(pdf_path)
        results: List[Dict] = []
        for idx, page in enumerate(reader.pages, start=1):
            txt = page.extract_text() or ""
            txt = _normalize_text(txt)
            chars = len(txt)

            # OCR fallback if text layer is likely insufficient
            is_ocr = False
            if chars < 200:
                images = convert_from_path(pdf_path, dpi=300, first_page=idx, last_page=idx)
                if images:
                    ocr_text = pytesseract.image_to_string(images[0], lang=self.ocr_lang)
                    ocr_text = _normalize_text(ocr_text)
                    if len(ocr_text) > chars:
                        txt = ocr_text
                        chars = len(txt)
                        is_ocr = True

            # skip super-short garbage
            if chars >= 50:
                results.append({"page": idx, "text": txt, "has_ocr": is_ocr, "chars": chars})
        return results



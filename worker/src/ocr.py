from __future__ import annotations

from pathlib import Path
from typing import Iterable


def run_ocr(file_path: Path) -> Iterable[str]:
    """Perform OCR on the uploaded document.

    This placeholder implementation treats the file as UTF-8 text and
    returns individual lines. In production this would call a dedicated OCR
    engine such as Tesseract or a hosted API.
    """

    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return [line.strip() for line in text.splitlines() if line.strip()]

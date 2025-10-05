from __future__ import annotations

from pathlib import Path
from typing import Iterable
from zipfile import ZipFile, is_zipfile


def run_ocr(file_path: Path) -> Iterable[str]:
    """Perform OCR on the uploaded document.

    This placeholder implementation treats the file as UTF-8 text and
    returns individual lines. In production this would call a dedicated OCR
    engine such as Tesseract or a hosted API.
    """
    if is_zipfile(file_path):
        lines: list[str] = []
        with ZipFile(file_path) as archive:
            for member in sorted(name for name in archive.namelist() if not name.endswith("/")):
                with archive.open(member) as handle:
                    text = handle.read().decode("utf-8", errors="ignore")
                lines.extend(line.strip() for line in text.splitlines() if line.strip())
        return lines

    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return [line.strip() for line in text.splitlines() if line.strip()]

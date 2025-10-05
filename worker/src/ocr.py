from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator
from zipfile import ZipFile, is_zipfile


@dataclass(frozen=True)
class OCRLine:
    """Simplified representation of OCR output for a single line of text."""

    text: str
    confidence: float


def _iter_text_lines(text: str) -> Iterator[OCRLine]:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        yield OCRLine(text=line, confidence=_estimate_confidence(line))


def _estimate_confidence(text: str) -> float:
    """Return a deterministic confidence score for placeholder OCR output."""

    lowered = text.lower()
    score = 0.98
    if any(keyword in lowered for keyword in ("incerta", "aguardando", "§")):
        score -= 0.2
    if any(char.isdigit() for char in text):
        score -= 0.02
    return max(0.0, min(1.0, score))


def run_ocr(file_path: Path) -> Iterable[OCRLine]:
    """Perform OCR on the uploaded document.

    This placeholder implementation treats the file as UTF-8 text and
    returns individual lines. In production this would call a dedicated OCR
    engine such as Tesseract or a hosted API.
    """
    if is_zipfile(file_path):
        lines: list[OCRLine] = []
        with ZipFile(file_path) as archive:
            for member in sorted(name for name in archive.namelist() if not name.endswith("/")):
                with archive.open(member) as handle:
                    text = handle.read().decode("utf-8", errors="ignore")
                lines.extend(_iter_text_lines(text))
        return lines

    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return list(_iter_text_lines(text))

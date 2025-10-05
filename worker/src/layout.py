from __future__ import annotations

from typing import Iterable, List


def detect_layout(lines: Iterable[str]) -> List[dict[str, str]]:
    """Detects layout structures in the OCR lines."""

    layout = []
    for index, line in enumerate(lines):
        layout.append({
            "index": index,
            "content": line,
            "section": "header" if index == 0 else "body",
        })
    return layout

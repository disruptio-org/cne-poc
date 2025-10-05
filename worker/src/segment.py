from __future__ import annotations

from collections import defaultdict
from typing import Iterable


SEGMENT_KEYS = ["orgao", "lista", "tipo"]


def segment_lines(layout: Iterable[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    segments: dict[str, list[dict[str, str]]] = defaultdict(list)
    for entry in layout:
        key = "body"
        lowered = entry["content"].lower()
        for segment in SEGMENT_KEYS:
            if segment in lowered:
                key = segment
                break
        segments[key].append(entry)
    return dict(segments)

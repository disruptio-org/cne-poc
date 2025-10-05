from __future__ import annotations

import json
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, Tuple

MASTER_DIR = Path("data/master")


def _load_master() -> Dict[str, dict]:
    records: Dict[str, dict] = {}
    for file in MASTER_DIR.glob("*.json"):
        data = json.loads(file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            records[data["sigla"].upper()] = data
        elif isinstance(data, list):
            for item in data:
                records[item["sigla"].upper()] = item
    return records


MASTER_CACHE = _load_master()


def match_sigla(sigla: str) -> Tuple[str, dict | None]:
    upper = sigla.upper()
    if upper in MASTER_CACHE:
        return upper, MASTER_CACHE[upper]
    matches = get_close_matches(upper, MASTER_CACHE.keys(), n=1, cutoff=0.7)
    if matches:
        match = matches[0]
        return match, MASTER_CACHE[match]
    return upper, None

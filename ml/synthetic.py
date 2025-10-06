from __future__ import annotations

import random
from typing import List

from api.app.services.master_data import MasterDataService

from .training import build_training_corpus


def generate_synthetic_dataset(multiplier: int = 2) -> List[dict[str, str]]:
    master_service = MasterDataService()
    master_records = master_service.list_records().records
    base_rows = build_training_corpus()
    synthetic: List[dict[str, str]] = []
    for _ in range(multiplier):
        for row in base_rows:
            record = row.copy()
            if master_records:
                match = random.choice(master_records)
                record["SIGLA"] = match.sigla
                record["PARTIDO_PROPONENTE"] = match.descricao
            record["INDEPENDENTE"] = record.get("INDEPENDENTE") or "N"
            record["NOME_CANDIDATO"] = f"{record.get('NOME_CANDIDATO', '').strip()} (synthetic)".strip()
            synthetic.append(record)
    return synthetic

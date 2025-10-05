#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

MASTER_DIR = Path('data/master')
MASTER_DIR.mkdir(parents=True, exist_ok=True)

seed = [
    {
        'sigla': 'MEC',
        'descricao': 'Ministério da Educação',
        'codigo': '001',
        'metadata': {'uf': 'BR'},
    },
    {
        'sigla': 'INEP',
        'descricao': 'Instituto Nacional de Estudos e Pesquisas Educacionais',
        'codigo': '002',
        'metadata': {'uf': 'BR'},
    },
]

(MASTER_DIR / 'default.json').write_text(json.dumps(seed, indent=2, ensure_ascii=False), encoding='utf-8')
print('Seeded master data with', len(seed), 'records')

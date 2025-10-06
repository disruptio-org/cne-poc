.PHONY: api worker web registry seed develop test

api:
	uvicorn api.app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	python -m worker.src.worker

web:
	cd web && npm install && npm run dev -- --host 0.0.0.0 --port 5173

registry:
	python -m http.server 9000 --directory data/state

seed:
	python scripts/seed_master_data.py

develop: seed
	@echo "Run 'make api', 'make worker' and 'make web' in separate terminals."

test:
	pytest -q

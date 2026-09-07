.PHONY: test test-integration seed codegen

test:
	pytest -q tests/unit

test-integration:
	pytest -q tests/integration

seed:
	python scripts/seed.py --tenant demo

codegen:
	python scripts/gen_models.py --out generated/

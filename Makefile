PYTHON := .venv/bin/python
PIP := .venv/bin/pip
UVICORN := .venv/bin/uvicorn

.PHONY: setup run run-api eval-baselines eval-neural eval-zeroshot

setup:
	python3.11 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e .

run:
	./scripts/run_api.sh

run-api:
	./scripts/run_api.sh

eval-baselines:
	$(PYTHON) -m models.baseline.evaluate_baselines

eval-neural:
	$(PYTHON) -m models.neural.evaluate

eval-zeroshot:
	$(PYTHON) -m models.zeroshot.llm_simplifier

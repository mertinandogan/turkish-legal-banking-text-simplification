# Turkish Legal Banking Text Simplification

Neural and baseline-driven simplification pipeline for Turkish banking regulations (BDDK), with a reproducible data workflow, comparative evaluation, and a web API/UI for interactive testing.

## What This Project Does

This repository tackles a practical NLP problem:

- Input: complex Turkish legal banking text
- Output: simplified text that remains faithful to legal meaning

The project includes:

- Data collection from BDDK documents
- Complex paragraph extraction and filtering
- Parallel dataset creation (`complex -> simple`)
- Baseline evaluation (TF-IDF, TextRank)
- Neural fine-tuning (mT5 + LoRA)
- Zero-shot LLM comparison
- Faithfulness and hallucination-oriented analysis
- FastAPI backend + simple web interface

## Current Project Snapshot

Based on the generated artifacts currently in this repository:

- Processed raw documents: **23**
- Extracted complex paragraphs: **70**
- Parallel split:
  - Train: **56**
  - Validation: **7**
  - Test (`test_gold`): **7**

Pilot evaluation files are under `results/`.

## Repository Structure

```text
api/                    FastAPI app (`api/main.py`)
configs/                YAML config (`configs/default.yaml`)
data/
  raw/                  Downloaded BDDK documents (.md + metadata)
  paragraphs/           Extracted complex paragraphs
  parallel/             Train/val/test parallel pairs
data_collection/        Scraping + extraction + synthetic dataset tools
models/
  baseline/             TF-IDF / TextRank baselines
  neural/               mT5 + LoRA training/inference/evaluation
  zeroshot/             Prompt-based LLM simplifier
evaluation/             Comparison + faithfulness + hallucination analysis
results/                Generated metrics, checkpoints, reports
web/                    Frontend assets/templates
```

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- Hugging Face Transformers
- PEFT / LoRA
- PyTorch
- scikit-learn, NetworkX
- OpenAI-compatible client (OpenRouter/OpenAI)
- JSONL-based data pipeline

## Setup

### 1) Create virtual environment

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e .
```

### 2) Optional API keys

For real LLM-based synthetic generation / zero-shot comparison:

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
# or
export OPENAI_API_KEY="sk-..."
```

If no key is set, zero-shot module can run in an offline fallback mode (rule-based simplification), useful for pipeline checks only.

## End-to-End Workflow

All commands assume project root.

### A) Collect BDDK documents

```bash
.venv/bin/python data_collection/bddk_scraper.py --mode test
```

Or range mode:

```bash
.venv/bin/python data_collection/bddk_scraper.py --mode range --start 1 --end 500
```

### B) Extract complex paragraphs

```bash
.venv/bin/python data_collection/paragraph_extractor.py --config configs/default.yaml
```

### C) Create parallel dataset

```bash
.venv/bin/python data_collection/synthetic_simplifier.py --config configs/default.yaml
```

### D) Baseline evaluation

```bash
.venv/bin/python models/baseline/evaluate_baselines.py \
  --test-file data/parallel/test_gold.jsonl \
  --output results/baseline_scores.json
```

### E) Neural training (mT5 + LoRA)

```bash
.venv/bin/python models/neural/train.py \
  --config configs/default.yaml \
  --train-file data/parallel/train.jsonl \
  --val-file data/parallel/val.jsonl
```

### F) Neural evaluation

```bash
.venv/bin/python models/neural/evaluate.py \
  --model-path results/neural_checkpoints/best_model \
  --test-file data/parallel/test_gold.jsonl \
  --output results/neural_scores.json
```

### G) Zero-shot comparison

```bash
.venv/bin/python models/zeroshot/llm_simplifier.py \
  --test-file data/parallel/test_gold.jsonl \
  --output results/zeroshot_scores.json
```

### H) Faithfulness and hallucination analysis

```bash
.venv/bin/python evaluation/faithfulness_checker.py \
  --input data/parallel/test_gold.jsonl \
  --output results/faithfulness_analysis.json

.venv/bin/python evaluation/hallucination_detector.py \
  --input data/parallel/test_gold.jsonl \
  --output results/hallucination_analysis.json
```

### I) Generate comparison report

```bash
.venv/bin/python evaluation/comparison_report.py \
  --results-dir results \
  --output results/comparison_report.md
```

## Run the Web App

```bash
.venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8003
```

Open:

- UI: `http://127.0.0.1:8003/`
- Stats API: `http://127.0.0.1:8003/api/stats`

## API Endpoints

- `GET /`  
  Serves web UI.

- `POST /api/simplify`  
  Simplifies input text with selected baseline models and returns basic reliability metrics.

- `POST /api/analyze`  
  Returns text complexity/jargon analysis.

- `GET /api/stats`  
  Returns dataset and model result snapshot from `data/` and `results/`.

- `GET /api/paragraphs?limit=20&offset=0`  
  Returns extracted paragraph records for inspection.

## Current Pilot Results (from `results/`)

- Baseline (TF-IDF / TextRank):
  - ROUGE-1: `0.7647`
  - ROUGE-2: `0.6212`
  - ROUGE-L: `0.7647`
  - BLEU: `0.2534`
- Neural (mT5 + LoRA, pilot run):
  - ROUGE-1: `0.0348`
  - ROUGE-2: `0.0000`
  - ROUGE-L: `0.0348`
  - BLEU: `0.0000`
- Zero-shot (OpenRouter run):
  - ROUGE-1: `0.2414`
  - ROUGE-2: `0.1865`
  - ROUGE-L: `0.2381`
  - BLEU: `0.0350`

These are interim experiment outputs on the current small pilot split and should not be interpreted as final benchmark conclusions.

## Notes and Limitations

- The current `test_gold` is small; expand and manually review for stronger claims.
- Faithfulness is critical in legal text simplification; always inspect qualitative failures.
- API-keyless fallback in zero-shot mode is only for workflow continuity, not for scientific comparison.

## License

MIT (see `LICENSE`).

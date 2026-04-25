# Evaluation Table (Current + To-Be-Filled)

| Experiment ID | Method Type | Model/Approach | Adaptation | Dataset Split | ROUGE-1 | ROUGE-2 | ROUGE-L | BLEU | Faithfulness | Hallucination Rate | Runtime/Cost | Status |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| E1 | Baseline (Extractive) | TF-IDF | None | `test_gold` (7 samples) | 0.7647 | 0.6212 | 0.7647 | 0.2534 | 0.5458* | 0.0429* | Local CPU | Completed (pilot) |
| E2 | Baseline (Extractive) | TextRank | None | `test_gold` (7 samples) | 0.7647 | 0.6212 | 0.7647 | 0.2534 | 0.5458* | 0.0429* | Local CPU | Completed (pilot) |
| E3 | Neural (Transformer) | mT5-small | LoRA/PEFT (1 epoch) | `test_gold` (7 samples) | 0.0348 | 0.0000 | 0.0348 | 0.0000 | TBD | TBD | Local CPU + HF download | Completed (pilot) |
| E4 | LLM Comparison | Zero-shot LLM | Prompt-based (OpenRouter API) | `test_gold` (7 samples) | 0.2414 | 0.1865 | 0.2381 | 0.0350 | TBD | TBD | API call + local scoring | Completed (pilot) |

## Dataset Snapshot (Current)
| Item | Value |
|---|---:|
| Processed raw documents | 23 |
| Extracted paragraphs | 70 |
| Average complexity | 2.29 |
| Average jargon density | 0.0628 |
| Scrape attempts / success | 11 / 11 |

`*` Faithfulness and hallucination values are dataset-level pilot indicators computed on the current `test_gold`.

## Pilot Dataset Note
- Current `test_gold` was bootstrapped offline from extracted paragraphs (rule-based simplification) because API-based synthetic generation requires an `OPENROUTER_API_KEY`.
- These values are valid for pipeline verification and interim reporting.
- Final report should rerun the same evaluation on manually reviewed gold-standard pairs.
- E4 zero-shot result was produced with real OpenRouter API calls on the same pilot set.

## How to Fill This Table Quickly
1. [x] Create/finalize `data/parallel/test_gold.jsonl`.
2. [x] Run baseline evaluation:
   - `.venv/bin/python models/baseline/evaluate_baselines.py --test-file data/parallel/test_gold.jsonl --output results/baseline_scores.json`
3. [x] Run neural evaluation:
   - `.venv/bin/python models/neural/evaluate.py --model-path results/neural_checkpoints/best_model --test-file data/parallel/test_gold.jsonl --output results/neural_scores.json`
4. [x] Run zero-shot evaluation script (if available in your workflow) and save to `results/zeroshot_scores.json`.
5. [x] Run report generator:
   - `.venv/bin/python evaluation/comparison_report.py --results-dir results --output results/comparison_report.md`

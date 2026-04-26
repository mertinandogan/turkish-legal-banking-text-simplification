# Release Notes - v1.0.0

## Highlights

- Project scope finalized as **Turkish Legal Banking Text Simplification**.
- Legacy MCP-focused code and docs removed from the repository.
- End-to-end pipeline consolidated: data collection, paragraph extraction, baseline/neural/zero-shot evaluation, and web API.
- Documentation rewritten for final academic delivery and reproducibility.

## What is Included

- Data pipeline for BDDK text collection and preprocessing.
- Baseline models: TF-IDF and TextRank.
- Neural evaluation path with mT5 + LoRA structure.
- Zero-shot simplification and comparison flow.
- Evaluation artifacts with pilot metrics and reporting docs.
- FastAPI service and lightweight frontend.

## Quality and Hygiene

- `.gitignore` simplified for this repo's actual scope.
- `.env` remains untracked; `.env.example` contains placeholders only.
- Quick startup workflow added (`make run` / `./scripts/run_api.sh`).
- Security scan completed for accidental API key leakage in tracked files.

## Known Limitations

- Current results are pilot-scale and should be interpreted as interim benchmarks.
- Gold test set coverage is still limited and should be expanded in the next iteration.

## Next Iteration Plan

- Expand real gold-standard test pairs.
- Re-run full comparison on a larger held-out set.
- Freeze reproducible experiment configs for v1.1.0.

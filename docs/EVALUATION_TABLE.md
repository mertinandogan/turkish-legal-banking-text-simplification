# Evaluation Table

Use this table in both midterm and final report to keep experiments consistent.

| Experiment ID | Method Type | Model/Approach | Adaptation | Dataset Split | Metrics | Faithfulness/Hallucination | Runtime/Cost | Notes |
|---|---|---|---|---|---|---|---|---|
| E1 | Baseline (Extractive) | TF-IDF Sentence Scoring | None | Test + Gold Test | ROUGE-1/2/L, BLEU | Faithfulness score, Hallucination rate | Avg inference time/sample | Performance floor |
| E2 | Baseline (Extractive) | TextRank | None | Test + Gold Test | ROUGE-1/2/L, BLEU | Faithfulness score, Hallucination rate | Avg inference time/sample | Graph-based baseline |
| E3 | Neural (Transformer) | mT5 (or selected seq2seq) | LoRA/PEFT | Test + Gold Test | ROUGE-1/2/L, BLEU, (opt. BERTScore) | Faithfulness score, Hallucination rate, Consistency | Train time + inference time | Main proposed model |
| E4 | LLM Comparison | Zero-shot Prompt-based LLM | Prompting | Test + Gold Test | ROUGE-1/2/L, BLEU, (opt. BERTScore) | Faithfulness score, Hallucination rate, Consistency | API latency/cost per sample | Practical comparison |

## Minimum Reporting Rules
- Report at least two core metrics (ROUGE + BLEU recommended).
- Always include faithfulness and hallucination-focused analysis.
- Include short qualitative error analysis with sample outputs.
- For fairness, keep evaluation split and prompt constraints consistent across methods.

## Suggested Result Summary Table (Fill-In)
| Method | ROUGE-L | BLEU | Faithfulness | Hallucination Rate | Avg Inference Time | Comment |
|---|---:|---:|---:|---:|---:|---|
| TF-IDF |  |  |  |  |  |  |
| TextRank |  |  |  |  |  |  |
| LoRA Model |  |  |  |  |  |  |
| Zero-shot LLM |  |  |  |  |  |  |

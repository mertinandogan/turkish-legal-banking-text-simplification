# Presentation Flow (Filled Draft)

## Slide 1 - Title
- Turkish Legal Banking Text Simplification
- AYBU Software Engineering / Neural Networks
- Team members + date

## Slide 2 - Problem and Motivation
- Banking legal texts are complex and jargon-heavy.
- Misinterpretation creates compliance and operational risks.
- Goal: simplify text while preserving legal meaning.

## Slide 3 - Task Definition
- **Input:** complex Turkish legal/banking paragraph
- **Output:** simpler, readable text with legal faithfulness
- Success criteria: readability + semantic/legal preservation

## Slide 4 - Dataset
- Source: BDDK public documents
- Current status:
  - 23 processed documents
  - 70 extracted paragraphs
  - avg complexity: 2.29
  - avg jargon density: 0.0628
- Gold parallel test set: in progress (manual verification)

## Slide 5 - Baselines (Generation-Aligned)
- TF-IDF extractive summarization
- TextRank extractive summarization
- Rationale: generation task -> extractive baselines are methodologically stronger than LogReg/SVM for this scope

## Slide 6 - Proposed Neural Method
- Model: mT5-small (seq2seq)
- Adaptation: LoRA / PEFT
- Compute-aware training setup

## Slide 7 - Zero-shot Comparison
- Prompt-based LLM generation
- Same input/output schema and same evaluation split
- Compare quality vs cost/runtime

## Slide 8 - Evaluation Plan
- ROUGE-1/2/L
- BLEU
- Faithfulness and hallucination metrics
- Qualitative error analysis with example outputs

## Slide 9 - Interim Results
- Data pipeline complete
- Baseline pilot metrics (current `test_gold`, n=7):
  - TextRank: R-1 0.7647, R-2 0.6212, R-L 0.7647, BLEU 0.2534
  - TF-IDF: R-1 0.7647, R-2 0.6212, R-L 0.7647, BLEU 0.2534
  - Faithfulness (avg): 0.5458
  - Hallucination score (avg): 0.0429
- Neural + zero-shot metrics: `TBD` (next experiment stage)
- Show one sample input-output from demo API

## Slide 10 - Error Analysis (Template)
- Case A: over-compression
- Case B: terminology loss
- Case C: potential hallucination / semantic drift

## Slide 11 - Limitations and Ethics
- Limited parallel legal data
- Potential bias and reliability limits
- Human-in-the-loop required for legal usage

## Slide 12 - Conclusion and Roadmap
- What is ready: dataset pipeline + model plan + evaluation framework
- Next: finalize gold set, run all experiments, deliver comparative results

## Optional Demo (2 min)
- `/` web interface input
- `/api/simplify` output
- brief mention of future evaluation dashboard

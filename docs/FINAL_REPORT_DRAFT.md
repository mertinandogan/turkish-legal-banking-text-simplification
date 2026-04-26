# Turkish Legal Banking Text Simplification: A Comparative Study on Summarization and Simplification

## Abstract
This project studies automatic simplification of Turkish banking regulations into plain language while preserving legal meaning. We frame the task as legal-domain text generation and compare generation-aligned extractive baselines (TF-IDF, TextRank) with a Transformer-based abstractive model (mT5 + LoRA) and a zero-shot LLM approach. The current dataset pipeline has produced 23 source documents and 70 complex legal paragraphs. Final quantitative results (ROUGE, BLEU, faithfulness, hallucination) are reported as ongoing (`TBD`) because the parallel gold test split and full experiment cycle are still being completed.

## 1. Introduction
Banking regulations are generally difficult to read due to legal jargon and long sentence structures. This increases misunderstanding risk for consumers and entry-level employees. In a legal-banking context, wording errors may lead to operational and compliance issues. Therefore, simplification systems must optimize readability without changing legal consequences.

### 1.1 Problem Statement
- **Input:** Complex Turkish banking/legal paragraph.
- **Output:** Simplified Turkish paragraph preserving legal intent and critical terms.

### 1.2 Contributions
- Domain-specific Turkish legal text collection and paragraph extraction pipeline.
- Generation-oriented baseline design (TF-IDF and TextRank extractive summarization).
- Planned neural adaptation using LoRA over a seq2seq model (mT5).
- Evaluation framework including faithfulness and hallucination analysis.

## 2. Related Work (Short)
- Transformer-based summarization/simplification methods in low-resource settings.
- Parameter-efficient tuning (LoRA/PEFT) for smaller compute budgets.
- Reliability-focused evaluation in legal generation (faithfulness, hallucination).

## 3. Dataset and Preprocessing
### 3.1 Source
Publicly available BDDK documents.

### 3.2 Current Data Status
- Documents processed: **23**
- Total extracted paragraphs: **70**
- Average complexity score: **2.29**
- Average jargon density: **0.0628**
- Raw scraping attempts: 11 / successful: 11

### 3.3 Preprocessing
- Raw document retrieval and normalization.
- Paragraph extraction with complexity/jargon filters.
- Planned parallel pair creation (`complex -> simple`) with synthetic generation + manual verification.
- Planned split: train/validation/test (`test_gold` manually verified subset).

### 3.4 Data Challenges
- Scarcity of Turkish domain-specific parallel legal corpora.
- High risk of semantic drift during simplification.
- Need for careful human validation on legal outputs.

## 4. Methodology
### 4.1 Baselines (Generation-Aligned)
- **TF-IDF extractive summarizer**
- **TextRank extractive summarizer**

Why this baseline choice: The task is text generation/simplification, so extractive summarization provides a better methodological floor than classification baselines (LogReg/SVM), which target a different task family.

### 4.2 Neural Method
- Base model: **google/mt5-small** (planned default)
- Adaptation: **LoRA/PEFT**
- Planned training setup:
  - epochs: 5
  - batch size: 8
  - learning rate: 3e-4
  - gradient accumulation: 4

### 4.3 Zero-shot Comparison
- Prompt-based generation using external LLM.
- Same evaluation split and metrics for fair comparison.

## 5. Experimental Setup
- Evaluation split: `data/parallel/test_gold.jsonl` (`TBD`, being finalized)
- Metrics:
  - ROUGE-1 / ROUGE-2 / ROUGE-L
  - BLEU
  - Faithfulness
  - Hallucination rate
- Error analysis over representative samples.

## 6. Results (Current Status)
### 6.1 Quantitative Results
Interim pilot results were generated on a bootstrapped `test_gold` set (7 samples):

- **TextRank baseline**
  - ROUGE-1: 0.7647
  - ROUGE-2: 0.6212
  - ROUGE-L: 0.7647
  - BLEU: 0.2534

- **TF-IDF baseline**
  - ROUGE-1: 0.7647
  - ROUGE-2: 0.6212
  - ROUGE-L: 0.7647
  - BLEU: 0.2534

- **Reliability indicators** (dataset-level, pilot):
  - Avg faithfulness score: 0.5458
  - Avg hallucination score: 0.0429
  - Number hallucination count: 0/7
  - Avg term preservation: 1.0

These are interim pipeline-validation numbers. Final benchmark values will be reported after API-based synthetic generation and manual gold review.

### 6.2 Expected Comparison Axes
- Quality: ROUGE/BLEU
- Reliability: faithfulness + hallucination
- Efficiency: runtime/cost for local model vs zero-shot API

## 7. Discussion (Interim)
The pipeline is stable for data collection, extraction, and baseline evaluation. The current pilot results confirm that:
- metric computation works end-to-end,
- comparison/report generation is reproducible,
- faithfulness/hallucination analysis is integrated.

The next critical step is replacing the offline bootstrapped labels with API-generated + manually reviewed gold data and rerunning all experiments.

## 8. Limitations and Ethical Considerations
- Legal simplification may introduce unintended meaning shifts.
- Dataset size is currently limited.
- Domain bias may exist due to source distribution.
- Model outputs should support, not replace, expert legal review.

## 9. Conclusion and Next Steps
This project establishes a reproducible framework for Turkish banking regulation simplification. Immediate next steps:
1. Finalize `test_gold` parallel set.
2. Run baseline and neural evaluations.
3. Produce full comparison report with error analysis.

## References
`TBD` (to be finalized in citation format required by course).

## Individual Contribution Statement
- Member 1: Data collection and preprocessing
- Member 2: Baseline and neural experimentation
- Member 3: Evaluation, reporting, and presentation

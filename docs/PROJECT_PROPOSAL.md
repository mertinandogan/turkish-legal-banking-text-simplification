# Neural Simplification of Banking Regulations

## 1) Project Title
Neural Simplification of Banking Regulations: A Comparative Study on Legal Text Summarization and Simplification

## 2) Problem Definition
Banking regulations and legal frameworks are usually written in highly complex, jargon-heavy language. This makes them difficult to understand for standard consumers and entry-level bank employees, increasing the risk of misinterpretation.

The objective of this project is to automatically simplify and summarize complex legal banking texts into plain, understandable language while preserving critical legal meaning.

## 3) Dataset
- **Source:** Publicly available Turkish banking regulations (BDDK guidelines).
- **Structure:** A corpus of complex legal paragraphs paired with simplified versions.
- **Data strategy:** Since large Turkish parallel corpora are limited, part of the dataset will be synthetically simplified using a strong LLM and then manually verified.
- **Gold standard:** A manually validated test subset will be maintained as a gold-standard benchmark.

### Key Challenges
- Preserving legal accuracy while reducing linguistic complexity.
- Handling low-resource, domain-specific parallel data in Turkish.

## 4) Planned Methods

### Baseline
- Extractive summarization with traditional NLP methods:
  - TextRank
  - TF-IDF sentence scoring

These establish a performance floor and are academically aligned with generation-oriented tasks.
Instead of classification-oriented baselines such as Logistic Regression or SVM, this project prioritizes
extractive summarization baselines because the target task is simplification/summarization generation.

### Advanced Neural Method
- Abstractive sequence-to-sequence summarization/simplification.
- Candidate pretrained models:
  - mT5
  - BART (or Turkish-capable variants)
- Fine-tuning strategy:
  - Parameter-Efficient Fine-Tuning (LoRA) to fit compute constraints.

### Comparative Analysis
- Compare fine-tuned model outputs with a zero-shot prompt-based LLM approach.
- Focus on quality, efficiency, and legal reliability.

## 5) Expected Outcomes
- A working abstractive simplification model for legal banking documents.
- Quantitative evaluation with:
  - ROUGE
  - BLEU
- Targeted error analysis on:
  - Hallucination risk
  - Faithfulness to source legal meaning

In this domain, semantic drift that changes legal consequences is considered a critical failure.

## 6) Minimal Execution Roadmap
1. Collect and clean BDDK source documents.
2. Extract paragraph-level samples and compute complexity metadata.
3. Build train/validation/test splits, with a manually reviewed gold test set.
4. Train baseline extractive methods and record benchmark metrics.
5. Fine-tune a seq2seq model with LoRA.
6. Run zero-shot LLM comparison.
7. Evaluate with ROUGE, BLEU, faithfulness, and hallucination checks.
8. Perform qualitative error analysis and report findings.

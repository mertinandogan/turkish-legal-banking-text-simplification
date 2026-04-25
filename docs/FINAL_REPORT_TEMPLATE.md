# Final Report Template

## Title
Neural Simplification of Banking Regulations: A Comparative Study on Legal Text Summarization and Simplification

## Abstract
- Problem and motivation (2-3 sentences)
- Method summary (baseline + LoRA + zero-shot)
- Main findings with key metrics
- Practical implication for legal banking text accessibility

## 1. Introduction
### 1.1 Background
- Why legal banking texts are hard to understand
- Risks of misinterpretation in banking/legal workflows

### 1.2 Problem Statement
- Input: complex Turkish legal paragraph
- Output: simplified but legally faithful paragraph

### 1.3 Contributions
- Domain-specific Turkish legal simplification dataset pipeline
- Strong extractive baselines for generation task
- LoRA-based neural simplification model
- Faithfulness/hallucination-centered analysis

## 2. Related Work
- Legal text simplification
- Turkish low-resource NLP for legal/financial domains
- Transformer adaptation (PEFT/LoRA)
- Hallucination and faithfulness evaluation in generation

## 3. Dataset and Preprocessing
### 3.1 Data Source
- BDDK public documents, scope, collection method

### 3.2 Dataset Construction
- Paragraph extraction rules
- Parallel pair generation approach
- Synthetic simplification and manual verification protocol

### 3.3 Splits and Statistics
- Train/validation/test sizes
- Gold-standard test subset details
- Average length, complexity, jargon density

### 3.4 Data Challenges
- Parallel data scarcity
- Terminology ambiguity
- Legal context sensitivity

## 4. Methodology
### 4.1 Baseline Methods (Generation-Aligned)
- TF-IDF extractive summarizer
- TextRank extractive summarizer
- Why extractive baselines are preferred over LogReg/SVM for this task

### 4.2 Neural Method
- Selected seq2seq model (e.g., mT5)
- LoRA configuration and rationale
- Training setup (epochs, batch size, LR, hardware)

### 4.3 Zero-shot LLM Comparison
- Prompt template
- Decoding setup
- Cost/latency considerations

## 5. Experimental Setup
- Evaluation protocol
- Reproducibility settings (seeds, versions)
- Inference settings for all methods

## 6. Results
### 6.1 Automatic Metrics
- ROUGE (1/2/L), BLEU (and optional BERTScore)
- Faithfulness/hallucination metrics

### 6.2 Comparative Analysis
- Baseline vs LoRA model vs zero-shot LLM
- Quality-efficiency trade-off

### 6.3 Error Analysis
- Typical successful cases
- Failure modes (hallucination, legal meaning drift, over-compression)
- Example outputs with short commentary

## 7. Discussion
- Interpretation of findings
- Why some methods perform better
- Domain-specific implications

## 8. Limitations and Ethical Considerations
- Data bias and representativeness
- Reliability and fairness concerns
- Misuse risks
- Human-in-the-loop requirement for legal contexts

## 9. Conclusion and Future Work
- Summary of key outcomes
- Next steps (larger gold set, ablation, robustness, explainability)

## References
- Use a consistent citation style (APA/IEEE)

## Appendix
- Hyperparameter tables
- Prompt templates
- Additional examples

## Individual Contribution Statement
- Member A:
- Member B:
- Member C:

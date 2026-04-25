# Presentation Flow (10-12 Slides)

## Slide 1 - Title
- Project title
- Course, university, team members

## Slide 2 - Problem and Motivation
- Why banking legal texts are complex
- Real impact of misunderstanding
- Project objective

## Slide 3 - Task Definition
- Input/Output formulation
- Success criteria: simplification + legal faithfulness

## Slide 4 - Dataset
- Data source (BDDK)
- Dataset construction pipeline
- Train/val/test + gold-standard subset
- Main data challenges

## Slide 5 - Baselines
- TF-IDF extractive summarization
- TextRank extractive summarization
- Why extractive baselines fit generation tasks better than LogReg/SVM

## Slide 6 - Proposed Neural Method
- Model choice (e.g., mT5)
- LoRA/PEFT strategy
- Training setup summary

## Slide 7 - Comparison Method
- Zero-shot LLM setup
- Prompt design and inference settings

## Slide 8 - Evaluation Design
- Metrics: ROUGE, BLEU, faithfulness, hallucination
- Error analysis protocol
- (If classification subtask exists: confusion matrix note)

## Slide 9 - Main Results
- Table/chart: baseline vs LoRA vs zero-shot
- Best model and margins

## Slide 10 - Error Analysis
- 2-3 representative examples
- Hallucination and meaning-drift cases

## Slide 11 - Limitations and Ethics
- Bias, reliability, misuse risk
- Human review requirement

## Slide 12 - Conclusion and Future Work
- What worked
- What remains
- Practical deployment direction

## Optional Demo (2-3 min)
- Brief system walkthrough:
  - Input legal paragraph
  - Model outputs
  - Metric/quality view

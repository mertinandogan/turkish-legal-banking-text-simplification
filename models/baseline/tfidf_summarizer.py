"""
TF-IDF Summarizer

Extractive summarization baseline using TF-IDF sentence scoring.
Selects sentences with highest average TF-IDF importance.
"""

import logging
import re
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class TfidfSummarizer:
    """
    TF-IDF-based extractive summarizer for Turkish text.
    
    Scores each sentence by the average TF-IDF weight of its terms
    and selects the highest-scoring sentences.
    """
    
    def __init__(
        self,
        num_sentences: int = 3,
        max_features: int = 10000,
        position_weight: float = 0.1,
    ):
        """
        Initialize TF-IDF summarizer.
        
        Args:
            num_sentences: Number of sentences to extract
            max_features: Maximum vocabulary size for TF-IDF
            position_weight: Weight bonus for sentences at document start/end
        """
        self.num_sentences = num_sentences
        self.max_features = max_features
        self.position_weight = position_weight
        
        self.stop_words = {
            "bir", "bu", "şu", "o", "ve", "ile", "için", "da", "de",
            "den", "dan", "ya", "ye", "mi", "mu", "mı", "mü",
            "ama", "fakat", "ancak", "çünkü", "eğer", "gibi",
            "daha", "en", "çok", "az", "her", "hiç", "bazı",
            "olan", "olarak", "olup", "olduğu", "olması", "olmak",
            "kadar", "sonra", "önce", "arasında", "üzerinde", "altında",
            "tarafından", "nedeniyle", "dolayı", "göre", "karşı",
            "ise", "hem", "ne", "ki", "var", "yok",
        }
    
    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        abbreviations = [
            "Dr", "Prof", "Av", "Md", "Yrd", "Doç", "No", "vb", "vd",
            "vs", "bkz", "a.g.e", "a.g.m", "md", "fk",
        ]
        
        temp = text
        replacements = {}
        for i, abbr in enumerate(abbreviations):
            placeholder = f"__ABR{i}__"
            temp = temp.replace(f"{abbr}.", placeholder)
            replacements[placeholder] = f"{abbr}."
        
        sentences = re.split(r"(?<=[.!?])\s+", temp)
        
        result = []
        for sent in sentences:
            for ph, orig in replacements.items():
                sent = sent.replace(ph, orig)
            sent = sent.strip()
            if len(sent.split()) >= 5:
                result.append(sent)
        
        return result
    
    def _preprocess(self, text: str) -> str:
        """Preprocess for TF-IDF."""
        text = text.lower()
        text = re.sub(r"[^\wçğıiöşüÇĞIİÖŞÜ\s]", " ", text)
        words = text.split()
        words = [w for w in words if w not in self.stop_words and len(w) > 2]
        return " ".join(words)
    
    def _compute_position_scores(self, n_sentences: int) -> np.ndarray:
        """
        Compute position-based scores.
        First and last sentences get higher scores.
        """
        scores = np.zeros(n_sentences)
        for i in range(n_sentences):
            # Higher weight for beginning and end
            if i < 2:
                scores[i] = 1.0 - (i * 0.3)
            elif i >= n_sentences - 2:
                scores[i] = 0.5
            else:
                scores[i] = 0.2
        return scores
    
    def summarize(self, text: str, num_sentences: Optional[int] = None) -> str:
        """
        Generate an extractive summary using TF-IDF scoring.
        
        Args:
            text: Input text to summarize
            num_sentences: Override default number of sentences
            
        Returns:
            Extractive summary
        """
        n = num_sentences or self.num_sentences
        sentences = self._split_sentences(text)
        
        if len(sentences) <= n:
            return text
        
        # Preprocess sentences
        preprocessed = [self._preprocess(s) for s in sentences]
        
        # Filter empty preprocessed sentences
        valid_indices = [i for i, p in enumerate(preprocessed) if p.strip()]
        if len(valid_indices) <= n:
            return " ".join(sentences[:n])
        
        valid_preprocessed = [preprocessed[i] for i in valid_indices]
        
        # Compute TF-IDF
        try:
            vectorizer = TfidfVectorizer(max_features=self.max_features)
            tfidf_matrix = vectorizer.fit_transform(valid_preprocessed)
        except ValueError:
            return " ".join(sentences[:n])
        
        # Score each sentence by average TF-IDF weight
        tfidf_scores = np.array(tfidf_matrix.mean(axis=1)).flatten()
        
        # Normalize
        if tfidf_scores.max() > 0:
            tfidf_scores = tfidf_scores / tfidf_scores.max()
        
        # Add position weighting
        position_scores = self._compute_position_scores(len(valid_indices))
        
        # Combined score
        combined_scores = (
            tfidf_scores * (1 - self.position_weight)
            + position_scores * self.position_weight
        )
        
        # Select top sentences
        top_indices = np.argsort(combined_scores)[::-1][:n]
        
        # Map back to original indices and sort by position
        original_indices = sorted([valid_indices[i] for i in top_indices])
        
        summary_sentences = [sentences[i] for i in original_indices]
        return " ".join(summary_sentences)
    
    def summarize_to_target_length(
        self,
        text: str,
        target_ratio: float = 0.5,
    ) -> str:
        """Summarize to approximately target_ratio of original length."""
        sentences = self._split_sentences(text)
        n = max(1, int(len(sentences) * target_ratio))
        return self.summarize(text, num_sentences=n)

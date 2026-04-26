"""
TextRank Summarizer

Extractive summarization baseline using the TextRank algorithm.
Implements graph-based sentence ranking for Turkish legal text.
"""

import logging
import re
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

logger = logging.getLogger(__name__)


class TextRankSummarizer:
    """
    TextRank-based extractive summarizer for Turkish text.
    
    Uses TF-IDF vectors for sentence similarity and PageRank
    for sentence importance ranking.
    """
    
    def __init__(
        self,
        num_sentences: int = 3,
        damping_factor: float = 0.85,
        max_iter: int = 100,
        similarity_threshold: float = 0.1,
    ):
        """
        Initialize TextRank summarizer.
        
        Args:
            num_sentences: Number of sentences to extract
            damping_factor: PageRank damping factor
            max_iter: Maximum PageRank iterations
            similarity_threshold: Minimum similarity to create graph edge
        """
        self.num_sentences = num_sentences
        self.damping_factor = damping_factor
        self.max_iter = max_iter
        self.similarity_threshold = similarity_threshold
        
        # Turkish stop words (common ones)
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
        """Split text into sentences, handling Turkish abbreviations."""
        # Protect common abbreviations
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
        
        # Split on sentence-ending punctuation
        sentences = re.split(r"(?<=[.!?])\s+", temp)
        
        # Restore abbreviations and clean
        result = []
        for sent in sentences:
            for ph, orig in replacements.items():
                sent = sent.replace(ph, orig)
            sent = sent.strip()
            if len(sent.split()) >= 5:  # Minimum word count
                result.append(sent)
        
        return result
    
    def _preprocess(self, text: str) -> str:
        """Preprocess text for TF-IDF vectorization."""
        text = text.lower()
        # Remove punctuation but keep Turkish characters
        text = re.sub(r"[^\wçğıiöşüÇĞIİÖŞÜ\s]", " ", text)
        # Remove stop words
        words = text.split()
        words = [w for w in words if w not in self.stop_words and len(w) > 2]
        return " ".join(words)
    
    def summarize(self, text: str, num_sentences: Optional[int] = None) -> str:
        """
        Generate an extractive summary using TextRank.
        
        Args:
            text: Input text to summarize
            num_sentences: Override default number of sentences
            
        Returns:
            Extractive summary (concatenated top sentences)
        """
        n = num_sentences or self.num_sentences
        sentences = self._split_sentences(text)
        
        if len(sentences) <= n:
            return text
        
        # Preprocess for TF-IDF
        preprocessed = [self._preprocess(s) for s in sentences]
        
        # Build TF-IDF similarity matrix
        try:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(preprocessed)
            similarity_matrix = cosine_similarity(tfidf_matrix)
        except ValueError:
            # If TF-IDF fails (e.g., all stop words), return first sentences
            return " ".join(sentences[:n])
        
        # Build graph
        graph = nx.Graph()
        for i in range(len(sentences)):
            graph.add_node(i)
        
        for i in range(len(sentences)):
            for j in range(i + 1, len(sentences)):
                sim = similarity_matrix[i][j]
                if sim > self.similarity_threshold:
                    graph.add_edge(i, j, weight=sim)
        
        # Run PageRank
        try:
            scores = nx.pagerank(
                graph,
                alpha=self.damping_factor,
                max_iter=self.max_iter,
            )
        except nx.PowerIterationFailedConvergence:
            # Fallback to degree centrality
            scores = nx.degree_centrality(graph)
        
        # Select top sentences (maintain original order)
        ranked_indices = sorted(scores, key=scores.get, reverse=True)[:n]
        ranked_indices.sort()  # Maintain original order
        
        summary_sentences = [sentences[i] for i in ranked_indices]
        return " ".join(summary_sentences)
    
    def summarize_to_target_length(
        self,
        text: str,
        target_ratio: float = 0.5,
    ) -> str:
        """
        Summarize to approximately target_ratio of original length.
        
        Args:
            text: Input text
            target_ratio: Target length as ratio of original (0.0 - 1.0)
            
        Returns:
            Summary text
        """
        sentences = self._split_sentences(text)
        n = max(1, int(len(sentences) * target_ratio))
        return self.summarize(text, num_sentences=n)

"""
Tag recommendation system based on similarity and co-occurrence.
"""

from typing import Dict, List, Set, Tuple


class TagRecommender:
    """Recommends tags based on keyword similarity and co-occurrence."""

    def __init__(self, tag_manager):
        """Initialize recommender."""
        self.tag_manager = tag_manager

    def recommend_by_similarity(
        self, keyword: str, top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """Recommend tags by keyword similarity."""
        recommendations = []
        keyword_lower = keyword.lower()

        for tag in self.tag_manager.get_all_tags():
            score = self._similarity_score(keyword_lower, tag.name.lower())
            if score > 0:
                recommendations.append((tag.name, score))

        return sorted(recommendations, key=lambda x: -x[1])[:top_n]

    def recommend_by_cooccurrence(
        self, tag_name: str, top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """Recommend tags by co-occurrence."""
        tag = self.tag_manager.get_tag(tag_name)
        if not tag or not tag.cooccurrence:
            return []

        recommendations = [
            (name, count) for name, count in tag.cooccurrence.items()
        ]
        return sorted(recommendations, key=lambda x: -x[1])[:top_n]

    def recommend_for_task(
        self, task_text: str, existing_tags: List[str], top_n: int = 3
    ) -> List[Tuple[str, float]]:
        """Recommend tags for a task based on keywords and context."""
        keywords = self._extract_keywords(task_text)
        candidates: Dict[str, float] = {}

        # Score by keyword similarity
        for keyword in keywords:
            similar = self.recommend_by_similarity(keyword, top_n=10)
            for tag_name, score in similar:
                if tag_name not in existing_tags:
                    candidates[tag_name] = candidates.get(tag_name, 0) + score * 0.7

        # Score by co-occurrence
        for existing_tag in existing_tags:
            cooccurring = self.recommend_by_cooccurrence(existing_tag, top_n=10)
            for tag_name, count in cooccurring:
                if tag_name not in existing_tags:
                    candidates[tag_name] = candidates.get(tag_name, 0) + count * 0.3

        return sorted(candidates.items(), key=lambda x: -x[1])[:top_n]

    def _similarity_score(self, s1: str, s2: str) -> float:
        """Calculate similarity score using Levenshtein-like approach."""
        if s1 == s2:
            return 1.0
        if s1 in s2 or s2 in s1:
            return 0.8
        # Substring match
        if len(s1) > 2 and s1 in s2:
            return 0.7
        if len(s2) > 2 and s2 in s1:
            return 0.7
        # Character overlap
        set1 = set(s1)
        set2 = set(s2)
        if not set1 or not set2:
            return 0
        overlap = len(set1 & set2) / len(set1 | set2)
        return overlap if overlap > 0.3 else 0

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction: split on spaces/punctuation
        import re

        words = re.findall(r"\b\w+\b", text.lower())
        # Filter common words
        common = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "is",
            "was",
            "are",
        }
        return [w for w in words if w not in common and len(w) > 2]

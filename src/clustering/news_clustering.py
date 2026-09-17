import re
from typing import Dict, List, Any, Set, Tuple
from src.utils.logging import setup_logger

logger = setup_logger("news_clustering")

COMMON_STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "up", "about", "into", "over", "after", "and", "or", "but", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "new",
    "how", "why", "what", "which", "who", "whom", "this", "that", "these", "those",
    "ai", "artificial", "intelligence"
}


class NewsEventClusterer:
    """
    Groups distinct news articles reporting on the same underlying news event.
    Deterministic event clustering based on title token overlap and entity similarity.
    Assigns event_cluster_id without deleting underlying article records.
    """

    @staticmethod
    def extract_keywords(title: str) -> Set[str]:
        """Extracts significant non-stopword tokens from article title."""
        tokens = re.findall(r"\b[a-zA-Z0-9]{3,}\b", title.lower())
        return {t for t in tokens if t not in COMMON_STOPWORDS}

    def calculate_jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """Calculates Jaccard similarity index between token sets."""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / float(union) if union > 0 else 0.0

    def cluster_articles(self, articles: List[Dict[str, Any]], similarity_threshold: float = 0.45) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Groups articles into event clusters.
        Returns: Tuple[updated_articles, cluster_summary_list]
        """
        clusters: List[Dict[str, Any]] = []  # List of {cluster_id, title, article_ids, keywords}
        updated_articles = [dict(a) for a in articles]

        cluster_index = 1

        for article in updated_articles:
            title = article.get("title") or article.get("name") or ""
            art_id = article["id"]
            keywords = self.extract_keywords(title)

            matched_cluster_id = None

            # Attempt matching existing clusters
            for cluster in clusters:
                sim = self.calculate_jaccard_similarity(keywords, cluster["keywords"])
                if sim >= similarity_threshold:
                    matched_cluster_id = cluster["cluster_id"]
                    cluster["article_ids"].append(art_id)
                    # Expand cluster keyword set
                    cluster["keywords"].update(keywords)
                    break

            if not matched_cluster_id:
                # Create a new event cluster
                matched_cluster_id = f"cluster:ev-{cluster_index:03d}"
                clusters.append({
                    "cluster_id": matched_cluster_id,
                    "representative_headline": title,
                    "article_ids": [art_id],
                    "keywords": set(keywords),
                    "created_at": article.get("published_at")
                })
                cluster_index += 1

            article["event_cluster_id"] = matched_cluster_id

        # Convert set of keywords to list for JSON serialization
        cluster_summary_list = []
        for c in clusters:
            cluster_summary_list.append({
                "event_cluster_id": c["cluster_id"],
                "headline": c["representative_headline"],
                "article_count": len(c["article_ids"]),
                "article_ids": c["article_ids"],
                "keywords": sorted(list(c["keywords"]))
            })

        logger.info(f"Grouped {len(articles)} articles into {len(clusters)} distinct event clusters.")
        return updated_articles, cluster_summary_list

import logging
from typing import Any, Dict, List, Tuple

from sklearn.feature_extraction.text import CountVectorizer

logger = logging.getLogger(__name__)


class TopicAnalyzer:
    def __init__(self, embedding_model="paraphrase-multilingual-MiniLM-L12-v2"):
        """Initialize a BERTopic model tuned for Vietnamese text."""
        try:
            try:
                from bertopic import BERTopic
                from bertopic.representation import KeyBERTInspired
                from hdbscan import HDBSCAN
                from sentence_transformers import SentenceTransformer
                from umap import UMAP
            except ModuleNotFoundError as exc:
                raise ModuleNotFoundError(
                    "Missing optional topic modeling dependencies. Install: "
                    "bertopic sentence-transformers umap-learn hdbscan"
                ) from exc

            logger.info(f"Loading embedding model: {embedding_model}")
            self.embedding_model = SentenceTransformer(embedding_model)

            # n_jobs=1 avoids UMAP process hangs seen on Windows.
            self.umap_model = UMAP(
                n_neighbors=15,
                n_components=5,
                min_dist=0.0,
                metric='cosine',
                random_state=42,
                n_jobs=1,
            )

            # HDBSCAN is stricter than KMeans here and avoids oversized clusters.
            self.hdbscan_model = HDBSCAN(
                min_cluster_size=5,
                min_samples=2,
                metric='euclidean',
                cluster_selection_method='eom',
                prediction_data=True,
            )

            # Keep the default tokenizer and use n-grams to capture short phrases.
            vn_stopwords = [
                "c\u1ee7a", "b\u1ecb", "v\u00e0", "t\u1ea1i", "l\u00e0",
                "trong", "c\u00f3", "cho", "v\u1edbi", "\u0111\u00e3",
                "nh\u01b0ng", "t\u1eeb", "m\u1ed9t", "nh\u1eefng",
                "ng\u01b0\u1eddi", "\u0111\u1ec3", "n\u00e0y", "khi",
                "\u0111\u1ebfn", "c\u00e1c", "nh\u01b0", "v\u1ec1",
                "\u0111\u01b0\u1ee3c", "s\u1ebd", "s\u1ef1", "kh\u00f4ng",
                "th\u00ec", "c\u0169ng", "nhi\u1ec1u", "h\u01a1n", "sau",
                "\u0111ang", "l\u1ea1i", "\u0111\u00f3", "ph\u1ea3i",
                "n\u0103m", "ng\u00e0y", "l\u00e0m", "nay", "v\u00e0o",
                "ra", "\u0111\u1ed3ng",
            ]

            self.vectorizer_model = CountVectorizer(
                stop_words=vn_stopwords,
                ngram_range=(1, 3),
            )

            self.representation_model = KeyBERTInspired()

            self.topic_model = BERTopic(
                embedding_model=self.embedding_model,
                umap_model=self.umap_model,
                hdbscan_model=self.hdbscan_model,
                vectorizer_model=self.vectorizer_model,
                representation_model=self.representation_model,
                language="multilingual",
                verbose=True,
            )
            self.is_fitted = False
            logger.info("TopicAnalyzer initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing TopicAnalyzer: {e}")
            raise

    def extract_hot_topics(self, docs: List[str]) -> Tuple[List[int], Any]:
        """
        Extract topics from a list of documents.

        Returns:
            topics: integer topic IDs assigned to each document.
            probs: topic assignment probabilities, if available.
        """
        if not docs:
            logger.warning("Empty document list provided.")
            return [], None

        logger.info(f"Extracting topics from {len(docs)} documents...")
        topics, probs = self.topic_model.fit_transform(docs)
        self.is_fitted = True
        return topics, probs

    def get_topic_info(self) -> Any:
        """Return extracted topic information as a DataFrame."""
        if not self.is_fitted:
            return None
        return self.topic_model.get_topic_info()

    def get_top_topics(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Return the most frequent non-outlier topics."""
        if not self.is_fitted:
            logger.warning("Topic model has not been fitted yet.")
            return []

        topic_info = self.topic_model.get_topic_info()
        valid_topics = topic_info[topic_info['Topic'] != -1]

        results = []
        for _, row in valid_topics.head(top_n).iterrows():
            topic_id = row['Topic']
            count = row['Count']

            keywords = self.topic_model.get_topic(topic_id)
            if keywords:
                top_words = [kw[0] for kw in keywords[:5]]

                rep_docs = self.topic_model.get_representative_docs(topic_id)
                rep_title = rep_docs[0].replace('\n', ' ').split('.', 1)[0].strip() if rep_docs else ""

                results.append({
                    'topic_id': topic_id,
                    'count': count,
                    'keywords': top_words,
                    'rep_title': rep_title,
                    'name': row.get('Name', ''),
                })

        return results

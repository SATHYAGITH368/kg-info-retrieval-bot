from sentence_transformers import CrossEncoder
import logging
from typing import List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self, model_name: str = 'BAAI/bge-reranker-large'):
        """
        Initialize the Reranker with a specified CrossEncoder model.
        """
        self.reranker_model = None
        try:
            self.config(model_name)
        except Exception as e:
            logger.error(f"Failed to initialize reranker model: {e}")
            raise

    def config(self, model_name: str):
        """
        Load the CrossEncoder model.
        """
        try:
            self.reranker_model = CrossEncoder(model_name)
            logger.info(f"Successfully loaded reranker model: {model_name}")
        except Exception as e:
            logger.error(f"Error loading model '{model_name}': {e}")
            raise RuntimeError(f"Could not load reranker model: {e}")

    def ranker(self, user_query: str, results: List[str], top_k: int) -> Tuple[List[str], List[float]]:
        """
        Re-rank a list of result documents based on their relevance to the user query.
        
        Args:
            user_query (str): The input query.
            results (List[str]): List of document texts.
            top_k (int): Number of top results to return.
        
        Returns:
            Tuple[List[str], List[float]]: Top-k ranked documents and their scores.
        """
        if not self.reranker_model:
            logger.error("Reranker model is not loaded.")
            raise ValueError("Reranker model is not loaded.")

        if not isinstance(results, list) or not all(isinstance(doc, str) for doc in results):
            logger.error("Results should be a list of strings.")
            raise TypeError("Results should be a list of strings.")

        try:
            pairs = [(user_query, doc) for doc in results]
            scores = self.reranker_model.predict(pairs)

            ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
            top_sentences = [doc for doc, _ in ranked[:top_k]]
            top_scores = [score for _, score in ranked[:top_k]]

            return top_sentences, top_scores

        except Exception as e:
            logger.error(f"Error during re-ranking: {e}")
            raise RuntimeError(f"Error during re-ranking: {e}")

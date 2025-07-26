from retrieval.bm_25search1 import BM25SEARCH1
from retrieval.contexual_search import ContexualSearch
#or from retrieval.contexual_search1 import Contexual
from retrieval.reranking import Reranker

class AgentSkills:
    def __init__(self):
        self.bm25 = BM25SEARCH1()
        self.embedding = ContexualSearch()
        self.reranker = Reranker(model_name="BAAI/bge-reranker-large")

        # Index PDFs for BM25 at startup
        self.bm25.ingest_folder_of_pdfs(
            folder_path="/Users/sathya/Downloads/unstructured_scraped/pdfs",
            type_of_chunk="sentence",
            sizeofchunk=1
        )

    def search_context(self, query: str, top_k: int = 5, method: str = "embedding", rerank: bool = True):
        if method.lower() == "bm25":
            results = self.bm25.search(query)
            # BM25 returns a list of strings, convert to dicts for reranker
            result_texts = results
        else:
            results = self.embedding.search(query, top_k=top_k)
            # Embedding search returns list of dicts with 'chunk' and 'score'
            result_texts = [
                doc['chunk'] if isinstance(doc, dict) and 'chunk' in doc else doc
                for doc in results
            ]

        # Always rerank, output as list of dicts with 'chunk' and 'score'
        reranked, scores = self.reranker.ranker(query, result_texts, top_k)
        return [
            {"chunk": chunk, "score": score}
            for chunk, score in zip(reranked, scores)
        ]
from retrieval.abstract_contexual import Contexual
from haystack.document_stores import ElasticsearchDocumentStore
from haystack.nodes import BM25Retriever, PreProcessor
from haystack import Document
import os


class BM25SEARCH(Contexual):
    def __init__(self):
       self.elasticsearch_doc_store = ElasticsearchDocumentStore(
    host="localhost",
    port=9201,   # 👈 Change this!
    username="elastic",
    password="veOaGJlE2Qvx2punjE=B",
    scheme="https",
    verify_certs=True,
    ca_certs="http_ca.crt",
    index="bm25search"
)

    

    def encode_query(self):
        pass

    def perform_retrieval(self):
        pass

    def handle_results(self, text, type_of_chunk, sizeofchunk):
        doc = Document(content=text)

        preprocessor = PreProcessor(
            split_by=type_of_chunk.lower(), 
            split_length=sizeofchunk,
            split_overlap=0,
            split_respect_sentence_boundary=False 
        )

        docs = preprocessor.process([doc])
        self.elasticsearch_doc_store.write_documents(docs)

    def search(self, search_query: str):
        retriever = BM25Retriever(document_store=self.elasticsearch_doc_store)
        results = retriever.retrieve(query=search_query, top_k=10)
        return [doc.content for doc in results]

    def parse_query_input(self, content, type_of_chunk, sizeofchunk):
        try:
            self.handle_results(content, type_of_chunk, sizeofchunk)
        except Exception as e:
            print(f"Error inserting data: {e}")


if __name__ == "__main__":
    bm25_search = BM25SEARCH()

    text = """
    Artificial Intelligence (AI) has rapidly emerged as a transformative force in virtually every sector of society.
    From healthcare and finance to education and transportation, AI technologies are redefining how we live and work.
    In healthcare, machine learning algorithms are being used to diagnose diseases with remarkable accuracy, often
    outperforming human doctors in specific tasks such as analyzing medical images. In finance, AI systems manage
    high-frequency trading, detect fraudulent transactions, and provide personalized investment advice. The education
    sector has seen a rise in intelligent tutoring systems and automated grading solutions, while self-driving cars
    and smart traffic systems are revolutionizing urban mobility. However, the rapid advancement of AI also raises
    important ethical and social concerns. Issues such as data privacy, algorithmic bias, job displacement, and the
    concentration of power in tech companies have become central topics of public debate. Governments and organizations
    around the world are now grappling with how to regulate AI in a way that fosters innovation while ensuring safety,
    transparency, and fairness. Furthermore, the emergence of generative AI models — capable of creating human-like text,
    images, and even music — is challenging our understanding of creativity and intellectual property. As AI continues to
    evolve, it is critical for policymakers, developers, and society at large to engage in ongoing dialogue to shape its
    development and use responsibly. The future of AI will depend not only on technological breakthroughs but also on our
    ability to align its capabilities with human values and societal goals.
    """

    chunk_type = "sentence"
    chunk_size = 1

    print("Indexing content...")
    bm25_search.parse_query_input(text, chunk_type, chunk_size)

    query = "ethical concerns in AI"
    print(f"\nSearching for: {query}")
    results = bm25_search.search(query)

    print("\nTop matching results:")
    for i, res in enumerate(results, 1):
        print(f"{i}. {res}")
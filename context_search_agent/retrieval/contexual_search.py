import spacy
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain.schema import Document
from ollama import chat
import PyPDF2


class ContexualSearch:
    def __init__(self):
        self.db_url = "postgresql+psycopg2://postgres:sathya@localhost:5432/postgres"
        self.collection_name = "semantra_contextual"
        self.embedding_function = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        self.nlp = spacy.load("en_core_web_sm")

    def chunk_creation(self, content: str, chunk_type: str = "SENTENCE", sizeofchunk: int = 10) -> List[str]:
        chunks = []
        if chunk_type == 'SENTENCE':
            doc = self.nlp(content)
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
            for i in range(0, len(sentences), sizeofchunk):
                chunks.append(" ".join(sentences[i:i + sizeofchunk]))
        elif chunk_type == 'PARAGRAPH':
            chunks = [p.strip() for p in content.split('\n\n') if p.strip()]
        elif chunk_type == 'WORD':
            doc = self.nlp(content)
            words = [token.text for token in doc if token.is_alpha or token.is_digit]
            for i in range(0, len(words), sizeofchunk):
                chunks.append(" ".join(words[i:i + sizeofchunk]))
        else:
            raise ValueError("Invalid chunk_type. Choose from 'SENTENCE', 'PARAGRAPH', or 'WORD'.")
        return chunks

    def contextualize_chunk(self, document: str, chunk: str, name: str, chunk_index: int) -> str:
        try:
            _ = chat(model='llama3', messages=[{'role': 'system', 'content': 'ping'}])
        except Exception:
            print("Loading llama3.2 model... This may take a moment.")

        prompt = f"""
        You are an assistant optimizing text chunks for contextual search.

        Given the full document below, and a specific chunk from it, generate a brief and informative contextual summary
        that situates the chunk within the overall document. This summary should highlight the chunk’s key topic or role
        in the document. Respond ONLY with the improved, contextually enriched chunk text—do NOT add explanations.

        <Document name="{name}">
        {document}
        </Document>

        <Chunk id="{chunk_index}">
        {chunk}
        </Chunk>
        """

        response = chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
        enriched = response['message']['content'].strip()
        return f"[{name} - Chunk {chunk_index}] {enriched}"

    def parse_query_input(self, document_name: str, full_text: str, text_chunks: List[str]) -> None:
        docs = [
            Document(
                page_content=self.contextualize_chunk(full_text, chunk, document_name, idx),
                metadata={"source": document_name}
            )
            for idx, chunk in enumerate(text_chunks)
        ]

        PGVector.from_documents(
            embedding=self.embedding_function,
            documents=docs,
            collection_name=self.collection_name,
            connection_string=self.db_url,
        )
        print(f"Inserted {len(docs)} chunks for document '{document_name}'.")

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        db = PGVector(
            collection_name=self.collection_name,
            connection_string=self.db_url,
            embedding_function=self.embedding_function,
        )
        results = db.similarity_search_with_score(query, k=top_k)
        return [{"chunk": doc.page_content, "score": score} for doc, score in results]

    def ingest_pdfs_from_folder(self, folder_path: str):
        folder = Path(folder_path)
        pdf_files = list(folder.glob("*.pdf"))

        if not pdf_files:
            print("No PDF files found in", folder_path)
            return

        for pdf_file in pdf_files:
            self.ingest_single_pdf(str(pdf_file))

    def ingest_single_pdf(self, pdf_file_path: str):
        pdf_path = Path(pdf_file_path)
        if not pdf_path.exists():
            print(f"File not found: {pdf_file_path}")
            return

        print(f"\nProcessing {pdf_path.name}...")
        full_text = self.extract_text_from_pdf(pdf_path)

        chunks = self.chunk_creation(full_text, chunk_type="SENTENCE", sizeofchunk=2)
        self.parse_query_input(pdf_path.stem, full_text, chunks)

    @staticmethod
    def extract_text_from_pdf(pdf_path: Path) -> str:
        text = ""
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

'''
if __name__ == "__main__":
    search_engine = ContexualSearch()

    # process specific files one by one
    [search_engine.ingest_single_pdf(path) for path in [
        r"/Users/sathya/Downloads/unstructured_scraped/pdfs/INSAT_Product_Version_information_V01.pdf",
        r"/Users/sathya/Downloads/unstructured_scraped/pdfs/Onset%20Prediction%202023.pdf",
        r"/Users/sathya/Downloads/unstructured_scraped/pdfs/Onset%20Prediction%202024.pdf",
        r"/Users/sathya/Downloads/unstructured_scraped/pdfs/sftp-mosdac_0.pdf",
        r"/Users/sathya/Downloads/unstructured_scraped/pdfs/STQC.pdf"
    ]]

    query = "When does the peak of TPW over the Arabian Sea occur in relation to the monsoon onset over Kerala?"
    results = search_engine.search(query)

    print("\nTop Matching Chunks:\n")
    for r in results:
        print(f"Score: {r['score']:.4f}\nChunk: {r['chunk']}\n")
'''
from retrieval.abstract_contexual import Contexual
from rank_bm25 import BM25Okapi
from PyPDF2 import PdfReader
from pathlib import Path

class BM25SEARCH1(Contexual):
    def __init__(self):
        self.corpus = []
        self.tokenized_corpus = []
        self.bm25 = None

    def encode_query(self):
        pass

    def perform_retrieval(self):
        pass    

    def handle_results(self, text, type_of_chunk, sizeofchunk):
     
        if type_of_chunk.lower() == "sentence":
            docs = [s.strip() for s in text.replace('\n', ' ').split('.') if s.strip()]
        elif type_of_chunk.lower() == "paragraph":
            docs = [p.strip() for p in text.split('\n\n') if p.strip()]
        else:
            docs = [text]
        self.corpus.extend(docs)
        self.tokenized_corpus = [doc.split() for doc in self.corpus]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def search(self, search_query: str):
        if not self.bm25:
            return []
        tokenized_query = search_query.split()
        scores = self.bm25.get_scores(tokenized_query)
        ranked = sorted(zip(self.corpus, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked[:10]]

    def parse_query_input(self, content, type_of_chunk, sizeofchunk):
        try:
            self.handle_results(content, type_of_chunk, sizeofchunk)
        except Exception as e:
            print(f"Error inserting data: {e}")

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        text = ""
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def ingest_single_pdf(self, pdf_file_path: str, type_of_chunk: str, sizeofchunk: int):
        pdf_path = Path(pdf_file_path)
        if not pdf_path.exists():
            print(f"File not found: {pdf_file_path}")
            return

        print(f"\nProcessing {pdf_path.name}...")
        full_text = self.extract_text_from_pdf(pdf_path)
        self.parse_query_input(full_text, type_of_chunk, sizeofchunk)

    def ingest_folder_of_pdfs(self, folder_path: str, type_of_chunk: str, sizeofchunk: int):
        folder = Path(folder_path)
        pdf_files = list(folder.glob("*.pdf"))

        if not pdf_files:
            print(f"No PDF files found in {folder_path}")
            return

        for pdf in pdf_files:
            self.ingest_single_pdf(str(pdf), type_of_chunk, sizeofchunk)

'''
if __name__ == "__main__":
    bm25_search = BM25SEARCH1()

    pdf_paths = [
        r"/Users/sathya/Downloads/unstructured_scraped/pdfs/INSAT_Product_Version_information_V01.pdf",
        r"/Users/sathya/Downloads/unstructured_scraped/pdfs/Onset%20Prediction%202023.pdf",
        r"/Users/sathya/Downloads/unstructured_scraped/pdfs/Onset%20Prediction%202024.pdf",
        r"/Users/sathya/Downloads/unstructured_scraped/pdfs/sftp-mosdac_0.pdf",
        r"/Users/sathya/Downloads/unstructured_scraped/pdfs/STQC.pdf"
    ]

    chunk_type = "sentence"
    chunk_size = 1

    print("Indexing PDF files...")
    for path in pdf_paths:
        bm25_search.ingest_single_pdf(path, chunk_type, chunk_size)

    query = "eWhen does the peak of TPW over the Arabian Sea occur in relation to the monsoon onset over Kerala?"
    print(f"\nSearching for: {query}")
    results = bm25_search.search(query)

    print("\nTop matching results:")
    for i, res in enumerate(results, 1):
        print(f"{i}. {res}")
        '''
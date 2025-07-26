from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from itext2kg.documents_distiller import DocumentsDistiller
from itext2kg import iText2KG
from itext2kg.graph_integration import GraphIntegrator
from pydantic import BaseModel, Field
from typing import List, Tuple

class ArticleResults(BaseModel):
    abstract: str = Field(description="Brief summary of the article's abstract")
    key_findings: str = Field(description="The key findings of the article")
    limitation_of_sota: str = Field(description="Limitation of the existing work")
    proposed_solution: str = Field(description="The proposed solution in detail") 
    paper_limitations: str = Field(description="Limitations of the proposed solution")


ollama_llm_model = ChatOllama(
    model="llama3",
    temperature=0,
)

ollama_embeddings_model = OllamaEmbeddings(
    model="llama3",
)



documents_information: List[Tuple[str, List[int], BaseModel, str]] = [
    ("itext2kg/datasets/scientific_articles/actionable-cyber-threat.pdf", [10, 11, 12], ArticleResults, "scientific article"),
]


def upload_and_distill(documents_info: List[Tuple[str, List[int], BaseModel, str]]):
    distilled_docs = []

    for path_, exclude_pages, blueprint, doc_type in documents_info:
        loader = PyPDFLoader(path_)
        pages = loader.load_and_split()
       
        pages = [page for page in pages if page.metadata["page"] + 1 not in exclude_pages]

        distiller = DocumentsDistiller(llm_model=ollama_llm_model)

        IE_query = f"""
        # DIRECTIVES:
        - Act like an experienced information extractor.
        - You have a chunk of a {doc_type}.
        - If you do not find the information, keep the field empty.
        """

        distilled_doc = distiller.distill(
            documents=[page.page_content.replace("{", "[").replace("}", "]") for page in pages],
            IE_query=IE_query,
            output_data_structure=blueprint,
        )

       
        formatted = [
            f"{doc_type}'s {key} - {value}".replace("{", "[").replace("}", "]")
            for key, value in distilled_doc.items()
            if value and value != []
        ]

        distilled_docs.append(formatted)

    return distilled_docs



distilled_docs = upload_and_distill(documents_information)

itext2kg = iText2KG(llm_model=ollama_llm_model, embeddings_model=ollama_embeddings_model)
kg = itext2kg.build_graph(sections=distilled_docs[0], ent_threshold=0.9, rel_threshold=0.9)

print("\n Knowledge Graph:")
print(kg)


URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "win33api"
 
graph_integrator = GraphIntegrator(uri=URI, username=USERNAME, password=PASSWORD)
graph_integrator.visualize_graph(knowledge_graph=kg)

from langchain_ollama import ChatOllama, OllamaEmbeddings
from itext2kg import iText2KG
from itext2kg.documents_distiller import DocumentsDistiller
from itext2kg.graph_integration import GraphIntegrator
from pydantic import BaseModel, Field
from typing import List, Optional

class JobResponsibility(BaseModel):
    description: str = Field(...)

class JobQualification(BaseModel):
    skill: str = Field(...)

class JobCertification(BaseModel):
    certification: str = Field(...)

class JobOffer(BaseModel):
    job_offer_title: str = Field(...)
    company: str = Field(...)
    location: str = Field(...)
    job_type: str = Field(...)
    responsibilities: List[JobResponsibility] = Field(...)
    qualifications: List[JobQualification] = Field(...)
    certifications: Optional[List[JobCertification]] = Field(None)
    benefits: Optional[List[str]] = Field(None)
    experience_required: str = Field(...)
    salary_range: Optional[str] = Field(None)
    apply_url: Optional[str] = Field(None)

# Ollama LLM & embeddings
llm = ChatOllama(
    model="llama3",
    temperature=0,
)

embeddings = OllamaEmbeddings(
    model="llama3",
)

# Sample job offer text
job_offer = """
THE FICTITIOUS COMPANY

FICTITIOUS COMPANY is a high-end French fashion brand known for its graphic and poetic style, driven by the values of authenticity and transparency upheld by its creator Simon Porte Jacquemus.

Your Role
Craft visual stories that captivate, inform, and inspire. Transform concepts and ideas into visual representations. As a member of the studio, in collaboration with the designers and under the direction of the Creative Designer, you should be able to take written or spoken ideas and convert them into designs that resonate. You need to have a deep understanding of the brand image and DNA, being able to find the style and layout suited to each project.

Your Missions
Translate creative direction into high-quality silhouettes using Photoshop
Work on a wide range of projects to visualize and develop graphic designs that meet each brief
Work independently as well as in collaboration with the studio team to meet deadlines, potentially handling five or more projects simultaneously
Develop color schemes and renderings in Photoshop, categorized by themes, subjects, etc.

Your Profile
Bachelor’s degree (Bac+3/5) in Graphic Design or Art
3 years of experience in similar roles within a luxury brand's studio
Proficiency in Adobe Suite, including Illustrator, InDesign, Photoshop
Excellent communication and presentation skills
Strong organizational and time management skills to meet deadlines in a fast-paced environment
Good understanding of the design process
Freelance contract possibility
"""

# Distill semantic structure
document_distiller = DocumentsDistiller(llm_model=llm)

IE_query = '''
# DIRECTIVES :
- Act like an experienced information extractor.
- You have a chunk of a job offer description.
- If you do not find the right information, keep its place empty.
'''

distilled_job_offer = document_distiller.distill(
    documents=[job_offer],
    IE_query=IE_query,
    output_data_structure=JobOffer
)

semantic_blocks = [
    f"{key} - {value}".replace("{", "[").replace("}", "]")
    for key, value in distilled_job_offer.items()
    if value not in ([], "", None)
]

# Build Knowledge Graph
itext2kg = iText2KG(llm_model=llm, embeddings_model=embeddings)

kg = itext2kg.build_graph(
    sections=semantic_blocks,
    ent_threshold=0.6,
    rel_threshold=0.6
)

# Optional: Visualize in Neo4j
graph_integrator = GraphIntegrator(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="win32api"
)

graph_integrator.visualize_graph(knowledge_graph=kg)

print(" Knowledge graph extracted and visualized.")

<img width="2163" height="56" alt="image" src="https://github.com/user-attachments/assets/459ae24c-e051-44fa-895b-d077a08fff6d" />KG-INFO-RETRIEVAL-BOT
# AI-Based Help Bot for Information Retrieval
- Uses a Knowledge Graph as the core data structure
- Extracts information from both static and dynamic web portal content
- Provides natural language query support

## Detailed Solution & Approach

Semantra.io is an AI-powered agentic system that transforms how users retrieve and understand complex satellite datasets and documentation from ISRO’s MOSDAC portal. By combining semantic understanding, geospatial reasoning, and knowledge graph engineering, it enables natural language access to both structured and unstructured data.

### Multi-Agent Architecture
  
Semantra.io is powered by a set of intelligent, specialized agents, each focused on a key aspect of the retrieval pipeline:

#### 1. Knowledge Graph Agent

Extracts entities and relationships from domain sources
Builds a knowledge graph of satellites, sensors, missions, data products, etc.
Enables reasoning and structured querying over the space data domain

#### 2.  Graph Embedding Agent

Generates vector embeddings from the knowledge graph
Enables semantic similarity search for vague or conceptual queries
Powers fast and accurate information retrieval using vector-based matching

#### 3.  Contextual Retrieval Agent

Converts documentation into Document Structure Graphs (DSGs)
Preserves semantic hierarchy of manuals, specifications, and policies
Enables context-aware Q&A with traceable answer sources
#### 4.  GeoAgent (Geospatial Parsing & Reasoning)

Parses geospatial mentions in user queries using tools like Mordecai3
Links place names to latitude/longitude coordinates
Resolves spatial filters (e.g., “rainfall over Kerala in July 2020”)
Enhances relevance of results using spatial constraints
 GeoAgent bridges the gap between natural language and spatial metadata, making it possible to answer geo-temporal queries over satellite products.
 
#### 🔗 Agent Coordination via AG-UI Protocol

All agents interact via a shared protocol (AG-UI) that ensures:

Modular and scalable orchestration
Smooth inter-agent communication
Unified response synthesis with traceability

#### 💬 Conversational Interface

The system is accessed via a chat-based UI:

Accepts natural language questions
Returns precise, contextual answers
Enables interactive exploration of satellite data


## Tech Stack

Semantra.io is built on a robust and scalable AI architecture, powered by modern tools for semantic search, vector databases, geospatial reasoning, and multi-agent coordination.

#### Knowledge Graph & Reasoning

Neo4j – Native graph database for representing satellite, mission, and sensor relationships
PyKEEN – For knowledge graph embedding and link prediction


#### Semantic & Contextual Retrieval

pgvector – Vector similarity search in PostgreSQL
Haystack – Framework for building NLP-powered search pipelines
Hugging Face Transformers – Pretrained models for Q&A, embedding, and document understanding
LangChain – Orchestration framework for LLM-based agent pipelines
Gemini / Gemini Pro – Multimodal language model for natural language understanding and reasoning

#### Geospatial Search

ElasticSearch – Full-text and hybrid search with dense/sparse retrieval support
GeoAgent – Custom agent using Mordecai3 and geonames for spatial entity extraction


#### Agent Communication & UI

AG-UI Protocol – Internal protocol for agent interaction and unified response generation
Conversational UI (Chat-based) – Frontend interface for querying the system in natural language

## AGENT

### Knowledge Graph Discovery Agent
The Knowledge Graph Discovery Agent is the consuming and query-serving layer of the system.
It connects to the Conversational UI, Graph Discovery Tools, and Embedding-based Semantic Search to provide real-time access to structured graph data and knowledge graph embeddings.

#### Features & Skills
Knowledge Graph Query Execution → Discover direct relationships in structured datasets.

Knowledge Graph Embedding Discovery → Identify indirect/semantic relationships using embeddings.

Conversational UI Query Handling → Understand and answer natural language graph queries.

Graph Exploration Interface Support → Assist in interactive graph browsing.


#### Installation & Setup
1. Clone the Repository
2. 
<pre> git clone https://github.com/SATHYAGITH368/kg-info-retrieval-bot.git </pre>

<pre> cd knowledge_graph_agent </pre>

3. Install Dependencies
<pre> pip install itexttokg
pip install neo4j
pip install python_a2a </pre>

5. (Optional) Test Locally
   
Run client.py to test the agent before integrating into the React UI:

<pre> python client1.py </pre>

7.  use it in the frontend run:npm run dev

8.  Run the Agent
<pre> python main1.py </pre>


The Knowledge Graph Discovery Agent can store and query data using Neo4j, a high-performance graph database.

1. Install Neo4j
Option A: Desktop App (Recommended for testing)
Download and install Neo4j Desktop from

https://neo4j.com/download/.

3. Start Neo4j
If using Neo4j Desktop, create and start a new database.

If using Docker, the database is available at:

Browser → http://localhost:7474

Bolt protocol → bolt://localhost:7687

5. Install Python Driver
Inside your knowledge_graph_agent environment:

<pre>  pip install neo4j  </pre>

4. Configure Connection
In your agent_executor1.py , set your Neo4j URI, username, and password:

<pre> from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
username = "neo4j"
password = "test"  # Change if needed

driver = GraphDatabase.driver(uri, auth=(username, password))</pre>









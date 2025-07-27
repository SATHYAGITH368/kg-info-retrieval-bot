KG-INFO-RETRIEVAL-BOT
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


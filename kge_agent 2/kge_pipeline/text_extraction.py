import ollama



def extract_text(text_content: str):
    """
    Extract ISRO-related entities and triples from the input text.
    This function first extracts entities, then extracts triples (edges) based on those entities.
    """

    entity_types = [
        {"entity_type_id": "1", "entity_type": "Mission", "description": "Name of the ISRO mission, e.g., Chandrayaan-3"},
        {"entity_type_id": "2", "entity_type": "LaunchVehicle", "description": "Rocket or launch vehicle used for the mission"},
        {"entity_type_id": "3", "entity_type": "Satellite", "description": "Name of satellite launched or involved"},
        {"entity_type_id": "4", "entity_type": "LaunchDate", "description": "Date of launch of the mission"},
        {"entity_type_id": "5", "entity_type": "Payload", "description": "Payload details of the mission"},
        {"entity_type_id": "6", "entity_type": "OrbitType", "description": "Type of orbit, e.g., geostationary, polar"},
        {"entity_type_id": "7", "entity_type": "MissionStatus", "description": "Current status of the mission, e.g., successful, ongoing, failed"},
    ]

  
    entity_prompt = f"""
You are an expert entity extractor.

Extract entities from the following text, and classify them based on the ENTITY TYPES provided below.

Text:
\"\"\"
{text_content}
\"\"\"

ENTITY TYPES:
{entity_types}

Return only valid JSON in this format:
{{
  "entities": [
    {{
      "entity_type": "<ENTITY_TYPE>",
      "entity": "<EXTRACTED_ENTITY_NAME>"
    }}
  ]
}}
"""

    entity_messages = [
        {"role": "system", "content": "You are an expert entity extractor."},
        {"role": "user", "content": entity_prompt}
    ]

    entity_response = ollama.chat(model='llama3', messages=entity_messages)
    extracted_entities = entity_response['message']['content']


    triple_prompt = f"""
You are an expert fact extractor that extracts fact triples from text.

CONTENT:
\"\"\"
{text_content}
\"\"\"

ENTITIES:
{extracted_entities}

ENTITY TYPES:
{entity_types}

TASK:
Extract all factual relationships between the given ENTITIES based on the CONTENT.

Only extract facts that:
- involve two DISTINCT ENTITIES from the ENTITIES list,
- are clearly stated or unambiguously implied in the CONTENT,
- and can be represented as edges in a knowledge graph.

Use SCREAMING_SNAKE_CASE for predicates.

Triple format example:
Mission Chandrayaan3 HasLaunchVehicle GSLVMk3
GSLVMk3 LaunchedSatellite PragyanRover
Chandrayaan3 HasLaunchDate 2023-07-14
PragyanRover HasPayload XRaySpectrometer
Chandrayaan3 HasMissionStatus Successful

Return only triples, one per line, no other text.
"""

    triple_messages = [
        {"role": "system", "content": "You are an expert fact extractor that extracts fact triples from text."},
        {"role": "user", "content": triple_prompt}
    ]

    triple_response = ollama.chat(model='llama3', messages=triple_messages)
    triples_text = triple_response['message']['content']

    return triples_text

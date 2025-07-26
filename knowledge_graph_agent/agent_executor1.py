from python_a2a import A2AServer, Message, TextContent, MessageRole
from kg_skills import KGAgentSkills
from neo4j import GraphDatabase
import traceback
import re
import json
import requests

MAX_ELEMENTS = 100  # limit number of nodes & edges sent to UI


class KGAgentExecutor(A2AServer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.skills = KGAgentSkills()
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "win33api")
        )

    def handle_message(self, message: Message) -> Message:
        try:
            content = message.content
            if isinstance(content, TextContent):
                user_text = content.text.strip()
            elif isinstance(content, dict) and "text" in content:
                user_text = str(content["text"]).strip()
                message.content = TextContent(text=user_text)
            elif isinstance(content, str):
                user_text = content.strip()
                message.content = TextContent(text=user_text)
            else:
                raise ValueError(f"Unsupported content type: {type(content)}")

            user_text_lower = user_text.lower()

            if any(word in user_text_lower for word in ["build", "create", "generate"]):
                domain = None
                if "satellite" in user_text_lower:
                    domain = "SATELLITE"
                elif "insitu" in user_text_lower:
                    domain = "INSITU"
                elif "radar" in user_text_lower:
                    domain = "RADAR"

                if domain:
                    return self.build_kg(message, domain)

            return self.query_kg(message, user_text)

        except Exception as e:
            traceback.print_exc()
            return Message(
                content=TextContent(text=f"Unexpected error: {e}"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id,
            )

    def build_kg(self, message, domain):
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) AS node_count")
                node_count = result.single()["node_count"]
            response_text = (
                f"Detected domain: {domain}. Neo4j currently has {node_count} nodes.\n"
            )
            response_text += self.skills.build_kg_from_csv(domain)
        except Exception as db_ex:
            traceback.print_exc()
            response_text = f"Error while accessing Neo4j or CSV: {db_ex}"

        return Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id,
        )

    def query_kg(self, message, user_text):
        try:
            with self.neo4j_driver.session() as session:
                better_prompt = f"""
You are a Neo4j knowledge graph assistant.

The graph contains nodes of type `Station`, each representing a weather station.
Each `Station` node has the following properties:
- `name` (string)
- `latitude` (float)
- `longitude` (float)
- `state` (string)
- `sttid` (string)
- `key` (string)
- `frequency` (string)
- `active` (string: "Active" or "In-Active")
- `startdate` (string, format: YYYY-MM-DD)
- `enddate` (string, format: YYYY-MM-DD)

Write a valid **Neo4j Cypher query** to answer the following natural language question **using only the above properties**.

✅ The query must always:
- use `MATCH (n)-[r]-(m)` to retrieve both nodes and their relationships, regardless of direction.

- if matching `id`, convert it to string using `toString(n.id)`.
- include `WHERE` clauses as appropriate, comparing strings case-insensitively with `toLower()`.
- return `n`, `r`, and `m`.
- limit the result to at most 100 rows.

🚫 Do not include explanations, comments, or formatting — only the Cypher query text.

Question: "{user_text}"

Cypher:
""".strip()

                cypher_query = call_gemini(better_prompt).strip()
                print(f"Generated Cypher: {cypher_query}")

                result = session.run(cypher_query)

                hierarchy = {}
                for record in result:
                    n = record.get("n")
                    if not n:
                        continue
                    name = n.get("name", "unknown")
                    hierarchy[name] = {
                        "active": n.get("active", ""),
                        "startDate": n.get("startdate", ""),
                        "endDate": n.get("enddate", ""),
                        "name": name,
                        "id": n.id,
                        "latitude": n.get("latitude", ""),
                        "longitude": n.get("longitude", ""),
                        "state": n.get("state", ""),
                        "sttid": n.get("sttid", ""),
                        "key": n.get("key", ""),
                        "frequency": n.get("frequency", ""),
                    }

                nodes, edges = session.execute_read(fetch_data, cypher_query)

                nodes = nodes[:MAX_ELEMENTS]
                edges = edges[:MAX_ELEMENTS]
                nodes, edges = clean_graph_data(nodes, edges)

                graph_response = {
                    "elements": {
                        "nodes": nodes,
                        "edges": edges
                    }
                }

                if not hierarchy:
                    return Message(
                        content=TextContent(text="No nodes found matching your query."),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id,
                    )

                json_hierarchy = json.dumps({"stations": hierarchy}, indent=2)

                summary_prompt = (
                    "Given the following JSON of weather stations, write a clear summary in natural English. "
                    "For each station, write **one bullet point** describing:\n"
                    "- Station name\n"
                    "- Active or Inactive status\n"
                    "- Start and end dates\n"
                    "- Location (latitude, longitude, state)\n"
                    "- Station ID and Key\n"
                    "- Frequency of data collection\n\n"
                    "Write in clear, concise sentences, one bullet per station.\n\n"
                    f"```json\n{json_hierarchy}\n```"
                )

                explanation = call_gemini(summary_prompt)

                response_dict = {
                    "explanation": explanation,
                    "graph": graph_response
                }

                return Message(
                    content=TextContent(text=json.dumps(response_dict, indent=2)),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id,
                )

        except Exception as e:
            traceback.print_exc()
            return Message(
                content=TextContent(text=f"Error while querying Neo4j: {e}"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id,
            )


def clean_graph_data(nodes, edges):
    node_ids = {n["data"]["id"] for n in nodes}
    valid_edges = [
        e for e in edges
        if e["data"]["source"] in node_ids and e["data"]["target"] in node_ids
    ]
    return nodes, valid_edges


def call_gemini(prompt: str) -> str:
    api_key = "AIzaSyAcc9r_l77Fv83C2qxadNV5CtGurMQHZcI"
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            f"{api_url}?key={api_key}",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        if raw_text.startswith("```"):
            cleaned = re.sub(r"^```[a-z]*\s*", "", raw_text)
            cleaned = re.sub(r"```$", "", cleaned)
            return cleaned.strip()

        return raw_text

    except requests.exceptions.ReadTimeout:
        return "⚠️ Gemini API timed out while generating the response. Please try again."
    except Exception as e:
        return f"⚠️ Error calling Gemini API: {e}"
def fetch_data(tx, query):
    result = tx.run(query)
    nodes = {}
    edges = []
    for record in result:
        n = record["n"]
        m = record["m"]
        r = record["r"]

        if n.id not in nodes:
            nodes[n.id] = {
                "data": {
                    "id": str(n.id),              # Convert node id to string
                    "labels": list(n.labels),
                    "properties": dict(n)
                }
            }
        if m.id not in nodes:
            nodes[m.id] = {
                "data": {
                    "id": str(m.id),              # Convert node id to string
                    "labels": list(m.labels),
                    "properties": dict(m)
                }
            }

        edges.append({
            "data": {
                "id": str(r.id),                  # Convert edge id to string
                "type": r.type,
                "source": str(r.start_node.id),   # Convert source to string
                "target": str(r.end_node.id),     # Convert target to string
                "properties": dict(r),
            }
        })

    nodes_list = list(nodes.values())

    print(f"DEBUG: Total unique nodes: {len(nodes_list)}")
    for node in nodes_list[:5]:  # print first 5 nodes
        print(f"Node: {node}")

    print(f"DEBUG: Total edges: {len(edges)}")
    for edge in edges[:5]:       # print first 5 edges
        print(f"Edge: {edge}")

    return nodes_list, edges
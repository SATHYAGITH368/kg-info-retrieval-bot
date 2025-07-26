from python_a2a import (
    A2AServer,
    Message,
    MessageRole,
    TextContent,
    ErrorContent,
)
from elasticsearch import Elasticsearch
from mordecai3 import Geoparser


class InsituGeoAgent(A2AServer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.es = Elasticsearch("http://localhost:9200")
        self.geo = Geoparser()

    def handle_message(self, message: Message) -> Message:
        try:
            query_text = message.content.text.strip()
            locations = []

            # First try Mordecai
            result = self.geo.geoparse_doc(query_text)

            if result.get("geolocated_ents"):
                for ent in result["geolocated_ents"]:
                    name = ent.get("name", "")
                    admin1 = ent.get("admin1_name", "")
                    lat = ent.get("lat", "")
                    lon = ent.get("lon", "")
                    locations.append(f"{name} ({admin1}) — Lat: {lat}, Lon: {lon}")

            # If no Mordecai result, try Elasticsearch
            if not locations:
                # First try exact phrase
                es_query = {
                    "query": {
                        "match_phrase": {
                            "name": query_text
                        }
                    },
                    "size": 1
                }
                es_resp = self.es.search(index="geonames", body=es_query)

                hit = next(iter(es_resp["hits"]["hits"]), None)

                # If no exact phrase match, try fuzzy
                if not hit:
                    es_query_fuzzy = {
                        "query": {
                            "match": {
                                "name": {
                                    "query": query_text,
                                    "fuzziness": "AUTO"
                                }
                            }
                        },
                        "size": 1
                    }
                    es_resp = self.es.search(index="geonames", body=es_query_fuzzy)
                    hit = next(iter(es_resp["hits"]["hits"]), None)

                if hit:
                    src = hit["_source"]
                    name = src.get("name", "")
                    admin1 = src.get("admin1_name", "")
                    lat = src.get("latitude", "")
                    lon = src.get("longitude", "")
                    locations.append(f"{name} ({admin1}) — Lat: {lat}, Lon: {lon}")

            if locations:
                response_text = "\n".join(locations)
            else:
                response_text = "No locations detected in your query."

            content = TextContent(text=response_text)

        except Exception as e:
            content = ErrorContent(message=str(e))

        return Message(
            content=content,
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id,
        )

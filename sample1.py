from elasticsearch import Elasticsearch
import spacy

# Load spaCy English model
nlp = spacy.load("en_core_web_trf")


# Connect to ES
es = Elasticsearch("http://localhost:9200")

# Input sentence
sentence = "We installed weather monitoring equipment at Diglipur in the Andaman & Nicobar Islands."

# Extract GPEs (places) from sentence
doc = nlp(sentence)
places = [ent.text for ent in doc.ents if ent.label_ == "GPE"]

if not places:
    print("No place names detected in sentence.")
else:
    print(f"Detected places: {places}\n")

    for place in places:
        query = {
            "query": {
                "match": {
                    "name": place
                }
            }
        }

        response = es.search(index="mosdac", body=query)

        print(f"Results for: {place}")
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            print(f"Name: {source['name']}")
            print(f"State: {source['admin1_name']}")
            print(f"Lat/Lon: {source['lat']}, {source['lon']}")
            print(f"Country: {source['country_code']}")
            print(f"Alternative names: {source['alternativenames']}")
            print("-" * 40)

        if not response["hits"]["hits"]:
            print("No matches found.")

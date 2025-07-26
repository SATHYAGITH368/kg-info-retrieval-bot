import numpy as np
import torch
import yaml
import psycopg2
import ast
import asyncio

from pykeen.models import DistMult
from pykeen.training import SLCWATrainingLoop
from pykeen.triples import TriplesFactory
from pykeen.evaluation import RankBasedEvaluator
from kge_pipeline.text_extraction import extract_text


class DistMultKnowledgeGraphEmbedding:
    def __init__(self, embedding_dim=30, model_path="distmult_model.pth", config_path='app/config/config.yaml'):
        self.embedding_dim = embedding_dim
        self.model_path = model_path
        self.config_path = config_path

        try:
            self.model_state = torch.load(self.model_path)
            self.entity_embeddings = self.model_state['entity_representations.0._embeddings.weight']
            self.relation_embeddings = self.model_state['relation_representations.0._embeddings.weight']
        except Exception:
         
            self.model_state = None
            self.entity_embeddings = None
            self.relation_embeddings = None

    def parse_raw_triples(self, raw_triples):
      
        triples = []
        for line in raw_triples:
            parts = line.strip().split()
            if len(parts) == 3:
                triples.append(tuple(parts))
            else:
                print(f"[WARN] Skipping malformed triple line: {line}")

        triples_np = np.array(triples, dtype=str)
        if triples_np.ndim != 2 or triples_np.shape[1] != 3:
            raise ValueError(f"Invalid triples shape: {triples_np.shape}. Expected (n, 3)")

        triples_factory = TriplesFactory.from_labeled_triples(triples_np)
        return triples, triples_factory

    def train_model(self, triples, embedding_dim=None, num_epochs=100):
      embedding_dim = embedding_dim or self.embedding_dim
      triples_factory = TriplesFactory.from_labeled_triples(np.array(triples, dtype=str))

      train_tf = triples_factory

      print(f"Training triples: {train_tf.num_triples}")

      model = DistMult(triples_factory=train_tf, embedding_dim=embedding_dim)
      training_loop = SLCWATrainingLoop(model=model, triples_factory=train_tf)
      training_loop.train(train_tf, num_epochs=num_epochs, batch_size=32)

      results = None

      return model, results, triples_factory


    def save_model_embeddings_to_db(self, model, triples_factory):
     
        config = self._load_db_config()
        conn = psycopg2.connect(**config)
        cur = conn.cursor()

      
        cur.execute("""
            CREATE TABLE IF NOT EXISTS entity_embeddings (
                id SERIAL PRIMARY KEY,
                entity TEXT UNIQUE,
                embedding VECTOR(30)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS relation_embeddings (
                id SERIAL PRIMARY KEY,
                relation TEXT UNIQUE,
                embedding VECTOR(30)
            );
        """)

        entity_embeddings = model.entity_representations[0](indices=None).detach().cpu().numpy()
        for entity, emb in zip(triples_factory.entity_to_id, entity_embeddings):
            cur.execute("""
                INSERT INTO entity_embeddings (entity, embedding)
                VALUES (%s, %s)
                ON CONFLICT (entity) DO UPDATE SET embedding = EXCLUDED.embedding;
            """, (entity, emb.tolist()))

        relation_embeddings = model.relation_representations[0](indices=None).detach().cpu().numpy()
        for relation, emb in zip(triples_factory.relation_to_id, relation_embeddings):
            cur.execute("""
                INSERT INTO relation_embeddings (relation, embedding)
                VALUES (%s, %s)
                ON CONFLICT (relation) DO UPDATE SET embedding = EXCLUDED.embedding;
            """, (relation, emb.tolist()))

        conn.commit()
        cur.close()
        conn.close()
        print("[INFO] Embeddings saved to PostgreSQL.")

    def parse_triples_from_text(self, text_output):
      triples = []
      lines = text_output.strip().split('\n')

      for line in lines:
        parts = line.strip().split(maxsplit=2)
        if len(parts) == 3:
            # Detect if the first part is a likely relation
            first_token = parts[0]
            if (
                first_token.isupper() or  # SCREAMING_SNAKE_CASE
                first_token[0].isupper()  # Capitalized relation name
            ):
                # Assume format: [relation, head, tail] → convert to [head, relation, tail]
                triple = [parts[0], parts[1], parts[2]]
            else:
                triple = parts
            triples.append([p.strip() for p in triple])
        else:
            print(f"[WARN] Skipping malformed line: {line}")

      triples_np = np.array(triples, dtype=str)
      if triples_np.ndim != 2 or triples_np.shape[1] != 3:
        raise ValueError(f"Invalid triples shape: {triples_np.shape}. Expected (n, 3)")

      triples_factory = TriplesFactory.from_labeled_triples(triples_np)
      return triples, triples_factory


    async def process_user_input(self, user_content):
       
        extracted_triples = extract_text(user_content)
        triples, triples_factory = self.parse_triples_from_text(extracted_triples)
       
        model, _, _ = self.train_model(triples)
        self.save_model_embeddings_to_db(model, triples_factory)
        
        return triples

    def _load_db_config(self):
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _fetch_embedding_from_db(self, name, table, key_column):
        config = self._load_db_config()
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        cur.execute(f"SELECT embedding FROM {table} WHERE {key_column} = %s", (name,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            emb_val = result[0]
      
            emb = torch.tensor(ast.literal_eval(emb_val) if isinstance(emb_val, str) else emb_val, dtype=torch.float32)
            return emb
        else:
            print(f"[WARN] {name} not found in {table}. Returning random vector.")
            return torch.randn(self.embedding_dim)

    def _fetch_all_entities_with_embeddings(self):
        config = self._load_db_config()
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        cur.execute("SELECT entity, embedding FROM entity_embeddings")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        entities = []
        embeddings = []
        for entity, emb_raw in rows:
            try:
                emb_parsed = ast.literal_eval(emb_raw) if isinstance(emb_raw, str) else list(emb_raw)
                embeddings.append([float(x) for x in emb_parsed])
                entities.append(entity)
            except Exception as e:
                print(f"[ERROR] Failed parsing embedding for entity '{entity}': {e}")

        return entities, torch.tensor(embeddings, dtype=torch.float32)

    def _fetch_all_relations_with_embeddings(self):
        config = self._load_db_config()
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        cur.execute("SELECT relation, embedding FROM relation_embeddings")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        relations = []
        embeddings = []
        for relation, emb_raw in rows:
            try:
                emb_parsed = ast.literal_eval(emb_raw) if isinstance(emb_raw, str) else list(emb_raw)
                embeddings.append([float(x) for x in emb_parsed])
                relations.append(relation)
            except Exception as e:
                print(f"[ERROR] Failed parsing embedding for relation '{relation}': {e}")

        return relations, torch.tensor(embeddings, dtype=torch.float32)

    def predict_tail_entities(self, head_entity, relation, top_k=5):
        h_emb = self._fetch_embedding_from_db(head_entity, "entity_embeddings", "entity")
        r_emb = self._fetch_embedding_from_db(relation, "relation_embeddings", "relation")
        entities, tail_embeddings = self._fetch_all_entities_with_embeddings()

        with torch.no_grad():
            scores = torch.matmul(tail_embeddings, (h_emb * r_emb))
            probs = torch.sigmoid(scores)
            top_scores, top_indices = torch.topk(probs, k=top_k)

        # Use enumerate to correctly map scores to entities
        return [(head_entity, relation, entities[i], top_scores[idx].item()) for idx, i in enumerate(top_indices)]

    def predict_head_entities(self, relation, tail_entity, top_k=5):
        t_emb = self._fetch_embedding_from_db(tail_entity, "entity_embeddings", "entity")
        r_emb = self._fetch_embedding_from_db(relation, "relation_embeddings", "relation")
        entities, head_embeddings = self._fetch_all_entities_with_embeddings()

        with torch.no_grad():
            scores = torch.matmul(head_embeddings, (t_emb * r_emb))
            probs = torch.sigmoid(scores)
            top_scores, top_indices = torch.topk(probs, k=top_k)

        return [(entities[i], relation, tail_entity, top_scores[idx].item()) for idx, i in enumerate(top_indices)]

    def predict_relations(self, head_entity, tail_entity, top_k=5):
        h_emb = self._fetch_embedding_from_db(head_entity, "entity_embeddings", "entity")
        t_emb = self._fetch_embedding_from_db(tail_entity, "entity_embeddings", "entity")
        relations, r_embeddings = self._fetch_all_relations_with_embeddings()

        with torch.no_grad():
            scores = torch.matmul(r_embeddings, (h_emb * t_emb))
            probs = torch.sigmoid(scores)
            top_scores, top_indices = torch.topk(probs, k=top_k)

        return [(head_entity, relations[i], tail_entity, top_scores[idx].item()) for idx, i in enumerate(top_indices)]

    def query_knowledge_graph(self, query_text, top_k=5):
      
        extracted_query = extract_text(query_text)
        triples, _ = self.parse_triples_from_text(extracted_query)
        results = []

        for triple in triples:
            head, relation, tail = (triple + [None] * 3)[:3]

            if head != '?' and relation != '?' and tail == '?':
                results.extend(self.predict_tail_entities(head, relation, top_k))
            elif head == '?' and relation != '?' and tail != '?':
                results.extend(self.predict_head_entities(relation, tail, top_k))
            elif head != '?' and relation == '?' and tail != '?':
                results.extend(self.predict_relations(head, tail, top_k))
            elif head != '?' and relation != '?' and tail != '?':
                print(f"[INFO] Full triple provided: {triple}. You may implement similarity matching here.")
            else:
                print(f"[WARN] Invalid query triple skipped: {triple}")

        return results


if __name__ == "__main__":

   sample_text = """
Chandrayaan3 is an ISRO mission launched by the GSLVMk3 launch vehicle on 2023-07-14.
The mission carried the PragyanRover payload which includes an XRaySpectrometer.
Chandrayaan3 mission status is successful.

Mangalyaan (Mars Orbiter Mission) was launched on 2013-11-05 using the PSLV-C25 rocket.
Mangalyaan's payload includes a Methane Sensor and a Lyman Alpha Photometer.
Mangalyaan is currently in Mars orbit and operational.

RISAT-2B is an Indian Radar Imaging Satellite launched on 2019-05-22.
The launch vehicle used was PSLV-C46.
RISAT-2B's mission status is active.

GSAT-30 is a communication satellite launched on 2020-01-17.
It was launched by the Ariane 5 rocket.
GSAT-30 provides high-quality telecommunication services.

Chandrayaan2 was launched on 2019-07-22.
It included the Vikram lander and Pragyan rover as payloads.
The launch vehicle was GSLVMk3.
Chandrayaan2 mission status was partially successful.

Cartosat-3 was launched by PSLV-C47 on 2019-11-27.
It carries a high-resolution panchromatic camera.
Cartosat-3's mission status is successful.
"""


  
   kge = DistMultKnowledgeGraphEmbedding()

  
   triples = asyncio.run(kge.process_user_input(sample_text))

   print("\nExtracted Triples:")
   for triple in triples:
        print(triple)


   print("\nTop tail entity predictions for (Chandrayaan3, HasLaunchVehicle, ?):")
   tail_preds = kge.predict_tail_entities("Chandrayaan3", "HasLaunchVehicle", top_k=3)
   for pred in tail_preds:
        print(pred)

   print("\nTop head entity predictions for (?, HasPayload, PragyanRover):")
   head_preds = kge.predict_head_entities("HasPayload", "PragyanRover", top_k=3)
   for pred in head_preds:
        print(pred)

   print("\nTop relation predictions for (Chandrayaan3, ?, PragyanRover):")
   rel_preds = kge.predict_relations("Chandrayaan3", "PragyanRover", top_k=3)
   for pred in rel_preds:
        print(pred)
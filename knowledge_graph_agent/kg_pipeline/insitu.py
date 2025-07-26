from neo4j import GraphDatabase
from pydantic import BaseModel
import pandas as pd
from pathlib import Path
from typing import List, Optional


class StationRecord(BaseModel):
    actv: str
    enddate: Optional[str]
    frequency: Optional[str] = ""
    id: str
    key: str
    latres: float
    longres: float
    name: str
    startdate: Optional[str]
    state: str
    sttid: int
    domain: str  # NEW — to capture AWS/AMS/IMDAWS/AWSAGRI/AMSAGRI


class Neo4jStationGraph:
    def __init__(self, uri, user, password, csv_mapping: dict):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.csv_mapping = csv_mapping  # dict {domain: csv_path}

    def close(self):
        self.driver.close()

    def load_station_records(self) -> List[StationRecord]:
        records = []
        for domain, path in self.csv_mapping.items():
            path = Path(path)
            print(f"📄 Reading {domain}: {path}")
            df = pd.read_csv(path, na_values=["NA"])
            for _, row in df.iterrows():
                record = StationRecord(
                    actv=str(row.get("actv", "") or ""),
                    enddate=str(row["enddate"]) if pd.notna(row.get("enddate")) else None,
                    frequency=str(row.get("frequency", "") or ""),
                    id=str(row.get("id", "") or ""),
                    key=str(row.get("key", "") or ""),
                    latres=float(row.get("latres", 0.0) or 0.0),
                    longres=float(row.get("longres", 0.0) or 0.0),
                    name=str(row.get("name", "") or ""),
                    startdate=str(row["startdate"]) if pd.notna(row.get("startdate")) else None,
                    state=str(row.get("state", "") or ""),
                    sttid=int(row.get("sttid", 0) or 0),
                    domain=domain
                )
                records.append(record)
        return records

    def build_graph(self):
        records = self.load_station_records()
        with self.driver.session() as session:
            for r in records:
                session.write_transaction(self.create_station_graph, r)

    @staticmethod
    def create_station_graph(tx, r: StationRecord):
        # Create Domain node
        tx.run("""
            MERGE (d:Domain {name: $domain})
        """, domain=r.domain)

        # Create Station node with all properties
        tx.run("""
            MERGE (s:Station {id: $id})
            SET s.name = $name,
                s.latitude = $lat,
                s.longitude = $lon,
                s.state = $state,
                s.active = $actv,
                s.startdate = $startdate,
                s.enddate = $enddate,
                s.frequency = $frequency,
                s.sttid = $sttid,
                s.key = $key
        """, id=r.id, name=r.name, lat=r.latres, lon=r.longres,
             state=r.state, actv=r.actv, startdate=r.startdate,
             enddate=r.enddate, frequency=r.frequency, sttid=r.sttid, key=r.key)

        # Link Station to Domain
        tx.run("""
            MATCH (s:Station {id: $id}), (d:Domain {name: $domain})
            MERGE (s)-[:BELONGS_TO]->(d)
        """, id=r.id, domain=r.domain)

        # Create Location node for state
        tx.run("""
            MERGE (loc:Location {name: $state})
            MERGE (s:Station {id: $id})-[:LOCATED_IN]->(loc)
        """, id=r.id, state=r.state)


if __name__ == "__main__":
    csvs = {
        "AWS": r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Insitu(AWS)\satellite_sensor_data_AWS.csv",
        "AMS": r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Insitu(AWS)\satellite_sensor_data_AMS.csv",
        "IMDAWS": r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Insitu(AWS)\satellite_sensor_data_IMDAWS.csv",
        "AWSAGRI": r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Insitu(AWS)\satellite_sensor_data_AWSAGRI.csv",
        "AMSAGRI": r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Insitu(AWS)\satellite_sensor_data_AWSUPG.csv"
    }

    graph = Neo4jStationGraph(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="win33api",
        csv_mapping=csvs
    )

    graph.build_graph()
    graph.close()
    print(" Neo4j knowledge graph built successfully.")

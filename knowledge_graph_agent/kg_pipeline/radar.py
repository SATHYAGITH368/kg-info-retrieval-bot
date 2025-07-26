from neo4j import GraphDatabase
from pydantic import BaseModel
import pandas as pd
from pathlib import Path
from typing import Optional, List


class ProductRecord(BaseModel):
    actv: str
    crnt_flg: str
    description: str
    enddate: Optional[str]
    frequency: Optional[str]
    id: str
    longres: Optional[str]
    name: str
    prefix: Optional[str]
    processlevel: Optional[str]
    satinorbit: Optional[str]
    startdate: Optional[str]
    suffix: Optional[str]
    techdoc: Optional[str]
    domain: str = "RADAR"


class Neo4jRadarGraph:
    def __init__(self, uri, user, password, csv_paths: List[str]):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.csv_paths = [Path(p) for p in csv_paths]

    def close(self):
        self.driver.close()

    def load_records(self) -> List[ProductRecord]:
        records = []
        for csv_path in self.csv_paths:
            print(f"📄 Reading RADAR CSV: {csv_path.name}")
            df = pd.read_csv(csv_path, na_values=["NA"])
            for _, row in df.iterrows():
                record = ProductRecord(
                    actv=str(row.get("actv", "") or ""),
                    crnt_flg=str(row.get("crnt_flg", "") or ""),
                    description=str(row.get("description", "") or ""),
                    enddate=str(row.get("enddate", "")) if pd.notna(row.get("enddate")) else None,
                    frequency=str(row.get("frequency", "")) or "",
                    id=str(row.get("id", "")) or "",
                    longres=str(row.get("longres", "")) or "",
                    name=str(row.get("name", "")) or "",
                    prefix=str(row.get("prefix", "")) or "",
                    processlevel=str(row.get("processlevel", "")) or "",
                    satinorbit=str(row.get("satinorbit", "")) or "",
                    startdate=str(row.get("startdate", "")) if pd.notna(row.get("startdate")) else None,
                    suffix=str(row.get("suffix", "")) or "",
                    techdoc=str(row.get("techdoc", "")) or "",
                )
                records.append(record)
        print(f"✅ Loaded {len(records)} records from all CSVs.")
        return records

    def build_graph(self):
        records = self.load_records()
        with self.driver.session() as session:
            for r in records:
                session.write_transaction(self.create_product_graph, r)

    @staticmethod
    def create_product_graph(tx, r: ProductRecord):
        # Ensure Domain exists
        tx.run("""
            MERGE (d:Domain {name: $domain})
        """, domain=r.domain)

        # Create Product node
        tx.run("""
            MERGE (p:Product {id: $id})
            SET p.name = $name,
                p.description = $description,
                p.active = $actv,
                p.crnt_flg = $crnt_flg,
                p.enddate = $enddate,
                p.startdate = $startdate,
                p.frequency = $frequency,
                p.prefix = $prefix,
                p.processlevel = $processlevel,
                p.satinorbit = $satinorbit,
                p.suffix = $suffix,
                p.techdoc = $techdoc,
                p.longres = $longres
        """, id=r.id, name=r.name, description=r.description, actv=r.actv,
             crnt_flg=r.crnt_flg, enddate=r.enddate, startdate=r.startdate,
             frequency=r.frequency, prefix=r.prefix, processlevel=r.processlevel,
             satinorbit=r.satinorbit, suffix=r.suffix, techdoc=r.techdoc, longres=r.longres)

        # Link Product -> Domain
        tx.run("""
            MATCH (p:Product {id: $id}), (d:Domain {name: $domain})
            MERGE (p)-[:BELONGS_TO]->(d)
        """, id=r.id, domain=r.domain)


if __name__ == "__main__":
    csv_list = [
        r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\RADAR\satellite_sensor_data_S_BAND_CHERRAPUNJI.csv",
        r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\RADAR\satellite_sensor_data_S_BAND_SHAR.csv",
        r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\RADAR\satellite_sensor_data_TERLS_C_BAND.csv"
    ]

    graph = Neo4jRadarGraph(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="win33api",
        csv_paths=csv_list
    )

    graph.build_graph()
    graph.close()
    print("✅ Neo4j knowledge graph built successfully for RADAR.")

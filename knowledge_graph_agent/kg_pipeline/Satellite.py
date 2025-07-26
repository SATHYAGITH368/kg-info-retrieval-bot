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
    domain: str = "SATELLITE"
    satellite: str


class Neo4jSatelliteGraph:
   def __init__(self, uri, user, password, satellite_csvs: dict):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.satellite_csvs = satellite_csvs  # dict: {satellite_name: [csv_path, ...]}

   def close(self):
        self.driver.close()

   def load_records(self) -> List[ProductRecord]:
        records = []
        for satellite, csv_list in self.satellite_csvs.items():
            for csv_path in csv_list:
                path = Path(csv_path)
                print(f"📄 Reading SATELLITE CSV: {path.name} (Satellite: {satellite})")
                df = pd.read_csv(path, na_values=["NA"])
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
                        satellite=satellite
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
    # Ensure Domain exists (only one node with name=SATELLITE)
    tx.run("""
        MERGE (d:Domain {name: $domain})
    """, domain=r.domain)

    # Ensure Satellite exists and belongs to Domain
    tx.run("""
        MATCH (d:Domain {name: $domain})
        MERGE (s:Satellite {name: $satellite})
        MERGE (s)-[:BELONGS_TO]->(d)
    """, satellite=r.satellite, domain=r.domain)

    # Create or update Product node
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

    # Link Product -> Satellite
    tx.run("""
        MATCH (p:Product {id: $id}), (s:Satellite {name: $satellite})
        MERGE (p)-[:PROVIDED_BY]->(s)
    """, id=r.id, satellite=r.satellite)



if __name__ == "__main__":
    # Satellite catalog with CSV paths
    satellite_csvs = {
        "EOS-06": [
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\EOS-06\satellite_sensor_data_OCM.csv",
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\EOS-06\satellite_sensor_data_scatterrometer.csv"
        ],
        "EOS-07": [
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\EOS-07\satellite_sensor_data_mhs.csv"
        ],
        "INSAT-3A": [
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\INSAT-3A\satellite_sensor_data_ccd.csv",
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\INSAT-3A\satellite_sensor_data_vhrr.csv"
        ],
        "INSAT-3D": [
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\INSAT-3D\satellite_sensor_data_imager.csv",
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\INSAT-3D\satellite_sensor_data_sounder.csv"
        ],
        "INSAT-3DR": [
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\INSAT-3DR\satellite_sensor_data_imager.csv",
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\INSAT-3DR\satellite_sensor_data_sounder.csv"
        ],
        "INSAT-3DS": [
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\INSAT-3DS\satellite_sensor_data_imager.csv",
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\INSAT-3DS\satellite_sensor_data_sounder.csv"
        ],
        "KALPANA-1": [
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\KALPANA-1\satellite_sensor_data_vhrr.csv"
        ],
        "MEGHATROPIQUES": [
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\MEGHATROPIQUES\satellite_sensor_data_madras.csv",
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\MEGHATROPIQUES\satellite_sensor_data_saphir.csv",
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\MEGHATROPIQUES\satellite_sensor_data_rosa.csv",
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\MEGHATROPIQUES\satellite_sensor_data_scarab.csv"
        ],
        "OCEANSAT-2": [
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\OCEANSAT-2\satellite_sensor_data_scatterometer.csv"
        ],
        "SARAL": [
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\SARAL\satellite_sensor_data_altimeter.csv"
        ],
        "SCATSAT-1": [
            r"C:\Users\AMD\isro1\knowledge_graph_agent\kg_pipeline\Catalog\Satellite\SCATSAT-1\satellite_sensor_data_scatterometer.csv"
        ]
    }

    graph = Neo4jSatelliteGraph(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="win33api",
        satellite_csvs=satellite_csvs
    )

    graph.build_graph()
    graph.close()
    print(" Neo4j knowledge graph built successfully for SATELLITE.")

from kg_pipeline.insitu import Neo4jStationGraph
from kg_pipeline.radar import Neo4jRadarGraph
from kg_pipeline.Satellite import Neo4jSatelliteGraph


class KGAgentSkills:
    def build_kg_from_csv(self, domain: str) -> str:
        domain = domain.upper()
        if domain == "RADAR":
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
        elif domain == "SATELLITE":
            satellite_csvs = {
              
            }
            graph = Neo4jSatelliteGraph(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="win34api",
                satellite_csvs=satellite_csvs
            )
        elif domain == "INSITU":
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
        else:
            return f" Unknown domain: {domain}"

        graph.build_graph()
        graph.close()
        return f" Neo4j knowledge graph built successfully for {domain}."

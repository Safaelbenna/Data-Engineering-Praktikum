from pathlib import Path

LOCAL_DATA_DIR = Path("test data")
VIRTUOSO_DATA_DIR = "/database/test data"

CONTAINER_NAME = "deltagraph_virtuoso"

DBA_USER = "dba"
DBA_PASSWORD = "mysecret"

SPARQL_ENDPOINT = "http://localhost:8890/sparql"

# Graph URI's can be changed
GRAPH_v1 = "http://dbpedia.org/snapshot/v1/mappingbased-objects" 
GRAPH_v2 = "http://dbpedia.org/snapshot/v2/mappingbased-objects"
GRAPH_2021 = "http://dbpedia.org/snapshot/2021/mappingbased-objects" 
GRAPH_2022 = "http://dbpedia.org/snapshot/2022/mappingbased-objects"
GRAPH_DELTA_ADDED_S   = "http://dbpedia.org/delta/added_small"
GRAPH_DELTA_REMOVED_S = "http://dbpedia.org/delta/removed_small"
GRAPH_DELTA_ADDED_B   = "http://dbpedia.org/delta/added_big"
GRAPH_DELTA_REMOVED_B = "http://dbpedia.org/delta/removed_big"
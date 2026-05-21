from pathlib import Path

LOCAL_DATA_DIR = Path("data/Decompressed-files")
VIRTUOSO_DATA_DIR = "/database/data/Decompressed-files"

CONTAINER_NAME = "deltagraph_virtdb"

DBA_USER = "dba"
DBA_PASSWORD = "mysecret"

SPARQL_ENDPOINT = "http://localhost:8890/sparql"

# Graph URI's can be changed
GRAPH_2021 = "http://dbpedia.org/snapshot/2021/mappingbased-objects" 
GRAPH_2022 = "http://dbpedia.org/snapshot/2022/mappingbased-objects"
from pathlib import Path

LOCAL_DATA_DIR = Path("test data")
VIRTUOSO_DATA_DIR = "/database/test data"

CONTAINER_NAME = "deltagraph_virtuoso"

DBA_USER = "dba"
DBA_PASSWORD = "mysecret"
BASE_URI = "http://dbpedia.org"


SPARQL_ENDPOINT = "http://localhost:8890/sparql"

def get_graph_uri(dataset_name: str, tag: str, version1: str, version2: str) -> str:
    return f"{BASE_URI}/delta/{dataset_name}/{version1}_{version2}/{tag}"




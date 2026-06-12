from pathlib import Path

LOCAL_DATA_DIR = Path("test data")
VIRTUOSO_DATA_DIR = "/database/test data"

CONTAINER_NAME = "deltagraph_virtuoso"

DBA_USER = "dba"
DBA_PASSWORD = "mysecret"

SPARQL_ENDPOINT = "http://localhost:8890/sparql"

# Graph URI's can be changed
ADDED_GRAPH_S = "http://dbpedia.org/delta/added_small" 
REMOVED_GRAPH_S = "http://dbpedia.org/delta/removed_small"
ADDED_GRAPH_B = "http://dbpedia.org/delta/added_big" 
REMOVED_GRAPH_B = "http://dbpedia.org/delta/removed_big"

# placeholders for the user's input
BATCH_SIZE = 100
NUMBER_OF_BATCHES = 10
NUMBER_OF_DELETIONS_PER_BATCH = 50
NUMBER_OF_ADDITIONS_PER_BATCH = 50

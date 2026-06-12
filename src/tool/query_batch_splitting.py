from config import NUMBER_OF_BATCHES, NUMBER_OF_ADDITIONS_PER_BATCH, NUMBER_OF_DELETIONS_PER_BATCH
from test_querying import run_query


def fetch_triples(graph_uri: str, limit: int, offset: int) -> bytes:
    query = f"""
        SELECT {{ ?s ?p ?o }}
        WHERE {{
        GRAPH <{graph_uri}> {{ ?s ?p ?o }}
        }}
        LIMIT {limit}
        OFFSET {offset}
        """
    resp = run_query(query)
    resp.raise_for_status() #Raises an exception if the HTTP response status code indicates an error (4xx or 5xx)
    return resp

def generate_batches(graph_uri_added: str, graph_uri_deleted: str) -> None:
    
    for i in range(NUMBER_OF_BATCHES):
        additions = fetch_triples(graph_uri_added,   NUMBER_OF_ADDITIONS_PER_BATCH, i * NUMBER_OF_ADDITIONS_PER_BATCH)
        deletions = fetch_triples(graph_uri_deleted, NUMBER_OF_DELETIONS_PER_BATCH, i * NUMBER_OF_DELETIONS_PER_BATCH)
      
        batch = {
        "additions": additions,
        "length_additions": len(additions.strip().splitlines()),       
        "deletions": deletions,
        "length_deletions": len(deletions.strip().splitlines())  
        }
        
        print(f"--- Batch {i+1} ---")
        print(batch)
        print()

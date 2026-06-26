from config import SPARQL_ENDPOINT
import time
import threading
import requests


def fetch_triples(graph_uri: str, limit: int, offset: int) -> str:
    query = f"""
        CONSTRUCT {{ ?s ?p ?o }}
        WHERE {{
        GRAPH <{graph_uri}> {{ ?s ?p ?o }}
        }}
        LIMIT {limit}
        OFFSET {offset}
        """
    resp = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "text/plain"},
        timeout=120,
    )
    resp.raise_for_status() #Raises an exception if the HTTP response status code indicates an error (4xx or 5xx)
    return resp.text

def count_triples_in_text(text: str) -> int:
    text = text.strip()
    if not text or text.startswith("# Empty"):
        return 0
    return len(text.splitlines())

def generate_batches(graph_uri_added: str,
    graph_uri_deleted: str,
    num_batches: int,
    additions_per_batch: int,
    deletions_per_batch: int) -> None:

    def helper(name, graph_uri, limit, offset):
        results[name] = fetch_triples(graph_uri, limit, offset)
    
    for i in range(num_batches):

        results = {}

        start_add = time.perf_counter()

        thread_add = threading.Thread(target=helper, args=("additions", graph_uri_added, additions_per_batch, i * additions_per_batch))
        thread_del = threading.Thread(target=helper, args=("deletions", graph_uri_deleted, deletions_per_batch, i * deletions_per_batch))

        thread_add.start()
        thread_del.start()
        thread_add.join()
        thread_del.join()

        end_del = time.perf_counter()
      
        batch = {
        "additions": results["additions"],
        "length_additions": count_triples_in_text(results["additions"]),       
        "deletions": results["deletions"],
        "length_deletions": count_triples_in_text(results["deletions"]) 
        }
        
        print(f"--- Batch {i+1} ---")
        print(batch)
        print("time: ", end_del - start_add)
        print()
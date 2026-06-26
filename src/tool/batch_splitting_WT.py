from config import SPARQL_ENDPOINT
import requests
import time 


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

    total_additions_time = 0
    total_deletions_time = 0

    for i in range(num_batches):

        start = time.perf_counter()
        additions = fetch_triples(graph_uri_added, additions_per_batch, i * additions_per_batch)
        additions_seconds = time.perf_counter() - start
        total_additions_time += additions_seconds
        print(f"Additions fetch time: {additions_seconds:.2f} seconds ({additions_seconds/60:.2f} min)")

        start = time.perf_counter()
        deletions = fetch_triples(graph_uri_deleted, deletions_per_batch, i * deletions_per_batch)
        deletions_seconds = time.perf_counter() - start
        total_deletions_time += deletions_seconds
        print(f"Deletions fetch time: {deletions_seconds:.2f} seconds ({deletions_seconds/60:.2f} min)")

        batch = {
            "additions": additions,
            "length_additions": count_triples_in_text(additions),
            "deletions": deletions,
            "length_deletions": count_triples_in_text(deletions)
        }

        print(f"--- Batch {i+1} ---")
        print(batch)
        print()

    print(f"Avg additions fetch time: {total_additions_time/num_batches:.2f} seconds")
    print(f"Avg deletions fetch time: {total_deletions_time/num_batches:.2f} seconds")

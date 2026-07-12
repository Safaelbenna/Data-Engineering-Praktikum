from config import SPARQL_ENDPOINT
from test_querying import run_query
import requests
import time 
import csv
import io
from SPARQLWrapper import SPARQLWrapper,CSV


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
        params={"query": query, "format": "application/n-triples"},
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




#class-based batching

def get_top_classes_by_entity_count(delta_graph_uri: str, graph_uri: str, top_n: int=1000) -> dict:

    query = f"""
    SELECT ?class (COUNT(DISTINCT ?s) AS ?entity_count)
    WHERE {{
        GRAPH <{delta_graph_uri}> {{ ?s ?p ?o }}
        GRAPH <{graph_uri}> {{ ?s a ?class }}
    }}
    GROUP BY ?class
    ORDER BY DESC(?entity_count)
    LIMIT {top_n}
    """
    raw_csv = run_query(query)
    decoded = raw_csv.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    return {row["class"]: int(row["entity_count"]) for row in reader}    

def get_top_classes_combined(
    added_graph_uri: str,
    removed_graph_uri: str,
    graph_uri_v1: str,
    graph_uri_v2: str,
    top_n: int = 10
) -> list[dict]:

    added_counts = get_top_classes_by_entity_count(added_graph_uri, graph_uri_v2)
    removed_counts = get_top_classes_by_entity_count(removed_graph_uri, graph_uri_v1)

    all_classes = set(added_counts) | set(removed_counts)

    combined = [
        {
            "class": class_uri,
            "added": added_counts.get(class_uri, 0),
            "removed": removed_counts.get(class_uri, 0),
        }
        for class_uri in all_classes
    ]

    combined.sort(key=lambda c: c["added"] + c["removed"], reverse=True)
    return combined[:top_n]

def get_entities_for_class(delta_graph_uri: str, graph_uri: str, class_uri: str, limit: int, offset: int) -> list[str]:
 #return the entities in the range the user set

    query = f"""
    SELECT DISTINCT ?s
    WHERE {{
        GRAPH <{delta_graph_uri}> {{ ?s ?p ?o }}
        GRAPH <{graph_uri}> {{ ?s a <{class_uri}> }}
    }}
    LIMIT {limit} OFFSET {offset}
    """
    raw_csv = run_query(query)
    decoded = raw_csv.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
 
    return [row["s"] for row in reader]    

def get_triples_for_entities(delta_graph_uri: str, entity_uris: list[str], limit: int, offset: int) -> list[tuple]:
    #get all the triples of the fetches entities 
    if not entity_uris:
        return []
 
    values_clause = " ".join(f"<{uri}>" for uri in entity_uris)
    query = f"""
    CONSTRUCT {{ ?s ?p ?o }}
    WHERE {{
        GRAPH <{delta_graph_uri}> {{ ?s ?p ?o }}
        VALUES ?s {{ {values_clause} }}
    }}
    """

    resp = requests.post(
        SPARQL_ENDPOINT,
        data={"query": query, "format": "application/n-triples"},
        timeout=120,
    )
    resp.raise_for_status()

    return resp.text  

def generate_class_based_batches(
    graph_uri_added: str,
    graph_uri_deleted: str,
    graph_uri_v1: str,
    graph_uri_v2: str,
    class_uri: str,
    num_batches: int,
    entities_added_per_batch: int,
    entities_removed_per_batch: int,
) -> list[dict]: 

    total_additions_time = 0
    total_deletions_time = 0
    batches = []

    for i in range(num_batches):

        start = time.perf_counter()
        added_entities = get_entities_for_class(
            graph_uri_added, graph_uri_v2, class_uri,
            limit=entities_added_per_batch, offset=i * entities_added_per_batch
        )
        additions = get_triples_for_entities(graph_uri_added, added_entities, limit=entities_added_per_batch, offset=i * entities_added_per_batch)
        additions_seconds = time.perf_counter() - start
        total_additions_time += additions_seconds
        print(f"Additions fetch time: {additions_seconds:.2f} seconds ({additions_seconds/60:.2f} min)")

        start = time.perf_counter()
        removed_entities = get_entities_for_class(
            graph_uri_deleted, graph_uri_v1, class_uri,
            limit=entities_removed_per_batch, offset=i * entities_removed_per_batch
        )
        deletions = get_triples_for_entities(graph_uri_deleted, removed_entities, limit=entities_removed_per_batch, offset=i * entities_removed_per_batch)
        deletions_seconds = time.perf_counter() - start
        total_deletions_time += deletions_seconds
        print(f"Deletions fetch time: {deletions_seconds:.2f} seconds ({deletions_seconds/60:.2f} min)")

        batch = {
            "additions": additions,
            "length_additions": len(additions),
            "deletions": deletions,
            "length_deletions": len(deletions)
        }
        batches.append(batch)

        print(f"--- Batch {i+1} ---")
        print(batch)
        print()
        return batches

    print(f"Avg additions fetch time: {total_additions_time/num_batches:.2f} seconds")
    print(f"Avg deletions fetch time: {total_deletions_time/num_batches:.2f} seconds") 
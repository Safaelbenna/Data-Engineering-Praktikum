from load_to_virtuoso import load_all_ttl_files
from test_querying import run_query, graph_exists
from config import ADDED_GRAPH_S, REMOVED_GRAPH_S, ADDED_GRAPH_B, REMOVED_GRAPH_B
import subprocess


def preview_graph(graph_uri: str) -> None:
    query = f"""
    SELECT ?s ?p ?o
    WHERE {{
      GRAPH <{graph_uri}> {{
        ?s ?p ?o
      }}
    }}
    LIMIT 10
    """

    result = run_query(query)

    print(f"Preview of {graph_uri}")
    print("-" * 50)
    print(result)

print("Loading TTL files...")
""" 
    can be removed later since it is only for snapshots that are not loaded yet 
"""
load_all_ttl_files()

""" 
    for debugging purposes to make sure that the graphs are actually loaded
"""
print("\nChecking if graphs exist...")
print("added graph exists:", graph_exists(ADDED_GRAPH_S))    
print("removed graph exists:", graph_exists(REMOVED_GRAPH_S))
print("added graph exists:", graph_exists(ADDED_GRAPH_B))    
print("removed graph exists:", graph_exists(REMOVED_GRAPH_B))


print("\nPreviewing 10 first triples...")
preview_graph(ADDED_GRAPH_S)
preview_graph(REMOVED_GRAPH_S)
preview_graph(ADDED_GRAPH_B)
preview_graph(REMOVED_GRAPH_B)






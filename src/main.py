from load_to_virtuoso import load_all_ttl_files
from test_querying import run_query, graph_exists
from config import GRAPH_2021, GRAPH_2022

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
print("2021 graph exists:", graph_exists(GRAPH_2021))
print("2022 graph exists:", graph_exists(GRAPH_2022))

print("\nPreviewing triples...")
preview_graph(GRAPH_2021)
preview_graph(GRAPH_2022)



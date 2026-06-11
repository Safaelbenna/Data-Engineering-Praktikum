from load_to_virtuoso import load_all_ttl_files
from test_querying import run_query, graph_exists
from config import GRAPH_v1, GRAPH_v2, GRAPH_2021, GRAPH_2022
from delta_computation import additions_computation, deletions_computation, convert_isql_output_to_nt
import time


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

start = time.perf_counter()
print("Loading TTL files...")

load_all_ttl_files()

""" 
    for debugging purposes to make sure that the graphs are actually loaded
"""
print("\nChecking if graphs exist...")
print("v1 graph exists:", graph_exists(GRAPH_v1))
print("v2 graph exists:", graph_exists(GRAPH_v2))
print("2021 graph exists:", graph_exists(GRAPH_2021))
print("2022 graph exists:", graph_exists(GRAPH_2022))





print("\nPreviewing 10 first triples...")
preview_graph(GRAPH_v1)
preview_graph(GRAPH_v2)
preview_graph(GRAPH_2021)
preview_graph(GRAPH_2022)


#print("\nDelta Computation")
#additions_computation(GRAPH_v1, GRAPH_v2)
#deletions_computation(GRAPH_v1, GRAPH_v2)
#additions_computation(GRAPH_2021, GRAPH_2022)
#deletions_computation(GRAPH_2021, GRAPH_2022)
#convert_isql_output_to_nt("additions_2022_minus_2021.txt", "additions_2022_minus_2021.ttl")

end = time.perf_counter()
seconds = end - start

print(f"Total runtime of Pipeline.\n")
print(f"Time: {seconds:.2f} seconds")
print(f"Time: {seconds/60:.2f} minutes")







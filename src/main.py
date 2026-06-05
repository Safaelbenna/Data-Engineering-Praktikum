from load_to_virtuoso import load_all_ttl_files
from test_querying import run_query, graph_exists
from config import GRAPH_v1, GRAPH_v2, GRAPH_2021, GRAPH_2022, GRAPH_DELTA_ADDED_S, GRAPH_DELTA_REMOVED_S, GRAPH_DELTA_REMOVED_B, GRAPH_DELTA_ADDED_B
from delta_computation import additions_computation, deletions_computation, store_delta_in_virtuoso, export_delta_as_trig
import subprocess
from rdflib import Dataset, URIRef


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
print("v1 graph exists:", graph_exists(GRAPH_v1))
print("v2 graph exists:", graph_exists(GRAPH_v2))
print("2021 graph exists:", graph_exists(GRAPH_2021))
print("2022 graph exists:", graph_exists(GRAPH_2022))

print("added graph exists:", graph_exists(GRAPH_DELTA_ADDED_S))    
print("removed graph exists:", graph_exists(GRAPH_DELTA_REMOVED_S))

sql = "SPARQL SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } };\nexit;\n"
result = subprocess.run(
    ["docker", "exec", "-i", "deltagraph_virtuoso", "isql", "1111", "dba", "mysecret"],
    input=sql, text=True, capture_output=True
)
print(result.stdout)


print("\nPreviewing 10 first triples...")
preview_graph(GRAPH_v1)
preview_graph(GRAPH_v2)
preview_graph(GRAPH_2021)
preview_graph(GRAPH_2022)
preview_graph(GRAPH_DELTA_ADDED_S)
preview_graph(GRAPH_DELTA_REMOVED_S)

store_delta_in_virtuoso(GRAPH_v1, GRAPH_v2)
print("added graph exists:", graph_exists(GRAPH_DELTA_ADDED_S))    
print("removed graph exists:", graph_exists(GRAPH_DELTA_REMOVED_S))
preview_graph(GRAPH_DELTA_ADDED_S)
preview_graph(GRAPH_DELTA_REMOVED_S)
#export_delta_as_trig("delta_.trig")

print("\nDelta Computation")
additions_computation(GRAPH_v1, GRAPH_v2)
deletions_computation(GRAPH_v1, GRAPH_v2)
additions_computation(GRAPH_2021, GRAPH_2022)
deletions_computation(GRAPH_2021, GRAPH_2022)


# #validating whether it works back with rdflib
# print("\nValidating with rdflib...")
# reloaded = Dataset()
# reloaded.parse("delta_.trig", format="trig")
# added_graph   = reloaded.graph(URIRef("http://dbpedia.org/delta/added"))
# removed_graph = reloaded.graph(URIRef("http://dbpedia.org/delta/removed"))
# print(f"Added triples   : {len(added_graph)}")
# print(f"Removed triples : {len(removed_graph)}")




import subprocess
import time
from rdflib import Dataset, URIRef
from test_querying import run_query, graph_exists
from config import GRAPH_DELTA_ADDED_S, GRAPH_DELTA_REMOVED_S, GRAPH_DELTA_ADDED_B, GRAPH_DELTA_REMOVED_B
import csv
import io

#delta computation with storing into files
def additions_computation(graph_uri1: str, graph_uri2: str) -> None:
    query = f"""
    SPARQL
    SELECT ?s ?p ?o
    WHERE {{
    GRAPH <{graph_uri2}> {{
        ?s ?p ?o .
    }}

    FILTER NOT EXISTS {{
        GRAPH <{graph_uri1}> {{
        ?s ?p ?o .
        }}
    }}
    }};
    exit;
    """

    start = time.time()
    value = "v" if ("v" in graph_uri1) else "202"

    print("\nComputing additions...")

    with open(f"additions_{value}2_minus_{value}1.txt", "w") as output:
        subprocess.run(
            ["docker", "exec", "-i", "deltagraph_virtuoso", "isql", "1111", "dba", "mysecret"],
            input=query,
            stdout=output,
            text=True
        )

    end = time.time()

    with open(f"additions_{value}2_minus_{value}1.txt", "r", errors="replace") as file:
        for line in file:
            if "Rows. --" in line:
                parts = line.split()
                rows, msec = int(parts[0]), int(parts[3])
                print(f"{rows:,} rows in ({msec})ms {msec/1000:.1f}s ({msec/60000:.1f} min)")


    seconds = end - start

    print("Finished")
    print(f"Time: {seconds:.2f} seconds")
    print(f"Time: {seconds/60:.2f} minutes")

def deletions_computation(graph_uri1: str, graph_uri2: str) -> None:
    query = f"""
    SPARQL
    SELECT ?s ?p ?o
    WHERE {{
    GRAPH <{graph_uri1}> {{
        ?s ?p ?o .
    }}

    FILTER NOT EXISTS {{
        GRAPH <{graph_uri2}> {{
        ?s ?p ?o .
        }}
    }}
    }};
    exit;
    """

    start = time.time()
    value = "v" if ("v" in graph_uri1) else "202"

    print("\nComputing deletions...")

    with open(f"deletions_{value}1_minus_{value}2.txt", "w") as output:
        subprocess.run(
            ["docker", "exec", "-i", "deltagraph_virtuoso", "isql", "1111", "dba", "mysecret"],
            input=query,
            stdout=output,
            text=True
        )

    end = time.time()

    with open(f"deletions_{value}1_minus_{value}2.txt", "r", errors="replace") as file:
        for line in file:
            if "Rows. --" in line:
                parts = line.split()
                rows, msec = int(parts[0]), int(parts[3])
                print(f"{rows:,} rows in ({msec})ms {msec/1000:.1f}s ({msec/60000:.1f} min)")

    seconds = end - start

    print("Finished")
    print(f"Time: {seconds:.2f} seconds")
    print(f"Time: {seconds/60:.2f} minutes")

#delta computation with storing into virtuoso

def store_delta_in_virtuoso(graph_uri1: str, graph_uri2: str) -> None:
    command = [
        "docker", "exec", "-i", "deltagraph_virtuoso",
        "isql", "1111", "dba", "mysecret",
    ]

    value = "small" if ("v" in graph_uri1) else "big"
    
    if (value == "small" and graph_exists(GRAPH_DELTA_ADDED_S)) or (value == "big" and graph_exists(GRAPH_DELTA_ADDED_B)):
        print(f"Added delta {value} graph already exists, skipping...")
    else:
        print(f"\nStoring added delta into Virtuoso...")
        start = time.time()
        added_query = f"SPARQL INSERT INTO <http://dbpedia.org/delta/added_{value}> {{ ?s ?p ?o }} WHERE {{ GRAPH <{graph_uri2}> {{ ?s ?p ?o }} FILTER NOT EXISTS {{ GRAPH <{graph_uri1}> {{ ?s ?p ?o }} }} }};\nexit;\n"
        result = subprocess.run(command, input=added_query, text=True, capture_output=True)
        end = time.time()
        seconds = end - start
        if result.returncode != 0:
            raise RuntimeError(f"Failed storing added delta: {result.stderr}")
        print("Finished")
        print(f"Time: {seconds:.2f} seconds")
        print(f"Time: {seconds/60:.2f} minutes")

    if (value == "small" and graph_exists(GRAPH_DELTA_REMOVED_S)) or (value == "big" and graph_exists(GRAPH_DELTA_REMOVED_B)):
        print(f"Removed delta {value} graph already exists, skipping...")
    else:
        print(f"\nStoring removed delta into Virtuoso...")
        start = time.time()
        removed_query = f"SPARQL INSERT INTO <http://dbpedia.org/delta/removed_{value}> {{ ?s ?p ?o }} WHERE {{ GRAPH <{graph_uri1}> {{ ?s ?p ?o }} FILTER NOT EXISTS {{ GRAPH <{graph_uri2}> {{ ?s ?p ?o }} }} }};\nexit;\n"
        result = subprocess.run(command, input=removed_query, text=True, capture_output=True)
        end = time.time()
        seconds = end - start
        if result.returncode != 0:
            raise RuntimeError(f"Failed storing removed delta: {result.stderr}")
        print("Finished")
        print(f"Time: {seconds:.2f} seconds")
        print(f"Time: {seconds/60:.2f} minutes")


# def export_delta_as_trig(output_path: str, graph_uri1: str) -> None:
    
#     value = "v" if ("v" in graph_uri1) else "202"
#     delta_graph = Dataset()
#     added_uri   = URIRef("http://dbpedia.org/delta/added_{value}")
#     removed_uri = URIRef("http://dbpedia.org/delta/removed_{value}")

#     print("\nExporting delta to TriG...")
#     start = time.time()

#     # fetch added triples
#     added_csv = run_query("""
#         SELECT ?s ?p ?o WHERE {
#             GRAPH <http://dbpedia.org/delta/added_{value}> { ?s ?p ?o }
#         }
#     """)
#     reader = csv.DictReader(io.StringIO(added_csv.decode("utf-8")))
#     for row in reader:
#         delta_graph.add((URIRef(row["s"]), URIRef(row["p"]), URIRef(row["o"]), added_uri))

#     # fetch removed triples
#     removed_csv = run_query("""
#         SELECT ?s ?p ?o WHERE {
#             GRAPH <http://dbpedia.org/delta/removed_{value}> { ?s ?p ?o }
#         }
#     """)
#     reader = csv.DictReader(io.StringIO(removed_csv.decode("utf-8")))
#     for row in reader:
#         delta_graph.add((URIRef(row["s"]), URIRef(row["p"]), URIRef(row["o"]), removed_uri))

#     delta_graph.serialize(output_path, format="trig")

#     end = time.time()
#     seconds = end - start
#     print(f"Finished — exported to {output_path}")
#     print(f"Time: {seconds:.2f} seconds")

import subprocess
import time
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

    seconds = end - start

    print("Finished")
    print(f"Time: {seconds:.2f} seconds")
    print(f"Time: {seconds/60:.2f} minutes")
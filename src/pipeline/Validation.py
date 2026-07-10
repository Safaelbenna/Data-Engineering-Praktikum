from test_querying import graph_exists
from config import GRAPH_2021, GRAPH_2022, CONTAINER_NAME
import subprocess
#from tool.config import ADDED_GRAPH_B, REMOVED_GRAPH_B
ADDED_GRAPH_B = "http://dbpedia.org/delta/added_big" 
REMOVED_GRAPH_B = "http://dbpedia.org/delta/removed_big"

def validate() -> None:
    updated_graph_uri = "http://dbpedia.org/snapshot/updated"

    # original Snapshot loading into the updated graph
    # if graph_exists(updated_graph_uri):
    #         print(f"Already loaded: {updated_graph_uri}")
    # else:
    query = f"""
        SPARQL DEFINE sql:log-enable 3
        INSERT INTO GRAPH <{updated_graph_uri}> {{
            ?s ?p ?o
        }}
        WHERE {{
            GRAPH <{GRAPH_2021}> {{ ?s ?p ?o }}
        }};
    exit;
    """

    result = subprocess.run(
        ["docker", "exec", "-i", CONTAINER_NAME, "isql", "1111", "dba", "mysecret"],
        input=query,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("copying of old graph failed.")
    
    print("first insert: ", result.stdout)

    # deleting deletions from the updated graph
    query_delete = f"""
    SPARQL DEFINE sql:log-enable 3
    DELETE FROM GRAPH <{updated_graph_uri}> {{
        ?s ?p ?o
    }}
    WHERE {{
        GRAPH <{REMOVED_GRAPH_B}> {{ ?s ?p ?o }}
    }};
    exit;
    """
    result_delete = subprocess.run(
            ["docker", "exec", "-i", CONTAINER_NAME, "isql", "1111", "dba", "mysecret"],
            input=query_delete,
            text=True,
            capture_output=True,
        )

    if result_delete.returncode != 0:
        print(result_delete.stderr)
        raise RuntimeError("deleting of deletions in the updated graph failed.")

    # adding additions to the updated graph
    query_add = f"""
    SPARQL DEFINE sql:log-enable 3
    INSERT INTO GRAPH <{updated_graph_uri}> {{
        ?s ?p ?o
    }}
    WHERE {{
        GRAPH <{ADDED_GRAPH_B}> {{ ?s ?p ?o }}
    }};
    exit;
    """

    result_add = subprocess.run(
            ["docker", "exec", "-i", CONTAINER_NAME, "isql", "1111", "dba", "mysecret"],
            input=query_add,
            text=True,
            capture_output=True,
        )

    if result_add.returncode != 0:
        print(result_add.stderr)
        raise RuntimeError("adding of additions in the updated graph failed.")

    # to verify the updated graph is same as the new snapshot -> we count how many triples are diffrent
    query_verify = f"""
    SPARQL
    SELECT COUNT(*) WHERE {{
        GRAPH <{updated_graph_uri}> {{ ?s ?p ?o }}
        FILTER NOT EXISTS {{ GRAPH <{GRAPH_2022}> {{ ?s ?p ?o }} }}
    }};
    exit;
    """
    result_verify = subprocess.run(
            ["docker", "exec", "-i", CONTAINER_NAME, "isql", "1111", "dba", "mysecret"],
            input=query_verify,
            text=True,
            capture_output=True,
        )

    if result_verify.returncode != 0:
        print(result_verify.stderr)
        raise RuntimeError("verification of the updated graph failed.")
    print(result_verify.stdout)


    query_verify2 = f"""
    SPARQL
    SELECT COUNT(*) WHERE {{
        GRAPH <{GRAPH_2022}> {{ ?s ?p ?o }}
        FILTER NOT EXISTS {{ GRAPH <{updated_graph_uri}> {{ ?s ?p ?o }} }}
    }};
    exit;
    """
    result_verify2 = subprocess.run(
            ["docker", "exec", "-i", CONTAINER_NAME, "isql", "1111", "dba", "mysecret"],
            input=query_verify2,
            text=True,
            capture_output=True,
        )

    if result_verify2.returncode != 0:
        print(result_verify2.stderr)
        raise RuntimeError("verification2 of the updated graph failed.")
    print(result_verify2.stdout)

print("Started Validation...")
validate()
print("Ended Validation...")
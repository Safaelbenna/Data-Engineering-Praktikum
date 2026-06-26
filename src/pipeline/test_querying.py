from SPARQLWrapper import SPARQLWrapper, CSV
from config import SPARQL_ENDPOINT


def run_query(query: str) -> dict:
    """
    Send a SPARQL query to Virtuoso and return the result as CSV.
    """
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(CSV)

    return sparql.query().convert()


def graph_exists(graph_uri: str) -> bool:
    """
    Check whether the named graph already exists.
    """
    query = f"""
    ASK {{
      GRAPH <{graph_uri}> {{
        ?s ?p ?o
      }}
    }}
    """

    result = run_query(query)
    text = result.decode("utf-8").strip()
    value = text.splitlines()[-1]
    return bool(int(value))


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


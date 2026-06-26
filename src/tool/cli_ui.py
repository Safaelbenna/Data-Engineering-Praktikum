import json
from pathlib import Path
import time
import pyfiglet
import requests
from rich.console import Console
from config import LOCAL_DATA_DIR
import questionary
from batch_splitting_WT import generate_batches
from load_to_virtuoso import load_selected_delta_files






console = Console()

SPARQL_ENDPOINT = "http://localhost:8890/sparql"


def show_banner():
    banner = pyfiglet.figlet_format("DeltaGraph")
    console.print(banner, style="yellow")
    console.print("A CLI for batching knowledge graph deltas\n", style="green")


def get_available_names() -> dict:
    names = {}

    for filepath in LOCAL_DATA_DIR.glob("*.ttl"):
        filename = filepath.stem

        if filename.startswith("additions_"):
            rest = filename[len("additions_"):]        
            parts = rest.split("_minus_")              
            v1 = parts[1]                              
            v2 = parts[0].split("_")[-1]              
            dataset_name = "_".join(parts[0].split("_")[:-1])

            if dataset_name not in names:
                names[dataset_name] = {}
            names[dataset_name][v1] = v1
            names[dataset_name][v2] = v2

    return names

triple_counts = {}

def get_triple_count(graph_uri: str) -> int:
    if graph_uri in triple_counts:
        return triple_counts[graph_uri]

    query = f"""
        SELECT COUNT(*) AS ?count
        WHERE {{ GRAPH <{graph_uri}> {{ ?s ?p ?o }} }}
    """
    resp = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "application/sparql-results+json"},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    count = int(data["results"]["bindings"][0]["count"]["value"])
    triple_counts[graph_uri] = count
    return count

def ask_validated_int(message: str, max_value: int, max_value_label: str) -> int:
    def validator(text: str):
        if not text.strip().isdigit():
            return "Please enter a positive whole number"
        value = int(text.strip())
        if value < 0:
            return "Value must be greater or equal to 0"
        if value > max_value:
            return f"Value must be ≤ {max_value} ({max_value_label})"
        return True

    answer = questionary.text(message, validate=validator).ask()
    return int(answer)


def get_user_input() -> dict:
    show_banner()

 
   
    STATE_FILE = Path(__file__).parent.parent / "user_input.json"
    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    name = state["name"]
    v1 = state["v1"]
    v2 = state["v2"]
    additions_file = state["additions_file"]
    deletions_file = state["deletions_file"]

    console.print(f"Start the batch splitting for {name}. The versions used are {v1} and {v2}\n", style="green")

    added_graph_uri   = f"http://dbpedia.org/delta/{name}/added"
    deleted_graph_uri = f"http://dbpedia.org/delta/{name}/removed"
        
    console.print(f"Loading delta files into virtuoso is starting...\n", style="blue")
    load_selected_delta_files(additions_file, deletions_file)
   
    

    total_additions = get_triple_count(added_graph_uri)
    total_deletions = get_triple_count(deleted_graph_uri)

    console.print(
        f"Available: {total_additions:,} additions, {total_deletions:,} deletions.",
        style="cyan"
    )

    max_batches = total_additions + total_deletions
    num_batches = ask_validated_int(
        "Number of batches:", max_batches, "total additions + deletions available"
    )

    additions_per_batch = ask_validated_int(
        "Additions per batch:", total_additions, "total additions available"
    )
    deletions_per_batch = ask_validated_int(
        "Deletions per batch:", total_deletions, "total deletions available"
    )
    if ((additions_per_batch == 0 and deletions_per_batch == 0) or num_batches == 0):
        print("Empty batches")

    elif (deletions_per_batch == 0):
        num_batches = min(total_additions // additions_per_batch, num_batches)
    elif additions_per_batch == 0:
        num_batches = min(total_deletions // deletions_per_batch, num_batches)

    else:
        num_batches = min(min(total_additions // additions_per_batch, total_deletions // deletions_per_batch), num_batches)


    return {
        "name": name,
        "older_version": v1,
        "newer_version": v2,
        "added_graph_uri": added_graph_uri,
        "deleted_graph_uri": deleted_graph_uri,
        "num_batches": num_batches,
        "additions_per_batch": additions_per_batch,
        "deletions_per_batch": deletions_per_batch,
    }


def main():
    start = time.perf_counter()

    params = get_user_input()
    console.print(params, style="blue")
    if ((params["additions_per_batch"] == 0 and params["deletions_per_batch"] == 0) or params["num_batches"] == 0):
        exit(0)

    generate_batches(
        graph_uri_added=params["added_graph_uri"],
        graph_uri_deleted=params["deleted_graph_uri"],
        num_batches=params["num_batches"],
        additions_per_batch=params["additions_per_batch"],
        deletions_per_batch=params["deletions_per_batch"]
    )

    seconds = time.perf_counter() - start
    console.print(f"\nTotal runtime of tool: {seconds:.2f} seconds ({seconds/60:.2f} min)", style="yellow")

main()    



    
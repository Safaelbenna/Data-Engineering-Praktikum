import time

import pyfiglet
import requests
from rich.console import Console
from config import LOCAL_DATA_DIR, get_graph_uri, SPARQL_ENDPOINT, get_graph_snapshot_uri
import questionary
from batch_splitting_WT import generate_batches, get_top_classes_combined, get_top_classes_by_entity_count,generate_class_based_batches
from load_to_virtuoso import load_selected_delta_files, load_selected_ttl_files
console = Console()





def show_banner():
    banner = pyfiglet.figlet_format("DeltaGraph")
    console.print(banner, style="yellow")
    console.print("Tool: A CLI for batching knowledge graph deltas\n", style="green")


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

#class based methods
def select_class_for_batching(top_classes: list[dict]) -> dict:
    if not top_classes:
        print("No classes with changed entities found.")
        return None

    choices = [
        questionary.Choice(
            title=f"{c['class'].split('/')[-1]:20} ({c['added']} added / {c['removed']} removed)",
            value=c
        )
        for c in top_classes
    ]

    selected = questionary.select(
        "Which class do you want to batch updates for?",
        choices=choices
    ).ask()

    return selected

def get_class_batch_settings(selected_class: dict) -> dict:
    max_added = selected_class["added"]
    max_removed = selected_class["removed"]

    num_batches = ask_validated_int(
        "Number of batches:", max_added + max_removed, "total added + removed entities available"
    )

    entities_added_per_batch = ask_validated_int(
        "Entities to add per batch:", max_added, "total added entities available"
    )

    entities_removed_per_batch = ask_validated_int(
        "Entities to remove per batch:", max_removed, "total removed entities available"
    )

    if ((entities_added_per_batch == 0 and entities_removed_per_batch == 0) or num_batches == 0):
        print("Empty batches")

    elif (entities_removed_per_batch == 0):
        num_batches = min(max_added // entities_added_per_batch, num_batches)
    elif entities_added_per_batch == 0:
        num_batches = min(max_removed // entities_removed_per_batch, num_batches)

    else:
        num_batches = min(min(max_added // entities_added_per_batch, max_removed // entities_removed_per_batch), num_batches)

    return {
        "num_batches": num_batches,
        "entities_added_per_batch": entities_added_per_batch,
        "entities_removed_per_batch": entities_removed_per_batch,
    }

def get_class_based_user_input(graph_uri_v1: str, graph_uri_v2: str, added_graph_uri: str, deleted_graph_uri: str) -> dict:


    console.print("Finding top classes by number of changed entities...\n", style="blue")
    top_classes = get_top_classes_combined(
        added_graph_uri, deleted_graph_uri,
        graph_uri_v2, graph_uri_v1,
        10
    )

    selected_class = select_class_for_batching(top_classes)
    if selected_class is None:
        raise SystemExit(1)

    console.print(
        f"Selected class: {selected_class['class'].split('/')[-1]} "
        f"({selected_class['added']:,} added / {selected_class['removed']:,} removed)",
        style="cyan"
    )

    batch_settings = get_class_batch_settings(selected_class)

    return {
        "mode": "class",
        "added_graph_uri": added_graph_uri,
        "deleted_graph_uri": deleted_graph_uri,
        "graph_uri_v1": graph_uri_v1,
        "graph_uri_v2": graph_uri_v2,
        "class_uri": selected_class["class"],
        "num_batches": batch_settings["num_batches"],
        "entities_added_per_batch": batch_settings["entities_added_per_batch"],
        "entities_removed_per_batch": batch_settings["entities_removed_per_batch"],
    }


def get_user_input() -> dict:
    show_banner()

    available_names = get_available_names()

    valid_names = [name for name, versions in available_names.items() if len(versions) >= 2]

    if not valid_names:
        console.print("No datasets with two or more versions found in test data.", style="red")
        raise SystemExit(1)

    name = questionary.select(
        "Select a dataset:",
        choices=valid_names
    ).ask()

    versions = available_names[name]
    version_keys = sorted(versions.keys())
    console.print(f"Available versions for '{name}': {', '.join(version_keys)}", style="cyan")

    v1 = questionary.text(
        "Enter the older version:",
        validate=lambda text: True if text.strip() in version_keys
                            else f"'{text.strip()}' not found. Available: {', '.join(version_keys)}"
    ).ask()
    v1 = v1.strip()

    remaining = [v for v in version_keys if v != v1]
    v2 = questionary.text(
        "Enter the newer version:",
        validate=lambda text: True if text.strip() in remaining
                            else f"'{text.strip()}' not found or already used. Available: {', '.join(remaining)}"
    ).ask()
    v2 = v2.strip()

    additions_file = f"additions_{name}_{v2}_minus_{v1}.ttl"
    deletions_file = f"deletions_{name}_{v1}_minus_{v2}.ttl"

    console.print(f"Start the batch splitting for {name}. The versions used are {v1} and {v2}\n", style="green")

    added_graph_uri = get_graph_uri(name, "added", v1, v2)
    deleted_graph_uri = get_graph_uri(name, "removed", v1, v2)

    console.print(f"Loading delta files into virtuoso is starting...\n", style="blue")
    load_selected_delta_files(additions_file, deletions_file)

    total_additions = get_triple_count(added_graph_uri)
    total_deletions = get_triple_count(deleted_graph_uri)

    console.print(
        f"Available: {total_additions:,} additions, {total_deletions:,} deletions.",
        style="cyan"
    )

    batching_mode = questionary.select(
        "How do you want to batch these updates?",
        choices=["By raw triples", "By entity class"]
    ).ask()

    if batching_mode == "By entity class":
        graph_uri_v1 = get_graph_snapshot_uri(name, v1)
        graph_uri_v2 = get_graph_snapshot_uri(name, v2)
        ttl_files = LOCAL_DATA_DIR.glob("*.ttl")
        v1_found = False
        v2_found = False
        file_name_v1 = ""
        file_name_v2 = ""
        for file in ttl_files:
            if not (file.name.startswith("additions_") or file.name.startswith("deletions_")) and name in file.name and (v1 in file.name):
                v1_found = True
                file_name_v1 = file.name

            elif not (file.name.startswith("additions_") or file.name.startswith("deletions_")) and name in file.name and (v2 in file.name):
                v2_found = True 
                file_name_v2 = file.name
            if v1_found and v2_found:
                break
        #if not in test data and not in V
        if (v1_found and v2_found):
            print("Need to find the available classes. Loading of snapshots started: ")
            load_selected_ttl_files(file_name_v1, file_name_v2)

        #if not in test data and not in V
        elif not (v1_found and v2_found) :
            print("Please check that both versions of the snapshots are in test data.")
            exit(1)

        return get_class_based_user_input(graph_uri_v1, graph_uri_v2, added_graph_uri, deleted_graph_uri)

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
        "mode": "triples",
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

    params = get_user_input()
    console.print(params, style="blue")

    if params["mode"] == "class":
        if params["num_batches"] == 0:
            exit(0)

        start = time.perf_counter()
        generate_class_based_batches(
            graph_uri_added=params["added_graph_uri"],
            graph_uri_deleted=params["deleted_graph_uri"],
            graph_uri_v2=params["graph_uri_v2"],
            graph_uri_v1=params["graph_uri_v1"],
            class_uri=params["class_uri"],
            num_batches=params["num_batches"],
            entities_added_per_batch=params["entities_added_per_batch"],
            entities_removed_per_batch=params["entities_removed_per_batch"],
        )
        seconds = time.perf_counter() - start
        console.print(f"\nTotal runtime of tool: {seconds:.2f} seconds ({seconds/60:.2f} min)", style="yellow")
        return

    if ((params["additions_per_batch"] == 0 and params["deletions_per_batch"] == 0) or params["num_batches"] == 0):
        exit(0)

    start = time.perf_counter()
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



    
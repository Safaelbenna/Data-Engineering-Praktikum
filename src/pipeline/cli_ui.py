import pyfiglet
from rich.console import Console
import questionary
from config import LOCAL_DATA_DIR, get_graph_uri
from delta_computation import additions_computation, deletions_computation
from load_to_virtuoso import load_selected_ttl_files
from test_querying import graph_exists, preview_graph
import time 

console = Console()


def show_banner():
    banner = pyfiglet.figlet_format("DeltaGraph")
    console.print(banner, style="yellow")
    console.print("A CLI for batching knowledge graph deltas\n", style="green")


def get_available_names() -> dict:
    names = {}

    for filepath in LOCAL_DATA_DIR.glob("*.ttl"):
        filename = filepath.stem

        if filename.startswith("additions_") or filename.startswith("deletions_"):
            continue

        parts = filename.split("_")
        dataset_name = parts[0]
        version = parts[1]

        if dataset_name not in names:
            names[dataset_name] = {}
        names[dataset_name][version] = filepath.name

    return names

def get_user_input() -> dict:
    show_banner()
    available_names = get_available_names()

    valid_names = [name for name, versions in available_names.items() if len(versions) == 2]

    if not valid_names:
        console.print("No datasets with exactly 2 versions found in test data.", style="red")
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


    graph_uri_older = get_graph_uri(name, v1)
    graph_uri_newer = get_graph_uri(name, v2)



    console.print(
        f"Using '{v1}' as the older snapshot and '{v2}' as the newer one.",
        style="cyan"
    )


    return {
    "name": name,
    "older_version": v1,
    "newer_version": v2,
    "graph_uri_older": graph_uri_older,
    "graph_uri_newer": graph_uri_newer,
    "file_older": available_names[name][v1],
    "file_newer": available_names[name][v2]
    }



def main():
    
    start = time.perf_counter()
    params = get_user_input()
    console.print(params, style="blue")
    console.print()


    console.print(f"Loading files into virtuoso is starting...\n", style="blue")
    load_selected_ttl_files(params["file_older"], params["file_newer"])

    #confirming that the graphs exist in virtuoso
    print("\nChecking if graphs exist...")
    print("older graph exists:", graph_exists(params["graph_uri_older"]))
    print("newer graph exists:", graph_exists(params["graph_uri_newer"]))

    #previewing the data to the user 
    print("\nPreviewing 10 first triples...")
    preview_graph(params["graph_uri_older"])
    preview_graph(params["graph_uri_newer"])
    print()

    #deltta computation
    if (graph_exists(params["graph_uri_older"]) and graph_exists(params["graph_uri_newer"])):
        additions_computation(params["graph_uri_older"], params["graph_uri_newer"])
        deletions_computation(params["graph_uri_older"], params["graph_uri_newer"])
        name = params["name"]
        v1 = params["older_version"]
        v2 = params["newer_version"]

        console.print(f"\nDelta files created in 'test data/':", style="green")
        console.print(f"  • additions_{name}_{v2}_minus_{v1}.ttl", style="cyan")
        console.print(f"  • deletions_{name}_{v1}_minus_{v2}.ttl", style="cyan")
    else:
        console.print("The graphs do not exist in virtuoso, hence the delta computation cannot be proceeded. Please check the data!", style= "red")
    
    seconds = time.perf_counter() - start
    console.print(f"\nTotal runtime of pipeline: {seconds:.2f} seconds ({seconds/60:.2f} min)", style="yellow")


main()  
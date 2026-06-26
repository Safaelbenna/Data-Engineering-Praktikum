import subprocess
import time
import requests

from config import (
    CONTAINER_NAME,
    DBA_USER,
    DBA_PASSWORD,
    LOCAL_DATA_DIR,
    VIRTUOSO_DATA_DIR,
    SPARQL_ENDPOINT
)
from test_querying import graph_exists




def get_graph_uri(filename: str) -> str:

    if filename.startswith("additions_"):
        operation = "added"
        rest = filename[len("additions_"):]
    elif filename.startswith("deletions_"):
        operation = "removed"
        rest = filename[len("deletions_"):]
    else:
        raise ValueError(f"Unknown file type: {filename}")

    # rest is now: small_dataset_v2_minus_v1.ttl
    rest = rest.replace(".ttl", "")
    dataset_name = rest.split("_v")[0].split("_202")[0]  # everything before the version part

    return f"http://dbpedia.org/delta/{dataset_name}/{operation}"


def load_file(filename: str, graph_uri: str) -> None:
    sql = f"""
    ld_dir('{VIRTUOSO_DATA_DIR}', '{filename}', '{graph_uri}');
    rdf_loader_run();
    """

    command = [
        "docker",
        "exec",
        "-i",
        CONTAINER_NAME,
        "isql",
        "1111",
        DBA_USER,
        DBA_PASSWORD,
    ]

    start = time.perf_counter()

    result = subprocess.run(
        command,
        input=sql,
        text=True,
        capture_output=True, #So stdout and stderr will be captured
    )

    end = time.perf_counter()
    seconds = end - start

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("Loading failed.")

    print(f"Finished loading command for {filename} into {graph_uri}")
    print(f"Time: {seconds:.2f} seconds")
    print(f"Time: {seconds/60:.2f} minutes")



def load_selected_delta_files(additions_file: str, deletions_file: str) -> None:
    selected = {additions_file, deletions_file}
    target_files = sorted(
        f for f in LOCAL_DATA_DIR.glob("*.ttl") if f.name in selected
    )

    if not target_files:
        raise FileNotFoundError(f"No additions/deletions .ttl files found in {LOCAL_DATA_DIR}")

    for file_path in target_files:
        filename = file_path.name
        graph_uri = get_graph_uri(filename)
        if graph_exists(graph_uri):
            print(f"Already loaded: {graph_uri}")
            continue
        load_file(filename, graph_uri)


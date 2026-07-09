import subprocess
import time

from config import (
    CONTAINER_NAME,
    DBA_USER,
    DBA_PASSWORD,
    LOCAL_DATA_DIR,
    VIRTUOSO_DATA_DIR,
)
from config import get_graph_uri, get_graph_snapshot_uri
from test_querying import graph_exists


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
        print(f"No additions/deletions .ttl files found in {LOCAL_DATA_DIR}")
        exit(1)

    v1 = ""
    v2 = ""
    found = False
    for file_path in target_files:
        filename = file_path.stem
        if filename.startswith("additions_") or filename.startswith("deletions_"):
            rest = filename[len("additions_"):]        
            parts = rest.split("_minus_")
            dataset_name = "_".join(parts[0].split("_")[:-1])
            if not found:
                v1 = parts[1]                              
                v2 = parts[0].split("_")[-1] 
                found = True
        tag = ""
        if filename.startswith("additions_"):
            tag = "added"
        elif filename.startswith("deletions_"):
            tag = "removed"   
        graph_uri = get_graph_uri(dataset_name, tag, v1, v2)

        if graph_exists(graph_uri):
            print(f"Already loaded: {graph_uri}")
            continue
        load_file(f"{filename}.ttl", graph_uri)

def load_selected_ttl_files(file_older: str, file_newer: str) -> None:
    
    selected = {file_older, file_newer}
    ttl_files = sorted(
        f for f in LOCAL_DATA_DIR.glob("*.ttl") if f.name in selected
    )
    
    if not ttl_files:
        raise FileNotFoundError(f"No .ttl files found in {LOCAL_DATA_DIR}")

    for file_path in ttl_files:
        filename = file_path.name
        parts = filename.split("_")
        dataset_name = parts[0]
        version = parts[1]
        if ".ttl" in version:
            version = version[:-4]

        graph_uri = get_graph_snapshot_uri(dataset_name, version)
        if graph_exists(graph_uri):
            print(f"Already loaded: {graph_uri}")
            continue
        load_file(filename, graph_uri)
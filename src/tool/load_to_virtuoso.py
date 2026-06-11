import subprocess
import time

from config import (
    CONTAINER_NAME,
    DBA_USER,
    DBA_PASSWORD,
    LOCAL_DATA_DIR,
    VIRTUOSO_DATA_DIR,
    ADDED_GRAPH_S,
    REMOVED_GRAPH_S,
    ADDED_GRAPH_B,
    REMOVED_GRAPH_B,
)
from test_querying import graph_exists


def get_graph_uri(filename: str) -> str:
    if "additions_v" in filename:
        return ADDED_GRAPH_S

    if "deletions_v" in filename:
        return REMOVED_GRAPH_S
    
    if "additions_202" in filename:
        return ADDED_GRAPH_B
    
    if "deletions_202" in filename:
        return REMOVED_GRAPH_B

    raise ValueError(f"Unknown year in filename: {filename}")


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



def load_all_ttl_files() -> None:
    addition_files = sorted(LOCAL_DATA_DIR.glob("additions_*.ttl"))
    deletion_files = sorted(LOCAL_DATA_DIR.glob("deletions_*.ttl"))
    
    target_files = addition_files + deletion_files
    
    if not target_files:
        raise FileNotFoundError(f"No additions/deletions .ttl files found in {LOCAL_DATA_DIR}")

    for file_path in target_files:
        filename = file_path.name
        graph_uri = get_graph_uri(filename)
        if graph_exists(graph_uri):
            print(f"Already loaded: {graph_uri}")
            continue
        load_file(filename, graph_uri)
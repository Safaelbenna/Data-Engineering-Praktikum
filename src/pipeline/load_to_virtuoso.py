import subprocess
import re
import time

from config import (
    CONTAINER_NAME,
    DBA_USER,
    DBA_PASSWORD,
    LOCAL_DATA_DIR,
    VIRTUOSO_DATA_DIR,
    GRAPH_v1,
    GRAPH_v2,
    GRAPH_2021,
    GRAPH_2022,
)
from test_querying import graph_exists


def get_graph_uri(filename: str) -> str:
    if "v1" in filename:
        return GRAPH_v1

    if "v2" in filename:
        return GRAPH_v2
    
    if "2021" in filename:
        return GRAPH_2021
    
    if "2022" in filename:
        return GRAPH_2022

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

    result = subprocess.run(
        command,
        input=sql,
        text=True,
        capture_output=True, #So stdout and stderr will be captured
    )

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("Loading failed.")

    print(f"Finished loading command for {filename} into {graph_uri}")




def load_all_ttl_files() -> None:
    all_files = set(LOCAL_DATA_DIR.glob("*.ttl"))
    additions = set(LOCAL_DATA_DIR.glob("additions_*.ttl"))
    deletions = set(LOCAL_DATA_DIR.glob("deletions_*.ttl"))
    ttl_files = sorted(all_files - additions - deletions)
    
    if not ttl_files:
        raise FileNotFoundError(f"No .ttl files found in {LOCAL_DATA_DIR}")

    for file_path in ttl_files:
        filename = file_path.name

        graph_uri = get_graph_uri(filename)
        if graph_exists(graph_uri):
            print(f"Already loaded: {graph_uri}")
            continue
        load_file(filename, graph_uri)

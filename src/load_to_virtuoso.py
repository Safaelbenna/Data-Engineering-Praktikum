import subprocess

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
    GRAPH_DELTA_ADDED,
    GRAPH_DELTA_REMOVED
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
    # maybe add checkpoint; to sql for larger files.

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

    #print(f"Loaded {filename} into {graph_uri}")
    print(f"Finished loading command for {filename} into {graph_uri}")

def load_trig_file(filename: str) -> None:
    # trig already has named graphs embedded, no need to specify a graph_uri
    sql = f"""
    DB.DBA.TTLP_MT(file_to_string_output('{VIRTUOSO_DATA_DIR}/{filename}'), '', 'http://dbpedia.org/delta/', 256);
    """
    command = [
        "docker", "exec", "-i", CONTAINER_NAME,
        "isql", "1111", DBA_USER, DBA_PASSWORD,
    ]
    result = subprocess.run(command, input=sql, text=True, capture_output=True)

    if result.returncode != 0:
        raise RuntimeError("Loading trig failed.")

    print(f"Finished loading {filename}")


def load_all_ttl_files() -> None:
    ttl_files = sorted(LOCAL_DATA_DIR.glob("*.ttl")) + sorted(LOCAL_DATA_DIR.glob("*.trig"))
    if not ttl_files:
        raise FileNotFoundError(f"No .ttl files found in {LOCAL_DATA_DIR}")

    for file_path in ttl_files:
        filename = file_path.name

        if "2021" in filename or "2022" in filename:
            print(f"Skipping large file: {filename}")
            continue

        if filename.endswith(".trig"):
            # if graph_exists(GRAPH_DELTA_ADDED) and graph_exists(GRAPH_DELTA_REMOVED):
            #     print(f"Already loaded: delta graphs")
            #     continue
            # load_trig_file(filename)
            print(f"Skipping trig file: {filename}")
            continue
        else:
            graph_uri = get_graph_uri(filename)
            if graph_exists(graph_uri):
                print(f"Already loaded: {graph_uri}")
                continue
            load_file(filename, graph_uri)
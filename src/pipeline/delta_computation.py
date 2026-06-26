import subprocess
import time


def additions_computation(graph_uri1: str, graph_uri2: str) -> None:
    query = f"""
    SPARQL
    SELECT ?s ?p ?o
    WHERE {{
    GRAPH <{graph_uri2}> {{
        ?s ?p ?o .
    }}

    FILTER NOT EXISTS {{
        GRAPH <{graph_uri1}> {{
        ?s ?p ?o .
        }}
    }}
    }};
    exit;
    """

    start = time.perf_counter()
    value = "v" if ("v" in graph_uri1) else "202"
    dataset_name = graph_uri1.rstrip("/").split("/")[-1]

    print("\nComputing additions...")

    with open(f"additions_{dataset_name}_{value}2_minus_{value}1.txt", "w") as output:
        subprocess.run(
            ["docker", "exec", "-i", "deltagraph_virtuoso", "isql", "1111", "dba", "mysecret"],
            input=query,
            stdout=output,
            text=True
        )

    end = time.perf_counter()

    with open(f"additions_{dataset_name}_{value}2_minus_{value}1.txt", "r", errors="replace") as file:
        for line in file:
            if "Rows. --" in line:
                parts = line.split()
                rows, msec = int(parts[0]), int(parts[3])
                print(f"{rows:,} rows in ({msec})ms {msec/1000:.1f}s ({msec/60000:.1f} min)")

    seconds = end - start

    print("Finished")
    print(f"Time: {seconds:.2f} seconds")
    print(f"Time: {seconds/60:.2f} minutes")

    print("converting response in a TTL file...\n")
    start = time.perf_counter()
    convert_isql_output_to_nt(
        f"additions_{dataset_name}_{value}2_minus_{value}1.txt",
        f"test data/additions_{dataset_name}_{value}2_minus_{value}1.ttl"
    )
    end = time.perf_counter()
    seconds = end - start

    print("Finished")
    print(f"Time: {seconds:.2f} seconds")
    print(f"Time: {seconds/60:.2f} minutes")


def deletions_computation(graph_uri1: str, graph_uri2: str) -> None:
    query = f"""
    SPARQL
    SELECT ?s ?p ?o
    WHERE {{
    GRAPH <{graph_uri1}> {{
        ?s ?p ?o .
    }}

    FILTER NOT EXISTS {{
        GRAPH <{graph_uri2}> {{
        ?s ?p ?o .
        }}
    }}
    }};
    exit;
    """

    start = time.perf_counter()
    value = "v" if ("v" in graph_uri1) else "202"
    dataset_name = graph_uri1.rstrip("/").split("/")[-1]

    print("\nComputing deletions...")

    with open(f"deletions_{dataset_name}_{value}1_minus_{value}2.txt", "w") as output:
        subprocess.run(
            ["docker", "exec", "-i", "deltagraph_virtuoso", "isql", "1111", "dba", "mysecret"],
            input=query,
            stdout=output,
            text=True
        )

    end = time.perf_counter()


    with open(f"deletions_{dataset_name}_{value}1_minus_{value}2.txt", "r", errors="replace") as file:
        for line in file:
            if "Rows. --" in line:
                parts = line.split()
                rows, msec = int(parts[0]), int(parts[3])
                print(f"{rows:,} rows in ({msec})ms {msec/1000:.1f}s ({msec/60000:.1f} min)")

    seconds = end - start

    print("Finished")
    print(f"Time: {seconds:.2f} seconds")
    print(f"Time: {seconds/60:.2f} minutes")

    print("converting response in a TTL file...\n")
    start = time.perf_counter()
    convert_isql_output_to_nt(
        f"deletions_{dataset_name}_{value}1_minus_{value}2.txt",
        f"test data/deletions_{dataset_name}_{value}1_minus_{value}2.ttl"
    )
    end = time.perf_counter()

    seconds = end - start

    print("Finished")
    print(f"Time: {seconds:.2f} seconds")
    print(f"Time: {seconds/60:.2f} minutes")

    


def to_nt_object(value: str) -> str:
    if value.startswith("http://") or value.startswith("https://"):
        return f"<{value}>"
    if value.startswith("_:"):
        return value

    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def convert_isql_output_to_nt(input_path: str, output_path: str) -> None:
    converted = 0
    skipped = 0
    start = time.perf_counter()
    with open(input_path, "r", encoding="utf-8", errors="replace") as inp, \
         open(output_path, "w", encoding="utf-8") as out:

        for line in inp:
            line = line.strip()

            if not line:
                continue

            parts = line.split()

            # keep only real triple rows
            if len(parts) != 3:
                skipped += 1
                continue

            s, p, o = parts

            if not (s.startswith("http://") or s.startswith("https://") or s.startswith("_:")):
                skipped += 1
                continue

            if not (p.startswith("http://") or p.startswith("https://")):
                skipped += 1
                continue

            out.write(f"<{s}> <{p}> {to_nt_object(o)} .\n")
            converted += 1
    end = time.perf_counter()


    print(f"Converted triples: {converted}")
    print(f"Skipped lines: {skipped}")
    seconds = end - start

    print("Finished")
    print(f"Time: {seconds:.2f} seconds")
    print(f"Time: {seconds/60:.2f} minutes")




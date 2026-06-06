import csv
import hashlib
import io
from test_querying import run_query

def hash_triple(s, p, o) -> str:
    triple = f"{s}{p}{o}"
    return hashlib.sha256(triple.encode()).hexdigest()

def get_hashes(graph, batch_size):
    offset = 0
    hashes = set()
    
    while True:
        query = f"""
        SELECT ?s ?p ?o
        WHERE {{
            GRAPH <{graph}> {{
                ?s ?p ?o
            }}
        }}
        LIMIT {batch_size}
        OFFSET {offset}
        """
        
        results = run_query(query)
        reader = csv.reader(io.StringIO(results.decode("utf-8")))
        print("reader: ", reader)        
        batch = list(reader)
        
        if not batch:
            break
        
        for row in batch:
            s, p, o = row
            fingerprint = hash_triple(s, p, o)
            hashes.add(fingerprint)
        
        offset += batch_size
        print(f"Processed {offset} triples...")
    
    return hashes
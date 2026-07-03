# DeltaGraph: Benchmark for Updates over Knowledge​ Graphs


A benchmark pipeline for computing deltas between DBpedia knowledge graph snapshots and splitting them into update batches.

## Description

DeltaGraph addresses a common problem with large knowledge graphs like DBpedia: since the underlying data changes frequently, keeping it up to date usually means reprocessing or redistributing entire snapshots, even when only a small fraction of the triples actually changed. This project builds a pipeline that takes two snapshot versions of DBpedia, computes the delta between them (triples added and removed), and splits it into configurable update batches. Small datasets are handled in-memory with rdflib via graph subtraction, while large snapshots are loaded into a Virtuoso instance and queried via SPARQL. Alongside the pipeline, we track the runtime of each stage (delta computation and batch generation) to spot inefficiencies and guide further optimization. This was built as part of the TUM BPC Data Engineering course.

## Getting Started

### Dependencies

* Python 3.x
* Docker (for running Virtuoso)
* `rdflib` (easier to work with for small datasets)
* A SPARQL client library (e.g. `SPARQLWrapper`)
* Virtuoso image: `openlink/virtuoso-opensource-7`

### Installing

* Clone this repository
* Download the Virtuoso image:
```
docker pull openlink/virtuoso-opensource-7
```
* Install Python dependencies:
```
pip install -r requirements.txt
```

### Executing program

* Start Virtuoso with Docker Compose:
```
docker compose up -d
```
The SPARQL endpoint should then be accessible at `http://localhost:8890/sparql`.
* Run the main pipeline:
```
python src/main.py
```

## Help

If Virtuoso isn't responding, check that the container is running:
```
docker ps
```
If the SPARQL endpoint is unreachable, confirm it's available at `http://localhost:8890/sparql`.

### Clearing a loaded graph (for testing)

To delete a loaded graph and re-test from a clean state, open an isql session in the running container:
```
docker exec -it deltagraph_virtuoso isql 1111 dba mysecret
```
Then clear the graph(s) you want to remove (swap in the relevant graph URI):
```
SPARQL CLEAR GRAPH <http://dbpedia.org/snapshot/v1/mappingbased-objects>;
SPARQL CLEAR GRAPH <http://dbpedia.org/snapshot/v2/mappingbased-objects>;


```
It's also worth clearing the corresponding entry from the load list so Virtuoso doesn't think the graph is still loaded:
```
DELETE FROM DB.DBA.load_list WHERE ll_graph IN (
    'http://dbpedia.org/snapshot/v1/mappingbased-objects',
    'http://dbpedia.org/snapshot/v2/mappingbased-objects'
);
```



A checkpoint may be needed after this — still confirming. (verify whether to keep this or not)

### Checking how many triples are loaded

```
SPARQL SELECT COUNT(*) WHERE { GRAPH <http://dbpedia.org/snapshot/v1/mappingbased-objects> { ?s ?p ?o } };
```

### Finding all stored graphs in Virtuoso

```
SELECT DISTINCT ?g
WHERE {
  GRAPH ?g {
    ?s ?p ?o
  }
}
ORDER BY ?g
```

### Running SPARQL queries via the endpoint (no isql needed)
 
Plain `SELECT` queries (like the row count and graph-listing ones above) don't require an isql session — they can be run directly through Virtuoso's SPARQL endpoint at `http://localhost:8890/sparql`. Open that URL in a browser, paste the query into the query box, and run it.
 
Example : counting triples in a graph, run directly at the endpoint:
```
SELECT COUNT(*) WHERE { GRAPH <http://dbpedia.org/snapshot/v1/mappingbased-objects> { ?s ?p ?o } }
```
 
Administrative commands like `CLEAR GRAPH` or deleting rows from `DB.DBA.load_list` still need the isql session shown above, since they touch Virtuoso internals beyond standard SPARQL.

## Authors

Ons Ben Makhlouf, 
Safa El Benna

## Acknowledgments

* [Virtuoso OpenLink Docker Image Setup](https://www.youtube.com/watch?v=ST8k-NzlY6A)
* [OpenLink Virtuoso GitHub](https://github.com/openlink/virtuoso-opensource)
* [CLI UI GitHub Reference](https://github.com/zurkon/lowkey?tab=readme-ov-file)



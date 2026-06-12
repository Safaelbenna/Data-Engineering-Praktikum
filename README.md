# Data-Engineering-Praktikum

docker pull openlink/virtuoso-opensource-7 #Downloading the Image

docker compose up -d   #to run docker then http://localhost:8890/sparql should be accessible

then Install dependencies with: pip install -r requirements.txt

then to run the main file: python src/main.py

to delete the loaded graph for testing (link has to be changed to wanted graph link):

___________________________

docker exec -it deltagraph_virtuoso isql 1111 dba mysecret

then (graph URI changes accordingly):

SPARQL CLEAR GRAPH <http://dbpedia.org/delta/added_small>;

SPARQL CLEAR GRAPH <http://dbpedia.org/delta/removed_small>;

SPARQL CLEAR GRAPH <http://dbpedia.org/delta/added_big>;

SPARQL CLEAR GRAPH <http://dbpedia.org/delta/removed_big>;

DELETE FROM DB.DBA.load_list
WHERE ll_graph IN (
'http://dbpedia.org/delta/added_big',

'http://dbpedia.org/delta/removed_big'
);


#find all the stored graphs in virtuoso

SELECT DISTINCT ?g
WHERE {
  GRAPH ?g {
    ?s ?p ?o
  }
}
ORDER BY ?g


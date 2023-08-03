MATCH
  (a:Person),
  (b:Movie)
WHERE a.name = 'A' AND b.name = 'B'
CREATE (a)-[r:ACTED_IN]->(b)
CREATE (b)<-[r:ACTED_IN]-(a)
CREATE (a:Person)-[s:PRODUCED]->(b)
CREATE (b)<-[s]-(a)
CREATE (a)-[:ACTED_IN]->(b)
// CREATE (a)-[:FILMED]->(b)
CREATE (b)<-[s]-(a)
// CREATE (a)-[s]->(c)
// CREATE (a)-[t]->(b)
RETURN type(r)

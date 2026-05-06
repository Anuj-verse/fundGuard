import os
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any

from app.graph import Neo4jGraph
from app.consumer import GraphKafkaConsumer
from app.gds import start_scheduler

app = FastAPI(title="FundGuard Graph Intelligence Service")

# Global instances
neo4j_graph = None
kafka_consumer = None
gds_scheduler = None

# In-memory cache for the latest detected patterns
active_patterns = []

@app.on_event("startup")
async def startup_event():
    global neo4j_graph, kafka_consumer, gds_scheduler, active_patterns
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASS", "fraud123456")
    
    # Init Neo4j
    neo4j_graph = Neo4jGraph(neo4j_uri, neo4j_user, neo4j_pass)
    try:
        neo4j_graph.create_schema()
    except Exception as e:
        print(f"Warning: Could not create schema. Is Neo4j running? Error: {e}")
        
    # Start Kafka Consumer
    kafka_brokers = os.getenv("KAFKA_BROKERS", "localhost:9092")
    # We will listen to edge-decisions or transactions-live.
    kafka_topic = os.getenv("KAFKA_TOPIC", "edge-decisions")
    
    kafka_consumer = GraphKafkaConsumer(
        bootstrap_servers=kafka_brokers,
        topic=kafka_topic,
        neo4j_graph=neo4j_graph,
        pattern_cache=active_patterns
    )
    kafka_consumer.start()
    
    # Start GDS scheduler (PageRank, Louvain)
    gds_scheduler = start_scheduler(neo4j_uri, neo4j_user, neo4j_pass)

@app.on_event("shutdown")
async def shutdown_event():
    if kafka_consumer:
        kafka_consumer.stop()
    if neo4j_graph:
        neo4j_graph.close()
    if gds_scheduler:
        gds_scheduler.shutdown()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/graph/{account_id}")
def get_ego_network(account_id: str, depth: int = 3):
    if not neo4j_graph:
        raise HTTPException(status_code=503, detail="Graph DB not initialized")
    try:
        network = neo4j_graph.get_ego_network(account_id, depth)
        return network
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patterns/active")
def get_active_patterns() -> List[Dict[str, Any]]:
    # Returns the most recently detected patterns
    return active_patterns[::-1][:50] # Return the 50 most recent

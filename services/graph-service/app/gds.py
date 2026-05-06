import logging
from apscheduler.schedulers.background import BackgroundScheduler
import app.graph as graph_module

logger = logging.getLogger(__name__)

def run_gds_algorithms(neo4j_uri, neo4j_user, neo4j_pass):
    logger.info("Running scheduled GDS algorithms (PageRank & Louvain)...")
    
    # We create a new driver instance for the scheduled job
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
    
    with driver.session() as session:
        # Clean up any existing projection
        try:
            session.run("CALL gds.graph.drop('fraud-graph', false)")
        except Exception:
            pass
            
        # 1. Project Graph
        session.run("""
            CALL gds.graph.project.cypher(
                'fraud-graph',
                'MATCH (a:Account) RETURN id(a) AS id',
                'MATCH (a:Account)-[r:TRANSFERRED]->(b:Account)
                 RETURN id(a) AS source, id(b) AS target, r.amount AS weight',
                { validateRelationships: false }
            )
        """)
        
        # 2. PageRank
        session.run("""
            CALL gds.pageRank.write('fraud-graph', {
                maxIterations: 20,
                dampingFactor: 0.85,
                relationshipWeightProperty: 'weight',
                writeProperty: 'pagerank'
            })
        """)
        
        # 3. Louvain Community Detection
        session.run("""
            CALL gds.louvain.write('fraud-graph', {
                writeProperty: 'community_id'
            })
        """)
        
        # 4. Clean up projection
        try:
            session.run("CALL gds.graph.drop('fraud-graph', false)")
        except Exception:
            pass
            
    driver.close()
    logger.info("Scheduled GDS algorithms completed.")

def start_scheduler(neo4j_uri, neo4j_user, neo4j_pass):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_gds_algorithms, 
        'interval', 
        minutes=5, 
        args=[neo4j_uri, neo4j_user, neo4j_pass],
        id='gds_job',
        replace_existing=True
    )
    scheduler.start()
    return scheduler

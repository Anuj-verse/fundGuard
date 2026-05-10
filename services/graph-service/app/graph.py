import logging
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

LOAD_QUERY = """
MERGE (sender:Account {id: $sender_account})
  ON CREATE SET
    sender.location   = $sender_location,
    sender.created_at = $timestamp,
    sender.fraud_count = 0,
    sender.txn_count   = 0

MERGE (receiver:Account {id: $receiver_account})
  ON CREATE SET
    receiver.location   = $receiver_location,
    receiver.created_at = $timestamp,
    receiver.fraud_count = 0,
    receiver.txn_count   = 0

MERGE (device:Device {id: $device_id})

CREATE (sender)-[t:TRANSFERRED {
    txn_id:     $transaction_id,
    amount:     toFloat($amount),
    timestamp:  $timestamp,
    channel:    $channel,
    is_fraud:   toInteger($is_fraud),
    risk_score: toFloat($risk_score),
    location:   $sender_location
}]->(receiver)

MERGE (sender)-[:USED_DEVICE]->(device)

WITH sender, receiver, t
SET sender.txn_count   = sender.txn_count + 1,
    receiver.txn_count = receiver.txn_count + 1,
    sender.fraud_count = sender.fraud_count + t.is_fraud
"""

LAYERING_QUERY = """
MATCH path = (a:Account)-[r1:TRANSFERRED]->(b:Account)
                        -[r2:TRANSFERRED]->(c:Account)
                        -[r3:TRANSFERRED]->(d:Account)
WHERE a.id = $sender_account AND a <> d
    AND r1.timestamp < r2.timestamp
    AND r2.timestamp < r3.timestamp
    AND duration.between(
        datetime(r1.timestamp),
        datetime(r3.timestamp)
        ).minutes <= 60
WITH a, d, r1, r3
RETURN a.id AS origin,
        d.id AS destination,
        r1.amount AS start_amount,
        r3.amount AS end_amount,
        round(toFloat(r3.amount)/toFloat(r1.amount)*100,1) AS amount_retained_pct,
        r1.timestamp AS start_time,
        r3.timestamp AS end_time
ORDER BY start_amount DESC
LIMIT 1
"""

CIRCULAR_QUERY = """
MATCH (a:Account)-[r1:TRANSFERRED]->(b:Account)
                 -[r2:TRANSFERRED]->(c:Account)
                 -[r3:TRANSFERRED]->(a)
WHERE a.id = $sender_account AND a <> b AND b <> c
    AND r1.timestamp < r2.timestamp
    AND r2.timestamp < r3.timestamp
RETURN a.id AS account_a,
        b.id AS account_b,
        c.id AS account_c,
        r1.amount AS amt_ab,
        r2.amount AS amt_bc,
        r3.amount AS amt_ca,
        r1.timestamp AS started_at
ORDER BY r1.amount DESC
LIMIT 1
"""

MULE_QUERY = """
MATCH (a:Account)-[r:TRANSFERRED]->()
WHERE a.id = $sender_account
WITH a,
     count(r)    AS total_out,
     min(r.timestamp) AS first_seen,
     max(r.timestamp) AS last_seen
WHERE total_out > 5
  AND duration.between(
        datetime(first_seen),
        datetime(last_seen)
      ).days <= 1
RETURN a.id AS account, total_out, first_seen, last_seen
LIMIT 1
"""

HUB_AND_SPOKE_QUERY = """
MATCH (a:Account)-[r:TRANSFERRED]->(b:Account)
WHERE a.id = $sender_account
  AND duration.between(datetime(r.timestamp), datetime($timestamp)).minutes <= 60
WITH a, count(DISTINCT b) as unique_receivers
WHERE unique_receivers > 10
RETURN a.id AS account, unique_receivers
LIMIT 1
"""

class Neo4jGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_schema(self):
        with self.driver.session() as session:
            cmds = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Device)  REQUIRE d.id IS UNIQUE",
                "CREATE INDEX IF NOT EXISTS FOR ()-[r:TRANSFERRED]-() ON (r.timestamp)",
                "CREATE INDEX IF NOT EXISTS FOR ()-[r:TRANSFERRED]-() ON (r.is_fraud)",
                "CREATE INDEX IF NOT EXISTS FOR ()-[r:TRANSFERRED]-() ON (r.amount)",
            ]
            for cmd in cmds:
                session.run(cmd)

    def ingest_transaction(self, txn: dict):
        with self.driver.session() as session:
            session.run(
                LOAD_QUERY,
                sender_account=txn.get("sender_account_id"),
                receiver_account=txn.get("receiver_account_id"),
                sender_location=txn.get("sender_geo_city", "UNKNOWN"),
                receiver_location=txn.get("receiver_geo_city", "UNKNOWN"),
                device_id=txn.get("device_id", "DEVICE_UNKNOWN"),
                transaction_id=txn.get("transaction_id"),
                amount=txn.get("amount"),
                timestamp=txn.get("timestamp"),
                channel=txn.get("channel", "UNKNOWN"),
                is_fraud=txn.get("is_fraud", 0),
                risk_score=txn.get("anomaly_score", 0.0) # From edge-service
            )

    def check_patterns(self, txn: dict):
        patterns = []
        with self.driver.session() as session:
            sender = txn.get("sender_account_id")
            timestamp = txn.get("timestamp")
            
            # 1. Layering
            res = session.run(LAYERING_QUERY, sender_account=sender).data()
            if res:
                patterns.append({"type": "layering", "details": res[0]})
                
            # 2. Circular
            res = session.run(CIRCULAR_QUERY, sender_account=sender).data()
            if res:
                patterns.append({"type": "circular", "details": res[0]})
                
            # 3. Mule Activation
            res = session.run(MULE_QUERY, sender_account=sender).data()
            if res:
                patterns.append({"type": "mule_activation", "details": res[0]})
                
            # 4. Hub-and-Spoke
            res = session.run(HUB_AND_SPOKE_QUERY, sender_account=sender, timestamp=timestamp).data()
            if res:
                patterns.append({"type": "hub_and_spoke", "details": res[0]})
                
        return patterns

    def get_ego_network(self, account_id: str, depth: int = 3):
        # We limit the return size for safety
        query = f"""
        MATCH path = (a:Account)-[r:TRANSFERRED*1..{depth}]-(b:Account)
        WHERE a.id = $account_id
        RETURN path
        LIMIT 100
        """
        with self.driver.session() as session:
            res = session.run(query, account_id=account_id).data()
            
        nodes = {}
        edges = []
        for row in res:
            path = row["path"]
            for node in path.nodes:
                nid = node.element_id
                nodes[nid] = {"node_id": nid, "id": node.get("id"), "labels": list(node.labels)}
            for rel in path.relationships:
                edges.append({
                    "source": rel.start_node.element_id,
                    "target": rel.end_node.element_id,
                    "type": rel.type,
                    "amount": rel.get("amount"),
                    "timestamp": rel.get("timestamp")
                })
        return {"nodes": list(nodes.values()), "edges": edges}

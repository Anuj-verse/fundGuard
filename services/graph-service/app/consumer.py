import json
import logging
import threading
from confluent_kafka import Consumer, KafkaError

logger = logging.getLogger(__name__)

class GraphKafkaConsumer:
    def __init__(self, bootstrap_servers, topic, neo4j_graph, pattern_cache):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.neo4j_graph = neo4j_graph
        self.pattern_cache = pattern_cache
        self.consumer = None
        self.producer = None
        self.running = False
        self.thread = None

    def _get_producer(self):
        if not self.producer:
            from confluent_kafka import Producer
            self.producer = Producer({'bootstrap.servers': self.bootstrap_servers})
        return self.producer

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._consume_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        if self.consumer:
            self.consumer.close()

    def _consume_loop(self):
        conf = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': 'graph-service-group',
            'auto.offset.reset': 'latest'
        }
        try:
            self.consumer = Consumer(conf)
            self.consumer.subscribe([self.topic])
            logger.info(f"Subscribed to topic {self.topic}")
        except Exception as e:
            logger.error(f"Failed to initialize consumer: {e}")
            return

        while self.running:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Consumer error: {msg.error()}")
                    continue

            try:
                print(f"Processing raw message: {msg.value()}")
                msg_val = json.loads(msg.value().decode('utf-8'))
                txn = msg_val.get("transaction", msg_val)
                
                # 1. Ingest into Neo4j
                txn["anomaly_score"] = msg_val.get("edge_score", 0.0)
                print(f"Ingesting txn: {txn['transaction_id']}")
                self.neo4j_graph.ingest_transaction(txn)
                print(f"Ingested txn: {txn['transaction_id']}")
                
                # 2. Check for patterns immediately
                new_patterns = self.neo4j_graph.check_patterns(txn)
                pattern_types = []
                for p in new_patterns:
                    self.pattern_cache.append({
                        "transaction_id": txn.get("transaction_id"),
                        "pattern": p
                    })
                    pattern_types.append(p.get("type"))
                print(f"Checked patterns for txn {txn['transaction_id']}: {pattern_types}")
                
                if len(self.pattern_cache) > 1000:
                    self.pattern_cache.pop(0)

                # 3. Publish to KAFKA graph-events so risk-engine can consume it
                producer = self._get_producer()
                if producer:
                    graph_event = {
                        "transaction_id": txn.get("transaction_id"),
                        "sender_account_id": txn.get("sender_account_id"),
                        "receiver_account_id": txn.get("receiver_account_id"),
                        "graph_risk_score": 0.8 if len(pattern_types) > 0 else 0.0,
                        "graph_flags": pattern_types,
                        "graph_subnetwork": {},
                        "transaction": txn,
                        "edge_score": msg_val.get("edge_score", 0.0)
                    }
                    print(f"Publishing to graph-events: {txn['transaction_id']}")
                    producer.produce("graph-events", value=json.dumps(graph_event).encode('utf-8'))
                    producer.flush(timeout=0.1)

            except Exception as e:
                print(f"Error processing message inside block: {e}")

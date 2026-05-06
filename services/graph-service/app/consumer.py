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
        self.running = False
        self.thread = None

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
                txn = json.loads(msg.value().decode('utf-8'))
                
                # We expect txn to contain fields like sender_account_id, receiver_account_id, etc.
                # 1. Ingest into Neo4j
                self.neo4j_graph.ingest_transaction(txn)
                
                # 2. Check for patterns immediately
                new_patterns = self.neo4j_graph.check_patterns(txn)
                for p in new_patterns:
                    # Append to the global pattern cache
                    self.pattern_cache.append({
                        "transaction_id": txn.get("transaction_id"),
                        "pattern": p
                    })
                    
                # Keep cache bounded (e.g. max 1000 items)
                if len(self.pattern_cache) > 1000:
                    self.pattern_cache.pop(0)

            except Exception as e:
                logger.error(f"Error processing message: {e}")

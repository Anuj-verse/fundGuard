import json
import logging
from confluent_kafka import Producer

logger = logging.getLogger(__name__)

class KafkaPublisher:
    def __init__(self, bootstrap_servers: str = "localhost:9092", topic: str = "transactions-live"):
        self.topic = topic
        try:
            self.producer = Producer({"bootstrap.servers": bootstrap_servers})
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None

    def publish(self, payload: dict):
        if not self.producer:
            print("Kafka producer not initialized. Skipping publish.")
            return
            
        try:
            # Fire and forget (async delivery)
            self.producer.produce(
                self.topic, 
                value=json.dumps(payload).encode('utf-8')
            )
            self.producer.flush(timeout=0.1)
        except Exception as e:
            print(f"Error publishing to Kafka: {e}")

    def shutdown(self):
        if self.producer:
            self.producer.flush(timeout=5.0)

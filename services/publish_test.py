from confluent_kafka import Producer
import sys
p=Producer({'bootstrap.servers': 'localhost:9092'})
p.produce('transactions-live', b'bar')
p.flush()

#!/usr/bin/env python3
"""
Script to stream a generated dataset to Kafka.

Requirements: 8.1
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

# Add src to python path if running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from synthetic_generator.kafka.producer import TransactionProducer
from synthetic_generator.models.transaction import Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stream_to_kafka")


def parse_row(row: dict[str, Any]) -> Transaction:
    """Parse a CSV/dict row back to a Transaction."""
    # This is a simplified parser for demonstration
    from datetime import datetime
    from synthetic_generator.models.enums import AccountType, Bank, Channel, FraudType
    from synthetic_generator.models.transaction import GeoLocation
    
    return Transaction(
        transaction_id=row["transaction_id"],
        timestamp=datetime.fromisoformat(row["timestamp"]) if isinstance(row["timestamp"], str) else row["timestamp"],
        sender_account=row["sender_account"],
        receiver_account=row["receiver_account"],
        amount=float(row["amount"]),
        channel=Channel(row["channel"]) if row["channel"] else None,
        sender_bank=Bank(row["sender_bank"]) if row["sender_bank"] else None,
        receiver_bank=Bank(row["receiver_bank"]) if row["receiver_bank"] else None,
        sender_geo=GeoLocation(
            city=row["sender_geo_city"],
            state=row["sender_geo_state"],
            latitude=float(row["sender_geo_latitude"]),
            longitude=float(row["sender_geo_longitude"]),
        ),
        receiver_geo=GeoLocation(
            city=row["receiver_geo_city"],
            state=row["receiver_geo_state"],
            latitude=float(row["receiver_geo_latitude"]),
            longitude=float(row["receiver_geo_longitude"]),
        ),
        sender_account_type=AccountType(row["sender_account_type"]) if row["sender_account_type"] else None,
        receiver_account_type=AccountType(row["receiver_account_type"]) if row["receiver_account_type"] else None,
        is_fraud=str(row["is_fraud"]).lower() == "true",
        fraud_type=FraudType(row["fraud_type"]) if row["fraud_type"] else None,
        fraud_ring_id=row["fraud_ring_id"] or None,
        description=row["description"] or None,
    )


async def async_main():
    parser = argparse.ArgumentParser(description="Stream transactions to Kafka")
    parser.add_argument("input_file", type=str, help="Path to input CSV or Parquet file")
    parser.add_argument("--brokers", type=str, default="localhost:9092", help="Kafka brokers")
    parser.add_argument("--topic", type=str, default="transactions", help="Kafka topic")
    parser.add_argument("--tps", type=int, default=1000, help="Transactions per second")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        return 1

    transactions = []
    logger.info("Loading transactions from %s...", input_path)
    
    if input_path.suffix == ".csv":
        import csv
        with open(input_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                transactions.append(parse_row(row))
    elif input_path.suffix == ".parquet":
        import pyarrow.parquet as pq
        table = pq.read_table(input_path)
        df = table.to_pandas()
        for _, row in df.iterrows():
            transactions.append(parse_row(row.to_dict()))
    else:
        logger.error("Unsupported file format: %s", input_path.suffix)
        return 1

    logger.info("Loaded %d transactions. Starting stream to %s...", len(transactions), args.brokers)
    
    producer = TransactionProducer(bootstrap_servers=args.brokers, topic=args.topic)
    await producer.start_stream(transactions, rate_per_sec=args.tps)
    await producer.close()
    
    logger.info("Streaming complete!")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(async_main()))

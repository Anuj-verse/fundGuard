#!/usr/bin/env python3
"""
Script to visualize fraud rings from a generated dataset.

Requirements: 10.2
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to python path if running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from synthetic_generator.stats.visualizer import generate_fraud_ring_viz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("visualizer")


def main():
    parser = argparse.ArgumentParser(description="Visualize fraud rings")
    parser.add_argument("input_file", type=str, help="Path to input CSV or Parquet file")
    parser.add_argument("fraud_ring_id", type=str, help="ID of the fraud ring to visualize")
    parser.add_argument("--output", type=str, default="fraud_ring_viz.png", help="Output image path")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        return 1

    transactions = []
    logger.info("Loading transactions from %s...", input_path)
    
    # Minimal parsing just for visualization
    from synthetic_generator.models.transaction import Transaction
    from synthetic_generator.models.enums import Channel, FraudType
    from datetime import datetime
    
    def parse_minimal(row):
        return Transaction(
            transaction_id=row["transaction_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]) if row["timestamp"] else None,
            sender_account=row["sender_account"],
            receiver_account=row["receiver_account"],
            amount=float(row["amount"]),
            channel=Channel(row["channel"]) if row["channel"] else None,
            sender_bank=None, receiver_bank=None, sender_account_type=None, receiver_account_type=None,
            is_fraud=str(row["is_fraud"]).lower() == "true",
            fraud_type=FraudType(row["fraud_type"]) if row["fraud_type"] else None,
            fraud_ring_id=row["fraud_ring_id"] or None,
            description=None,
        )

    if input_path.suffix == ".csv":
        import csv
        with open(input_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["fraud_ring_id"] == args.fraud_ring_id:
                    transactions.append(parse_minimal(row))
    elif input_path.suffix == ".parquet":
        import pyarrow.parquet as pq
        table = pq.read_table(input_path)
        df = table.to_pandas()
        for _, row in df[df["fraud_ring_id"] == args.fraud_ring_id].iterrows():
            transactions.append(parse_minimal(row.to_dict()))
    else:
        logger.error("Unsupported file format: %s", input_path.suffix)
        return 1

    if not transactions:
        logger.error("No transactions found for fraud ring ID: %s", args.fraud_ring_id)
        return 1

    logger.info("Found %d transactions. Generating visualization...", len(transactions))
    
    generate_fraud_ring_viz(args.fraud_ring_id, transactions, output_path=args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

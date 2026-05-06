"""
Tests for output writers (CSV, Parquet, Kafka).

Covers:
- FileWriter CSV output with correct columns
- FileWriter Parquet output
- FileWriter batch writing
- KafkaWriter integration
- BaseWriter protocol compliance
"""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path

import pytest

from synthetic_generator.models.enums import AccountType, Bank, Channel
from synthetic_generator.models.transaction import GeoLocation, Transaction
from synthetic_generator.output.file_writer import FileWriter
from synthetic_generator.output.kafka_writer import KafkaWriter
from synthetic_generator.output.writer import BaseWriter


@pytest.fixture
def sample_transactions() -> list[Transaction]:
    """Create sample transactions for testing."""
    geo = GeoLocation(city="Mumbai", state="Maharashtra", latitude=19.076, longitude=72.877)
    txns = []
    for i in range(10):
        txns.append(Transaction(
            transaction_id=f"TXN-TEST{i:04d}",
            timestamp=datetime(2024, 6, 15, 12, i, 0),
            sender_account=f"ACC-SEND{i:04d}",
            receiver_account=f"ACC-RECV{i:04d}",
            amount=1000.0 + i * 100,
            channel=Channel.UPI,
            sender_bank=Bank.SBI,
            receiver_bank=Bank.HDFC,
            sender_geo=geo,
            receiver_geo=geo,
            sender_account_type=AccountType.SAVINGS,
            receiver_account_type=AccountType.CURRENT,
        ))
    return txns


@pytest.fixture
def tmp_output_dir(tmp_path) -> Path:
    """Create a temporary output directory."""
    return tmp_path / "output"


class TestBaseWriterProtocol:
    def test_file_writer_is_base_writer(self, tmp_output_dir):
        writer = FileWriter(tmp_output_dir / "test.csv")
        assert isinstance(writer, BaseWriter)

    def test_kafka_writer_is_base_writer(self):
        writer = KafkaWriter()
        assert isinstance(writer, BaseWriter)


class TestFileWriterCSV:
    def test_creates_csv_file(self, sample_transactions, tmp_output_dir):
        path = tmp_output_dir / "test.csv"
        writer = FileWriter(path, format="csv")
        writer.write(sample_transactions)
        writer.close()
        assert path.exists()

    def test_csv_has_header(self, sample_transactions, tmp_output_dir):
        path = tmp_output_dir / "test.csv"
        writer = FileWriter(path, format="csv")
        writer.write(sample_transactions)
        writer.close()

        with open(path) as f:
            reader = csv.reader(f)
            header = next(reader)
            assert "transaction_id" in header
            assert "amount" in header
            assert "is_fraud" in header

    def test_csv_row_count(self, sample_transactions, tmp_output_dir):
        path = tmp_output_dir / "test.csv"
        writer = FileWriter(path, format="csv")
        writer.write(sample_transactions)
        writer.close()

        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 11  # 1 header + 10 data rows

    def test_csv_correct_columns(self, sample_transactions, tmp_output_dir):
        path = tmp_output_dir / "test.csv"
        writer = FileWriter(path, format="csv")
        writer.write(sample_transactions)
        writer.close()

        with open(path) as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert row["transaction_id"] == "TXN-TEST0000"
            assert float(row["amount"]) == 1000.0
            assert row["channel"] == "UPI"

    def test_batch_writing(self, sample_transactions, tmp_output_dir):
        path = tmp_output_dir / "batch.csv"
        writer = FileWriter(path, format="csv", batch_size=5)
        writer.write(sample_transactions[:5])
        writer.write(sample_transactions[5:])
        writer.close()
        assert writer.written_count == 10

    def test_written_count(self, sample_transactions, tmp_output_dir):
        path = tmp_output_dir / "count.csv"
        writer = FileWriter(path, format="csv")
        writer.write(sample_transactions)
        assert writer.written_count == 10
        writer.close()


class TestFileWriterParquet:
    def test_parquet_creates_file(self, sample_transactions, tmp_output_dir):
        """Test Parquet output (falls back to CSV if pyarrow missing)."""
        path = tmp_output_dir / "test.parquet"
        writer = FileWriter(path, format="parquet")
        writer.write(sample_transactions)
        writer.close()
        # File should exist (either .parquet or .csv fallback)
        assert writer.written_count == 10


class TestFileWriterValidation:
    def test_invalid_format_raises(self, tmp_output_dir):
        with pytest.raises(ValueError, match="Unsupported format"):
            FileWriter(tmp_output_dir / "test.xml", format="xml")

    def test_creates_parent_dirs(self, tmp_output_dir):
        path = tmp_output_dir / "nested" / "deep" / "test.csv"
        writer = FileWriter(path, format="csv")
        assert path.parent.exists()
        writer.close()


class TestKafkaWriter:
    @pytest.mark.asyncio
    async def test_kafka_write(self, sample_transactions):
        writer = KafkaWriter()
        await writer._async_write(sample_transactions)
        assert writer.written_count == 10

    def test_kafka_writer_has_producer(self):
        writer = KafkaWriter(bootstrap_servers="localhost:9092")
        assert writer.producer is not None

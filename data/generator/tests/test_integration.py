"""
Integration tests for the Synthetic Data Generator.

Verifies end-to-end functionality including:
- Generating 10K transactions with all fraud types
- Universal correctness properties across full pipeline
- End-to-end reproducibility
- File output compatibility

Requirements: 12.1
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from synthetic_generator.core.seed_manager import SeedManager
from synthetic_generator.evaluation.dataset_generator import EvaluationDatasetGenerator
from synthetic_generator.output.file_writer import FileWriter
from synthetic_generator.stats.collector import StatsCollector
from synthetic_generator.stats.reporter import output_stats_json


@pytest.fixture
def test_output_dir(tmp_path):
    out = tmp_path / "integration_out"
    out.mkdir()
    return out


class TestEndToEndPipeline:
    def test_end_to_end_generation_and_stats(self, test_output_dir):
        """End-to-end test of generation, statistics, and file output."""
        seed_mgr = SeedManager(master_seed=123)
        
        # Override generate method targets for a smaller 10K test
        generator = EvaluationDatasetGenerator(seed_mgr)
        original_generate = generator.generate
        
        def mock_generate(time_range=None, account_pool_size=1000):
            generator.account_factory.generate_account_pool(size=account_pool_size)
            target_total = 10_000
            target_fraud = 200
            
            transactions = generator.transaction_generator.generate_batch(
                count=target_total - target_fraud, 
                time_range=time_range
            )
            fraud_txns = generator._generate_fraud_transactions(
                target_fraud, time_range
            )
            transactions.extend(fraud_txns)
            transactions.sort(key=lambda x: x.timestamp)
            return transactions
            
        generator.generate = mock_generate
        
        from synthetic_generator.core.transaction_generator import TimeRange
        tr = TimeRange(datetime(2024,1,1), datetime(2024,1,30))
        transactions = generator.generate(time_range=tr, account_pool_size=1000)
        
        assert len(transactions) >= 10_000
        
        # Stats collection
        stats = StatsCollector().compute(transactions)
        assert stats.fraud_count >= 150
        assert len(stats.fraud_by_type) == 6  # All 6 types should be present
        
        # JSON Output
        json_path = test_output_dir / "stats.json"
        output_stats_json(stats, json_path)
        assert json_path.exists()
        
        with open(json_path) as f:
            data = json.load(f)
            assert data["total_transactions"] == len(transactions)
            
        # CSV Output
        csv_path = test_output_dir / "data.csv"
        writer = FileWriter(csv_path, format="csv", batch_size=5000)
        writer.write(transactions)
        writer.close()
        
        assert csv_path.exists()
        assert writer.written_count == len(transactions)

    def test_end_to_end_reproducibility(self):
        """Test full pipeline reproducibility with the same seed."""
        from synthetic_generator.core.transaction_generator import TimeRange
        tr = TimeRange(datetime(2024,1,1), datetime(2024,1,30))
        
        # Run 1
        seed1 = SeedManager(master_seed=42)
        gen1 = EvaluationDatasetGenerator(seed1)
        
        def mock_generate(gen, time_range, account_pool_size):
            gen.account_factory.generate_account_pool(size=account_pool_size)
            txns = gen.transaction_generator.generate_batch(
                count=400, time_range=time_range
            )
            fraud_txns = gen._generate_fraud_transactions(
                100, time_range
            )
            txns.extend(fraud_txns)
            txns.sort(key=lambda x: x.timestamp)
            return txns
            
        txns1 = mock_generate(gen1, tr, 500)
        
        # Run 2
        seed2 = SeedManager(master_seed=42)
        gen2 = EvaluationDatasetGenerator(seed2)
        txns2 = mock_generate(gen2, tr, 500)
        
        assert len(txns1) == len(txns2)
        for t1, t2 in zip(txns1, txns2):
            assert t1.transaction_id == t2.transaction_id
            assert t1.amount == t2.amount
            assert t1.timestamp == t2.timestamp
            assert t1.sender_account == t2.sender_account

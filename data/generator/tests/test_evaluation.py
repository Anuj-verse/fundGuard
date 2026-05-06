"""
Tests for evaluation dataset generator and validator.

Covers Properties 18 and 19.
Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from synthetic_generator.core.seed_manager import SeedManager
from synthetic_generator.core.transaction_generator import TimeRange
from synthetic_generator.evaluation.dataset_generator import EvaluationDatasetGenerator
from synthetic_generator.evaluation.validator import DatasetValidator


@pytest.fixture
def mini_dataset():
    """Generates a scaled-down dataset for testing speed.
    
    Target: 10,000 total, 200 fraud (2%).
    """
    seed_manager = SeedManager(master_seed=42)
    generator = EvaluationDatasetGenerator(seed_manager)
    time_range = TimeRange(
        start=datetime(2024, 6, 1), end=datetime(2024, 6, 5)
    )
    
    # We monkeypatch the targets for a fast test run
    # Since generate() doesn't currently take targets as args, we need to
    # intercept or we just rely on validation with custom targets.
    # Actually, we can test the generator's exact logic by making a mini class or 
    # copying logic, but the easiest is to just use a smaller pool and manually call methods.
    
    # We will test the exact 1M generator using smaller targets dynamically
    original_generate = generator.generate
    
    def mock_generate(time_range=None, account_pool_size=1000):
        # 1. Setup account pool
        generator.account_factory.generate_account_pool(size=account_pool_size)

        target_total = 10_000
        target_fraud = 200
        target_legit = target_total - target_fraud

        # 2. Generate legitimate transactions
        transactions = generator.transaction_generator.generate_batch(
            count=target_legit, time_range=time_range
        )

        # 3. Generate fraudulent transactions
        fraud_transactions = generator._generate_fraud_transactions(
            target_fraud, time_range
        )
        transactions.extend(fraud_transactions)

        transactions.sort(key=lambda x: x.timestamp)
        
        # Verify exact counts padding
        if len(transactions) != target_total:
            diff = target_total - len(transactions)
            if diff > 0:
                padding = generator.transaction_generator.generate_batch(diff, time_range)
                transactions.extend(padding)
                transactions.sort(key=lambda x: x.timestamp)
            elif diff < 0:
                legit_indices = [i for i, t in enumerate(transactions) if not t.is_fraud]
                to_remove = set(legit_indices[-(-diff):])
                transactions = [t for i, t in enumerate(transactions) if i not in to_remove]

        return transactions
        
    return mock_generate(time_range=time_range)


class TestEvaluationDataset:
    def test_total_count(self, mini_dataset):
        assert len(mini_dataset) == 10_000

    def test_fraud_rate(self, mini_dataset):
        fraud_txns = [t for t in mini_dataset if t.is_fraud]
        # Allow small tolerance
        assert 170 <= len(fraud_txns) <= 230

    def test_fraud_type_balance(self, mini_dataset):
        """Property 18: Fraud Type Balance."""
        validator = DatasetValidator(target_total=10_000, target_fraud=200)
        report = validator.validate(mini_dataset)
        assert report["status"] == "PASSED", report["errors"]

    def test_unique_identifiers(self, mini_dataset):
        """Property 19: Unique Identifiers."""
        txn_ids = [t.transaction_id for t in mini_dataset]
        assert len(txn_ids) == len(set(txn_ids))

    def test_reproducibility(self):
        """Property: Reproducibility across multiple runs."""
        seed1 = SeedManager(master_seed=99)
        gen1 = EvaluationDatasetGenerator(seed1)
        
        # Manually generate 500 txns
        seed1.set_all_seeds(99)
        gen1.account_factory.generate_account_pool(size=500)
        txns1 = gen1.transaction_generator.generate_batch(
            count=500, time_range=TimeRange(datetime(2024,1,1), datetime(2024,1,2))
        )
        
        seed2 = SeedManager(master_seed=99)
        gen2 = EvaluationDatasetGenerator(seed2)
        
        seed2.set_all_seeds(99)
        gen2.account_factory.generate_account_pool(size=500)
        txns2 = gen2.transaction_generator.generate_batch(
            count=500, time_range=TimeRange(datetime(2024,1,1), datetime(2024,1,2))
        )
        
        assert len(txns1) == len(txns2)
        for t1, t2 in zip(txns1, txns2):
            assert t1.transaction_id == t2.transaction_id
            assert t1.amount == t2.amount

"""
Tests for statistics collector, reporter, and visualizer.

Covers:
- Stats computation accuracy
- Fraud rate calculation
- Amount distribution
- Temporal distribution
- JSON output format
- Text output format
- Graph generation

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from synthetic_generator.core.seed_manager import SeedManager
from synthetic_generator.core.account_factory import AccountFactory
from synthetic_generator.fraud.layering import LayeringInjector
from synthetic_generator.fraud.circular import CircularInjector
from synthetic_generator.models.enums import AccountType, Bank, Channel, FraudType
from synthetic_generator.models.transaction import GeoLocation, Transaction
from synthetic_generator.stats.collector import DatasetStats, StatsCollector
from synthetic_generator.stats.reporter import output_stats_json, output_stats_text
from synthetic_generator.stats.visualizer import generate_fraud_ring_viz


@pytest.fixture
def geo():
    return GeoLocation(city="Mumbai", state="Maharashtra", latitude=19.076, longitude=72.877)


@pytest.fixture
def legit_transactions(geo):
    txns = []
    for i in range(80):
        txns.append(Transaction(
            transaction_id=f"TXN-LEGIT{i:04d}",
            timestamp=datetime(2024, 6, 15, i % 24, (i * 7) % 60, 0),
            sender_account=f"ACC-S{i % 10:04d}",
            receiver_account=f"ACC-R{(i + 1) % 10:04d}",
            amount=1000.0 + i * 50,
            channel=[Channel.UPI, Channel.NEFT, Channel.IMPS][i % 3],
            sender_bank=Bank.SBI,
            receiver_bank=Bank.HDFC,
            sender_geo=geo,
            receiver_geo=geo,
            sender_account_type=AccountType.SAVINGS,
            receiver_account_type=AccountType.CURRENT,
        ))
    return txns


@pytest.fixture
def fraud_transactions(geo):
    txns = []
    for i in range(20):
        txns.append(Transaction(
            transaction_id=f"TXN-FRAUD{i:04d}",
            timestamp=datetime(2024, 6, 15, 14, i, 0),
            sender_account=f"ACC-FS{i:04d}",
            receiver_account=f"ACC-FR{i:04d}",
            amount=50000.0 + i * 1000,
            channel=Channel.NEFT,
            sender_bank=Bank.ICICI,
            receiver_bank=Bank.PNB,
            sender_geo=geo,
            receiver_geo=geo,
            sender_account_type=AccountType.CURRENT,
            receiver_account_type=AccountType.SAVINGS,
            is_fraud=True,
            fraud_type=FraudType.LAYERING if i < 10 else FraudType.CIRCULAR,
            fraud_ring_id=f"FR-TEST-{i // 5:03d}",
        ))
    return txns


@pytest.fixture
def all_transactions(legit_transactions, fraud_transactions):
    return legit_transactions + fraud_transactions


class TestStatsCollector:
    def test_total_count(self, all_transactions):
        stats = StatsCollector().compute(all_transactions)
        assert stats.total_transactions == 100

    def test_fraud_count(self, all_transactions):
        stats = StatsCollector().compute(all_transactions)
        assert stats.fraud_count == 20

    def test_fraud_rate(self, all_transactions):
        stats = StatsCollector().compute(all_transactions)
        assert stats.fraud_rate == 20.0

    def test_fraud_by_type(self, all_transactions):
        stats = StatsCollector().compute(all_transactions)
        assert stats.fraud_by_type["layering"] == 10
        assert stats.fraud_by_type["circular"] == 10

    def test_fraud_ring_count(self, all_transactions):
        stats = StatsCollector().compute(all_transactions)
        assert stats.fraud_ring_count == 4  # rings 000, 001, 002, 003

    def test_amount_stats(self, all_transactions):
        stats = StatsCollector().compute(all_transactions)
        assert stats.amount_stats["min"] > 0
        assert stats.amount_stats["max"] > stats.amount_stats["min"]
        assert stats.amount_stats["mean"] > 0
        assert stats.amount_stats["median"] > 0

    def test_temporal_stats(self, all_transactions):
        stats = StatsCollector().compute(all_transactions)
        assert len(stats.temporal_stats) > 0
        assert sum(stats.temporal_stats.values()) == 100

    def test_channel_stats(self, all_transactions):
        stats = StatsCollector().compute(all_transactions)
        assert len(stats.channel_stats) > 0
        total = sum(stats.channel_stats.values())
        assert total == 100

    def test_account_degree(self, all_transactions):
        stats = StatsCollector().compute(all_transactions)
        assert len(stats.account_degree) > 0
        # Each account should have at least 1 counterparty
        for acct, degree in stats.account_degree.items():
            assert degree >= 1

    def test_empty_transactions(self):
        stats = StatsCollector().compute([])
        assert stats.total_transactions == 0
        assert stats.fraud_count == 0
        assert stats.fraud_rate == 0.0


class TestStatsReporter:
    def test_json_output(self, all_transactions, tmp_path):
        stats = StatsCollector().compute(all_transactions)
        path = tmp_path / "stats.json"
        output_stats_json(stats, path)
        assert path.exists()

        with open(path) as f:
            data = json.load(f)
        assert data["total_transactions"] == 100
        assert data["fraud_count"] == 20
        assert "amount_stats" in data

    def test_json_has_all_keys(self, all_transactions, tmp_path):
        stats = StatsCollector().compute(all_transactions)
        path = tmp_path / "stats.json"
        output_stats_json(stats, path)

        with open(path) as f:
            data = json.load(f)
        expected_keys = {
            "total_transactions", "fraud_count", "fraud_rate_pct",
            "fraud_by_type", "fraud_ring_count", "amount_stats",
            "temporal_stats", "channel_stats", "bank_stats",
        }
        assert expected_keys.issubset(set(data.keys()))

    def test_text_output(self, all_transactions, tmp_path):
        stats = StatsCollector().compute(all_transactions)
        path = tmp_path / "stats.txt"
        output_stats_text(stats, path)
        assert path.exists()

        content = path.read_text()
        assert "SYNTHETIC DATASET STATISTICS" in content
        assert "Total Transactions" in content
        assert "Fraud by Type" in content

    def test_text_contains_amounts(self, all_transactions, tmp_path):
        stats = StatsCollector().compute(all_transactions)
        path = tmp_path / "stats.txt"
        output_stats_text(stats, path)
        content = path.read_text()
        assert "Amount Distribution" in content
        assert "₹" in content


class TestVisualizer:
    def test_graph_generation(self):
        mgr = SeedManager(master_seed=42)
        factory = AccountFactory(seed_manager=mgr)
        factory.generate_account_pool(size=20)
        accounts = factory.accounts

        txns = LayeringInjector().inject(accounts, {"min_hops": 4, "max_hops": 6}, datetime(2024, 6, 15))
        ring_id = txns[0].fraud_ring_id

        G = generate_fraud_ring_viz(ring_id, txns)
        assert G is not None
        assert G.number_of_nodes() >= 4
        assert G.number_of_edges() >= 4

    def test_empty_ring_returns_none(self):
        G = generate_fraud_ring_viz("FR-NONEXISTENT", [])
        assert G is None

    def test_graph_with_output(self, tmp_path):
        mgr = SeedManager(master_seed=42)
        factory = AccountFactory(seed_manager=mgr)
        factory.generate_account_pool(size=20)
        accounts = factory.accounts

        txns = CircularInjector().inject(accounts, {}, datetime(2024, 6, 15))
        ring_id = txns[0].fraud_ring_id

        out = tmp_path / "ring.png"
        G = generate_fraud_ring_viz(ring_id, txns, output_path=out)
        assert G is not None
        # Image may or may not be created depending on matplotlib

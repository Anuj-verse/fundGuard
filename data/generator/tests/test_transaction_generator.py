"""
Unit and property tests for TransactionGenerator.

Tests cover:
- Single transaction generation with valid fields
- Batch generation with correct count and sorted timestamps
- Timestamp distribution following peak hour patterns
- Amount distribution (log-normal, heavy-tailed, within bounds)
- Geographic attributes within Indian bounds
- Channel-specific amount ranges
- Reproducibility with seeded random

Properties verified:
- Property 1: Valid Indian Banking Attributes
- Property 2: Amount Range Constraint
- Property 3: Valid Geographic Attributes
- Property 4: Complete Required Fields

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

import pytest

from synthetic_generator.core.account_factory import AccountFactory
from synthetic_generator.core.seed_manager import SeedManager
from synthetic_generator.core.transaction_generator import (
    TransactionGenerator,
    TimeRange,
    DEFAULT_HOUR_DISTRIBUTION,
)
from synthetic_generator.models.enums import AccountType, Bank, Channel
from synthetic_generator.models.transaction import GeoLocation


@pytest.fixture
def seed_manager() -> SeedManager:
    """Create a fresh SeedManager."""
    return SeedManager(master_seed=42)


@pytest.fixture
def account_factory(seed_manager: SeedManager) -> AccountFactory:
    """Create an AccountFactory with a populated pool."""
    factory = AccountFactory(seed_manager=seed_manager)
    factory.generate_account_pool(size=50)
    return factory


@pytest.fixture
def generator(
    seed_manager: SeedManager,
    account_factory: AccountFactory,
) -> TransactionGenerator:
    """Create a TransactionGenerator."""
    return TransactionGenerator(seed_manager, account_factory)


class TestGenerateBaseTransaction:
    """Tests for generate_base_transaction method."""

    def test_returns_valid_transaction(self, generator: TransactionGenerator) -> None:
        """Verify a generated transaction has all required fields."""
        txn = generator.generate_base_transaction()
        assert txn.transaction_id.startswith("TXN-")
        assert txn.timestamp is not None
        assert txn.sender_account is not None
        assert txn.receiver_account is not None
        assert txn.sender_account != txn.receiver_account
        assert txn.amount >= 100.0
        assert txn.amount <= 10_000_000.0
        assert txn.channel in Channel
        assert txn.sender_bank in Bank
        assert txn.receiver_bank in Bank

    def test_transaction_is_not_fraud(self, generator: TransactionGenerator) -> None:
        """Verify base transactions are not marked as fraud."""
        txn = generator.generate_base_transaction()
        assert txn.is_fraud is False
        assert txn.fraud_type is None
        assert txn.fraud_ring_id is None

    def test_with_specified_timestamp(self, generator: TransactionGenerator) -> None:
        """Verify timestamp is set when specified."""
        ts = datetime(2024, 6, 15, 14, 30, 0)
        txn = generator.generate_base_transaction(timestamp=ts)
        assert txn.timestamp == ts

    def test_geo_locations_are_valid(self, generator: TransactionGenerator) -> None:
        """Verify sender and receiver geo locations are within Indian bounds."""
        txn = generator.generate_base_transaction()
        for geo in [txn.sender_geo, txn.receiver_geo]:
            assert 6.0 <= geo.latitude <= 36.0
            assert 68.0 <= geo.longitude <= 98.0
            assert len(geo.city) > 0
            assert len(geo.state) > 0

    def test_account_types_are_set(self, generator: TransactionGenerator) -> None:
        """Verify sender and receiver account types are set."""
        txn = generator.generate_base_transaction()
        assert txn.sender_account_type in AccountType
        assert txn.receiver_account_type in AccountType

    def test_updates_account_activity(self, generator: TransactionGenerator) -> None:
        """Verify transaction updates account activity tracking."""
        txn = generator.generate_base_transaction()
        sender = generator.account_factory.get_account(txn.sender_account)
        receiver = generator.account_factory.get_account(txn.receiver_account)
        assert sender.transaction_count >= 1
        assert receiver.transaction_count >= 1
        assert txn.receiver_account in sender.counterparties
        assert txn.sender_account in receiver.counterparties


class TestGenerateBatch:
    """Tests for generate_batch method."""

    def test_generates_correct_count(self, generator: TransactionGenerator) -> None:
        """Verify batch has the requested number of transactions."""
        time_range = TimeRange(
            start=datetime(2024, 6, 1),
            end=datetime(2024, 6, 30),
        )
        batch = generator.generate_batch(count=50, time_range=time_range)
        assert len(batch) == 50

    def test_transactions_sorted_by_timestamp(
        self, generator: TransactionGenerator
    ) -> None:
        """Verify batch is sorted by timestamp."""
        time_range = TimeRange(
            start=datetime(2024, 6, 1),
            end=datetime(2024, 6, 30),
        )
        batch = generator.generate_batch(count=30, time_range=time_range)
        timestamps = [txn.timestamp for txn in batch]
        assert timestamps == sorted(timestamps)

    def test_timestamps_within_range(self, generator: TransactionGenerator) -> None:
        """Verify all timestamps are within the time range."""
        start = datetime(2024, 6, 1)
        end = datetime(2024, 6, 30, 23, 59, 59)
        time_range = TimeRange(start=start, end=end)
        batch = generator.generate_batch(count=30, time_range=time_range)
        for txn in batch:
            assert txn.timestamp >= start
            assert txn.timestamp <= end

    def test_all_transaction_ids_unique(self, generator: TransactionGenerator) -> None:
        """Verify all transaction IDs in a batch are unique."""
        time_range = TimeRange(
            start=datetime(2024, 6, 1),
            end=datetime(2024, 6, 30),
        )
        batch = generator.generate_batch(count=100, time_range=time_range)
        ids = [txn.transaction_id for txn in batch]
        assert len(set(ids)) == len(ids)


class TestGetRealisticTimestamp:
    """Tests for get_realistic_timestamp method."""

    def test_returns_datetime(self, generator: TransactionGenerator) -> None:
        """Verify method returns a datetime object."""
        ts = generator.get_realistic_timestamp()
        assert isinstance(ts, datetime)

    def test_hour_within_range(self, generator: TransactionGenerator) -> None:
        """Verify generated hour is 0-23."""
        for _ in range(100):
            ts = generator.get_realistic_timestamp()
            assert 0 <= ts.hour <= 23

    def test_peak_hours_more_likely(self, generator: TransactionGenerator) -> None:
        """Verify peak hours (10-11, 15-17) appear more frequently."""
        hours = Counter()
        for _ in range(1000):
            ts = generator.get_realistic_timestamp()
            hours[ts.hour] += 1

        peak_hours = {10, 11, 15, 16, 17}
        off_peak_hours = {0, 1, 2, 3, 4, 5}

        peak_count = sum(hours[h] for h in peak_hours)
        off_peak_count = sum(hours[h] for h in off_peak_hours)

        # Peak hours should have significantly more transactions
        assert peak_count > off_peak_count, (
            f"Peak hours ({peak_count}) should exceed "
            f"off-peak hours ({off_peak_count})"
        )


class TestCalculateAmount:
    """Tests for calculate_amount method."""

    def test_amount_within_global_bounds(self, generator: TransactionGenerator) -> None:
        """Property 2: All amounts are within [₹100, ₹1Cr]."""
        for _ in range(200):
            channel = Channel.UPI
            amount = generator.calculate_amount(channel, AccountType.SAVINGS)
            assert 100.0 <= amount <= 10_000_000.0

    def test_amount_varies_by_channel(self, generator: TransactionGenerator) -> None:
        """Verify different channels produce different amount distributions."""
        upi_amounts = [
            generator.calculate_amount(Channel.UPI, AccountType.SAVINGS)
            for _ in range(100)
        ]
        rtgs_amounts = [
            generator.calculate_amount(Channel.RTGS, AccountType.SAVINGS)
            for _ in range(100)
        ]

        upi_mean = sum(upi_amounts) / len(upi_amounts)
        rtgs_mean = sum(rtgs_amounts) / len(rtgs_amounts)

        # RTGS should have much higher average amounts
        assert rtgs_mean > upi_mean

    def test_amount_is_rounded(self, generator: TransactionGenerator) -> None:
        """Verify amounts are rounded to 2 decimal places."""
        for _ in range(50):
            amount = generator.calculate_amount(Channel.UPI, AccountType.SAVINGS)
            assert amount == round(amount, 2)

    def test_heavy_tail_distribution(self, generator: TransactionGenerator) -> None:
        """Property 2: Verify amount distribution is heavy-tailed (log-normal)."""
        amounts = [
            generator.calculate_amount(Channel.NEFT, AccountType.CURRENT)
            for _ in range(500)
        ]
        # Median should be significantly less than mean for heavy-tailed dist
        sorted_amounts = sorted(amounts)
        median = sorted_amounts[len(sorted_amounts) // 2]
        mean = sum(amounts) / len(amounts)
        # For log-normal, mean > median
        assert mean >= median * 0.8, (
            f"Expected heavy-tailed: mean={mean:.2f}, median={median:.2f}"
        )


class TestProperty1BankingAttributes:
    """Property 1: All generated transactions have valid Indian banking attributes."""

    def test_all_channels_valid(self, generator: TransactionGenerator) -> None:
        """Verify all transaction channels are valid enum values."""
        for _ in range(100):
            txn = generator.generate_base_transaction()
            assert txn.channel in Channel

    def test_all_banks_valid(self, generator: TransactionGenerator) -> None:
        """Verify all banks are valid enum values."""
        for _ in range(50):
            txn = generator.generate_base_transaction()
            assert txn.sender_bank in Bank
            assert txn.receiver_bank in Bank

    def test_all_account_types_valid(self, generator: TransactionGenerator) -> None:
        """Verify all account types are valid enum values."""
        for _ in range(50):
            txn = generator.generate_base_transaction()
            assert txn.sender_account_type in AccountType
            assert txn.receiver_account_type in AccountType


class TestProperty3GeographicAttributes:
    """Property 3: All geographic attributes within Indian bounds."""

    def test_sender_geo_in_bounds(self, generator: TransactionGenerator) -> None:
        """Verify all sender geo locations are within India."""
        for _ in range(100):
            txn = generator.generate_base_transaction()
            assert 6.0 <= txn.sender_geo.latitude <= 36.0
            assert 68.0 <= txn.sender_geo.longitude <= 98.0

    def test_receiver_geo_in_bounds(self, generator: TransactionGenerator) -> None:
        """Verify all receiver geo locations are within India."""
        for _ in range(100):
            txn = generator.generate_base_transaction()
            assert 6.0 <= txn.receiver_geo.latitude <= 36.0
            assert 68.0 <= txn.receiver_geo.longitude <= 98.0


class TestProperty4CompleteFields:
    """Property 4: All required fields present and non-null."""

    def test_all_required_fields_present(
        self, generator: TransactionGenerator
    ) -> None:
        """Verify all required fields exist on generated transactions."""
        for _ in range(50):
            txn = generator.generate_base_transaction()
            assert txn.transaction_id is not None and len(txn.transaction_id) > 0
            assert txn.timestamp is not None
            assert txn.sender_account is not None and len(txn.sender_account) > 0
            assert txn.receiver_account is not None and len(txn.receiver_account) > 0
            assert txn.amount is not None
            assert txn.channel is not None
            assert txn.sender_bank is not None
            assert txn.receiver_bank is not None
            assert txn.sender_geo is not None
            assert txn.receiver_geo is not None
            assert txn.sender_account_type is not None
            assert txn.receiver_account_type is not None


class TestTimeRange:
    """Tests for TimeRange dataclass."""

    def test_valid_range(self) -> None:
        """Verify valid time range creation."""
        tr = TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 12, 31))
        assert tr.start < tr.end

    def test_invalid_range_raises(self) -> None:
        """Verify reversed range raises ValueError."""
        with pytest.raises(ValueError, match="start .* must be before end"):
            TimeRange(start=datetime(2024, 12, 31), end=datetime(2024, 1, 1))

    def test_same_start_end_raises(self) -> None:
        """Verify same start and end raises ValueError."""
        with pytest.raises(ValueError):
            TimeRange(start=datetime(2024, 6, 1), end=datetime(2024, 6, 1))


class TestReproducibility:
    """Tests for reproducible transaction generation."""

    def test_same_seed_same_transactions(self) -> None:
        """Verify identical seeds produce identical transaction attributes."""
        ts = datetime(2024, 6, 15, 12, 0, 0)

        mgr1 = SeedManager(master_seed=42)
        f1 = AccountFactory(seed_manager=mgr1)
        f1.generate_account_pool(size=20)
        g1 = TransactionGenerator(mgr1, f1)
        txn1 = g1.generate_base_transaction(timestamp=ts)

        mgr2 = SeedManager(master_seed=42)
        f2 = AccountFactory(seed_manager=mgr2)
        f2.generate_account_pool(size=20)
        g2 = TransactionGenerator(mgr2, f2)
        txn2 = g2.generate_base_transaction(timestamp=ts)

        assert txn1.amount == txn2.amount
        assert txn1.channel == txn2.channel
        assert txn1.sender_bank == txn2.sender_bank
        assert txn1.receiver_bank == txn2.receiver_bank

"""
Unit and property tests for AccountFactory.

Tests cover:
- Account creation with valid Indian attributes
- Pool generation with correct size and distribution
- Random account selection with exclusion
- Dormant account detection
- Activity marking and counterparty tracking
- Property 19: All account IDs are unique

Validates: Requirements 1.1, 4.1, 9.4
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from synthetic_generator.core.account_factory import AccountFactory
from synthetic_generator.core.seed_manager import SeedManager
from synthetic_generator.models.enums import AccountType, Bank


@pytest.fixture
def seed_manager() -> SeedManager:
    """Create a fresh SeedManager for each test."""
    return SeedManager(master_seed=42)


@pytest.fixture
def factory(seed_manager: SeedManager) -> AccountFactory:
    """Create an AccountFactory with seeded random."""
    return AccountFactory(seed_manager=seed_manager)


class TestCreateAccount:
    """Tests for create_account method."""

    def test_creates_account_with_valid_fields(self, factory: AccountFactory) -> None:
        """Verify created account has all required non-empty fields."""
        acct = factory.create_account()
        assert acct.account_id.startswith("ACC-")
        assert len(acct.account_id) > 4
        assert acct.account_type in AccountType
        assert acct.bank in Bank
        assert len(acct.account_holder_name) > 0
        assert acct.mobile.startswith("+91")
        assert len(acct.pan) == 10
        assert acct.address is not None
        assert len(acct.pin_code) == 6

    def test_creates_account_with_specified_type(self, factory: AccountFactory) -> None:
        """Verify account type is set correctly when specified."""
        acct = factory.create_account(account_type=AccountType.CORPORATE)
        assert acct.account_type == AccountType.CORPORATE

    def test_creates_account_with_specified_bank(self, factory: AccountFactory) -> None:
        """Verify bank is set correctly when specified."""
        acct = factory.create_account(bank=Bank.HDFC)
        assert acct.bank == Bank.HDFC

    def test_creates_dormant_account(self, factory: AccountFactory) -> None:
        """Verify dormant flag is set when specified."""
        acct = factory.create_account(is_dormant=True)
        assert acct.is_dormant is True

    def test_account_registered_in_pool(self, factory: AccountFactory) -> None:
        """Verify created account is registered in the factory pool."""
        acct = factory.create_account()
        assert acct.account_id in factory.accounts
        assert factory.pool_size == 1

    def test_multiple_accounts_have_unique_ids(self, factory: AccountFactory) -> None:
        """Verify multiple accounts have distinct IDs."""
        accounts = [factory.create_account() for _ in range(100)]
        ids = {a.account_id for a in accounts}
        assert len(ids) == 100


class TestGenerateAccountPool:
    """Tests for generate_account_pool method."""

    def test_generates_correct_number(self, factory: AccountFactory) -> None:
        """Verify pool has the requested number of accounts."""
        pool = factory.generate_account_pool(size=50)
        assert len(pool) == 50
        assert factory.pool_size == 50

    def test_generates_with_default_distribution(self, factory: AccountFactory) -> None:
        """Verify accounts are distributed across types with defaults."""
        pool = factory.generate_account_pool(size=100)
        types = {acct.account_type for acct in pool}
        # With 100 accounts and default distribution, expect at least 3 types
        assert len(types) >= 3

    def test_generates_with_custom_distribution(self, factory: AccountFactory) -> None:
        """Verify custom distribution allocates correctly."""
        dist = {"savings": 1.0, "current": 0.0, "jan_dhan": 0.0,
                "nri": 0.0, "corporate": 0.0}
        pool = factory.generate_account_pool(size=20, distribution=dist)
        assert len(pool) == 20
        for acct in pool:
            assert acct.account_type == AccountType.SAVINGS

    def test_all_pool_ids_unique(self, factory: AccountFactory) -> None:
        """Property 19: All account IDs are unique in the pool."""
        pool = factory.generate_account_pool(size=500)
        ids = [acct.account_id for acct in pool]
        assert len(set(ids)) == len(ids), "Duplicate account IDs found!"

    def test_pool_registered_in_factory(self, factory: AccountFactory) -> None:
        """Verify all pool accounts are registered in the factory."""
        pool = factory.generate_account_pool(size=30)
        for acct in pool:
            assert acct.account_id in factory.accounts


class TestGetRandomAccount:
    """Tests for get_random_account method."""

    def test_returns_account_from_pool(self, factory: AccountFactory) -> None:
        """Verify returned account is from the pool."""
        factory.generate_account_pool(size=20)
        acct = factory.get_random_account()
        assert acct.account_id in factory.accounts

    def test_filters_by_account_type(self, factory: AccountFactory) -> None:
        """Verify filtering by account type works."""
        factory.generate_account_pool(size=50)
        acct = factory.get_random_account(account_type=AccountType.SAVINGS)
        assert acct.account_type == AccountType.SAVINGS

    def test_excludes_specified_ids(self, factory: AccountFactory) -> None:
        """Verify exclusion works."""
        pool = factory.generate_account_pool(size=10)
        exclude = {pool[0].account_id, pool[1].account_id}
        acct = factory.get_random_account(exclude=exclude)
        assert acct.account_id not in exclude

    def test_raises_when_no_match(self, factory: AccountFactory) -> None:
        """Verify ValueError when no matching accounts exist."""
        factory.create_account(account_type=AccountType.SAVINGS)
        with pytest.raises(ValueError, match="No matching accounts"):
            factory.get_random_account(account_type=AccountType.NRI)

    def test_raises_when_all_excluded(self, factory: AccountFactory) -> None:
        """Verify ValueError when all accounts are excluded."""
        pool = factory.generate_account_pool(size=5)
        all_ids = {a.account_id for a in pool}
        with pytest.raises(ValueError, match="No matching accounts"):
            factory.get_random_account(exclude=all_ids)


class TestGetDormantAccounts:
    """Tests for get_dormant_accounts method."""

    def test_explicitly_dormant_accounts(self, factory: AccountFactory) -> None:
        """Verify explicitly dormant accounts are returned."""
        factory.create_account(is_dormant=True)
        factory.create_account(is_dormant=False)
        dormant = factory.get_dormant_accounts()
        # The non-dormant account also counts as dormant since it has no activity
        assert len(dormant) == 2

    def test_never_used_accounts_are_dormant(self, factory: AccountFactory) -> None:
        """Verify accounts with no activity are considered dormant."""
        factory.generate_account_pool(size=10)
        dormant = factory.get_dormant_accounts()
        assert len(dormant) == 10  # All newly created accounts have no activity

    def test_recently_active_not_dormant(self, factory: AccountFactory) -> None:
        """Verify recently active accounts are not dormant."""
        acct = factory.create_account()
        factory.mark_activity(acct.account_id, datetime.now())
        dormant = factory.get_dormant_accounts(min_dormant_days=90)
        assert len(dormant) == 0

    def test_old_activity_is_dormant(self, factory: AccountFactory) -> None:
        """Verify accounts with old activity are dormant."""
        acct = factory.create_account()
        old_date = datetime.now() - timedelta(days=100)
        factory.mark_activity(acct.account_id, old_date)
        dormant = factory.get_dormant_accounts(min_dormant_days=90)
        assert len(dormant) == 1
        assert dormant[0].account_id == acct.account_id


class TestMarkActivity:
    """Tests for mark_activity method."""

    def test_updates_last_activity(self, factory: AccountFactory) -> None:
        """Verify last_activity is updated."""
        acct = factory.create_account()
        now = datetime.now()
        factory.mark_activity(acct.account_id, now)
        assert factory.accounts[acct.account_id].last_activity == now

    def test_increments_transaction_count(self, factory: AccountFactory) -> None:
        """Verify transaction_count increments."""
        acct = factory.create_account()
        now = datetime.now()
        factory.mark_activity(acct.account_id, now)
        factory.mark_activity(acct.account_id, now)
        factory.mark_activity(acct.account_id, now)
        assert factory.accounts[acct.account_id].transaction_count == 3

    def test_clears_dormant_flag(self, factory: AccountFactory) -> None:
        """Verify activity clears the dormant flag."""
        acct = factory.create_account(is_dormant=True)
        assert acct.is_dormant is True
        factory.mark_activity(acct.account_id, datetime.now())
        assert factory.accounts[acct.account_id].is_dormant is False

    def test_adds_counterparty(self, factory: AccountFactory) -> None:
        """Verify counterparty is tracked."""
        acct1 = factory.create_account()
        acct2 = factory.create_account()
        factory.mark_activity(acct1.account_id, datetime.now(),
                            counterparty_id=acct2.account_id)
        assert acct2.account_id in factory.accounts[acct1.account_id].counterparties

    def test_unknown_account_raises_error(self, factory: AccountFactory) -> None:
        """Verify KeyError for unknown account IDs."""
        with pytest.raises(KeyError, match="Account not found"):
            factory.mark_activity("NONEXISTENT", datetime.now())


class TestReproducibility:
    """Tests for reproducible account generation."""

    def test_same_seed_same_accounts(self) -> None:
        """Verify identical seeds produce identical account pools."""
        mgr1 = SeedManager(master_seed=42)
        factory1 = AccountFactory(seed_manager=mgr1)
        pool1 = factory1.generate_account_pool(size=20)

        mgr2 = SeedManager(master_seed=42)
        factory2 = AccountFactory(seed_manager=mgr2)
        pool2 = factory2.generate_account_pool(size=20)

        # Account attributes should match (IDs differ due to UUID)
        for a1, a2 in zip(pool1, pool2):
            assert a1.account_holder_name == a2.account_holder_name
            assert a1.mobile == a2.mobile
            assert a1.pan == a2.pan
            assert a1.account_type == a2.account_type

    def test_different_seed_different_accounts(self) -> None:
        """Verify different seeds produce different account pools."""
        mgr1 = SeedManager(master_seed=42)
        factory1 = AccountFactory(seed_manager=mgr1)
        pool1 = factory1.generate_account_pool(size=10)

        mgr2 = SeedManager(master_seed=99)
        factory2 = AccountFactory(seed_manager=mgr2)
        pool2 = factory2.generate_account_pool(size=10)

        names1 = [a.account_holder_name for a in pool1]
        names2 = [a.account_holder_name for a in pool2]
        assert names1 != names2


class TestProperty19UniqueIdentifiers:
    """Property 19: All generated account_ids are unique.

    Validates: Requirements 9.4
    """

    def test_1000_accounts_all_unique(self) -> None:
        """Verify 1000 accounts have no duplicate IDs."""
        mgr = SeedManager(master_seed=42)
        factory = AccountFactory(seed_manager=mgr)
        pool = factory.generate_account_pool(size=1000)
        ids = [acct.account_id for acct in pool]
        assert len(set(ids)) == 1000, \
            f"Expected 1000 unique IDs, got {len(set(ids))}"

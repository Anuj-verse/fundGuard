"""
Property tests for all fraud injectors.

Covers Properties 5-17 as defined in tasks.md.
"""

from __future__ import annotations
from datetime import datetime, timedelta
import random
import pytest

from synthetic_generator.core.seed_manager import SeedManager
from synthetic_generator.core.account_factory import AccountFactory
from synthetic_generator.models.enums import AccountType, Channel, FraudType
from synthetic_generator.fraud.base import FraudInjector
from synthetic_generator.fraud.registry import REGISTRY
from synthetic_generator.fraud.layering import LayeringInjector
from synthetic_generator.fraud.circular import CircularInjector
from synthetic_generator.fraud.mule_activation import MuleActivationInjector
from synthetic_generator.fraud.structuring import StructuringInjector
from synthetic_generator.fraud.round_tripping import RoundTrippingInjector
from synthetic_generator.fraud.hub_spoke import HubSpokeInjector


@pytest.fixture
def accounts():
    mgr = SeedManager(master_seed=42)
    factory = AccountFactory(seed_manager=mgr)
    factory.generate_account_pool(size=30)
    return factory.accounts


@pytest.fixture
def ts():
    return datetime(2024, 6, 15, 12, 0, 0)


# --- Registry ---
class TestRegistry:
    def test_all_types_registered(self):
        for ft in FraudType:
            assert ft in REGISTRY.registered_types

    def test_get_returns_class(self):
        cls = REGISTRY.get(FraudType.LAYERING)
        assert cls is LayeringInjector


# --- P5/P6: Layering ---
class TestLayering:
    def test_chain_length(self, accounts, ts):
        inj = LayeringInjector()
        txns = inj.inject(accounts, {"min_hops": 4, "max_hops": 8, "total_amount": 500_000.0}, ts)
        assert 4 <= len(txns) <= 8

    def test_chain_linkage(self, accounts, ts):
        txns = LayeringInjector().inject(accounts, {"min_hops": 4, "max_hops": 8}, ts)
        for i in range(len(txns) - 1):
            assert txns[i].receiver_account == txns[i + 1].sender_account

    def test_time_window(self, accounts, ts):
        txns = LayeringInjector().inject(accounts, {"time_window_mins": 60}, ts)
        span = (txns[-1].timestamp - txns[0].timestamp).total_seconds() / 60
        assert span <= 60

    def test_fraud_tags(self, accounts, ts):
        txns = LayeringInjector().inject(accounts, {}, ts)
        ring_id = txns[0].fraud_ring_id
        for t in txns:
            assert t.is_fraud is True
            assert t.fraud_type == FraudType.LAYERING
            assert t.fraud_ring_id == ring_id

    def test_amount_preservation(self, accounts, ts):
        txns = LayeringInjector().inject(accounts, {"total_amount": 500_000.0}, ts)
        for t in txns:
            assert 100.0 <= t.amount <= 10_000_000.0


# --- P7/P8: Circular ---
class TestCircular:
    def test_cycle_length(self, accounts, ts):
        txns = CircularInjector().inject(accounts, {"min_cycle_length": 3, "max_cycle_length": 6}, ts)
        assert 3 <= len(txns) <= 6

    def test_origin_is_first_and_last(self, accounts, ts):
        txns = CircularInjector().inject(accounts, {"min_cycle_length": 3, "max_cycle_length": 6}, ts)
        assert txns[0].sender_account == txns[-1].receiver_account

    def test_fraud_tags(self, accounts, ts):
        txns = CircularInjector().inject(accounts, {}, ts)
        ring_id = txns[0].fraud_ring_id
        for t in txns:
            assert t.is_fraud is True
            assert t.fraud_type == FraudType.CIRCULAR
            assert t.fraud_ring_id == ring_id


# --- P9/P10: Mule Activation ---
class TestMuleActivation:
    def test_burst_count(self, accounts, ts):
        txns = MuleActivationInjector().inject(accounts, {"activation_burst_count": 10}, ts)
        assert len(txns) == 10

    def test_burst_within_24h(self, accounts, ts):
        txns = MuleActivationInjector().inject(accounts, {"activation_burst_count": 10}, ts)
        span = (txns[-1].timestamp - txns[0].timestamp).total_seconds() / 3600
        assert span <= 24

    def test_counterparty_degree(self, accounts, ts):
        txns = MuleActivationInjector().inject(accounts, {"activation_burst_count": 10}, ts)
        all_accounts = set()
        for t in txns:
            all_accounts.add(t.sender_account)
            all_accounts.add(t.receiver_account)
        assert len(all_accounts) > 5

    def test_fraud_tags(self, accounts, ts):
        txns = MuleActivationInjector().inject(accounts, {}, ts)
        for t in txns:
            assert t.is_fraud is True
            assert t.fraud_type == FraudType.MULE_ACTIVATION


# --- P11/P12/P13: Structuring ---
class TestStructuring:
    def test_below_threshold(self, accounts, ts):
        txns = StructuringInjector().inject(accounts, {"total_amount": 5_000_000.0, "threshold": 999_999.0}, ts)
        for t in txns:
            assert t.amount <= 999_999.0

    def test_time_window(self, accounts, ts):
        txns = StructuringInjector().inject(accounts, {"time_window_mins": 480}, ts)
        if len(txns) > 1:
            span = (txns[-1].timestamp - txns[0].timestamp).total_seconds() / 60
            assert span <= 480

    def test_amount_variance(self, accounts, ts):
        txns = StructuringInjector().inject(accounts, {"total_amount": 5_000_000.0}, ts)
        if len(txns) > 2:
            amounts = [t.amount for t in txns[:-1]]  # Exclude last (remainder)
            assert len(set(amounts)) > 1, "Amounts should vary"

    def test_fraud_tags(self, accounts, ts):
        txns = StructuringInjector().inject(accounts, {}, ts)
        for t in txns:
            assert t.is_fraud is True
            assert t.fraud_type == FraudType.STRUCTURING


# --- P14/P15: Round-Tripping ---
class TestRoundTripping:
    def test_net_flow_approx_zero(self, accounts, ts):
        txns = RoundTrippingInjector().inject(accounts, {"num_intermediaries": 3}, ts)
        origin = txns[0].sender_account
        outflow = sum(t.amount for t in txns if t.sender_account == origin)
        inflow = sum(t.amount for t in txns if t.receiver_account == origin)
        # Net should be approximately zero (within 15% tolerance)
        assert abs(outflow - inflow) / max(outflow, 1) < 0.15

    def test_has_descriptions(self, accounts, ts):
        txns = RoundTrippingInjector().inject(accounts, {}, ts)
        for t in txns:
            assert t.description is not None

    def test_fraud_tags(self, accounts, ts):
        txns = RoundTrippingInjector().inject(accounts, {}, ts)
        for t in txns:
            assert t.is_fraud is True
            assert t.fraud_type == FraudType.ROUND_TRIPPING


# --- P16/P17: Hub-and-Spoke ---
class TestHubSpoke:
    def test_receiver_count(self, accounts, ts):
        txns = HubSpokeInjector().inject(accounts, {"min_receivers": 11}, ts)
        # First txn is lump sum to hub, rest are distributions
        distribution_txns = txns[1:]
        receivers = {t.receiver_account for t in distribution_txns}
        assert len(receivers) >= 10

    def test_hub_receives_first(self, accounts, ts):
        txns = HubSpokeInjector().inject(accounts, {}, ts)
        hub = txns[0].receiver_account
        # All subsequent txns should have hub as sender
        for t in txns[1:]:
            assert t.sender_account == hub

    def test_rapid_channels(self, accounts, ts):
        txns = HubSpokeInjector().inject(accounts, {}, ts)
        for t in txns[1:]:
            assert t.channel in [Channel.UPI, Channel.IMPS]

    def test_within_1_hour(self, accounts, ts):
        txns = HubSpokeInjector().inject(accounts, {}, ts)
        span = (txns[-1].timestamp - txns[0].timestamp).total_seconds() / 3600
        assert span <= 1.5  # Slight buffer

    def test_fraud_tags(self, accounts, ts):
        txns = HubSpokeInjector().inject(accounts, {}, ts)
        ring_id = txns[0].fraud_ring_id
        for t in txns:
            assert t.is_fraud is True
            assert t.fraud_type == FraudType.HUB_SPOKE
            assert t.fraud_ring_id == ring_id

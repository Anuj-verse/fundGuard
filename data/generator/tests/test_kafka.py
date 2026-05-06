"""
Tests for Kafka rate limiter and producer.

Covers:
- Rate limiter configuration validation
- Rate limiter token acquisition
- Burst simulation
- Producer serialization
- Producer retry logic with mock
- Producer metrics

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from synthetic_generator.kafka.rate_limiter import BurstConfig, RateLimiter
from synthetic_generator.kafka.producer import TransactionProducer, _MockProducer
from synthetic_generator.models.enums import AccountType, Bank, Channel
from synthetic_generator.models.transaction import GeoLocation, Transaction


@pytest.fixture
def sample_transaction() -> Transaction:
    """Create a sample transaction for testing."""
    geo = GeoLocation(city="Mumbai", state="Maharashtra", latitude=19.076, longitude=72.877)
    return Transaction(
        transaction_id="TXN-TEST001",
        timestamp=datetime(2024, 6, 15, 12, 0, 0),
        sender_account="ACC-SENDER001",
        receiver_account="ACC-RECV001",
        amount=5000.0,
        channel=Channel.UPI,
        sender_bank=Bank.SBI,
        receiver_bank=Bank.HDFC,
        sender_geo=geo,
        receiver_geo=geo,
        sender_account_type=AccountType.SAVINGS,
        receiver_account_type=AccountType.CURRENT,
    )


# --- Rate Limiter Tests ---
class TestRateLimiterConfig:
    def test_valid_rate(self):
        limiter = RateLimiter(rate_per_sec=1000)
        assert limiter.rate_per_sec == 1000

    def test_min_rate(self):
        limiter = RateLimiter(rate_per_sec=100)
        assert limiter.rate_per_sec == 100

    def test_max_rate(self):
        limiter = RateLimiter(rate_per_sec=10000)
        assert limiter.rate_per_sec == 10000

    def test_below_min_raises(self):
        with pytest.raises(ValueError, match="rate_per_sec must be between"):
            RateLimiter(rate_per_sec=50)

    def test_above_max_raises(self):
        with pytest.raises(ValueError, match="rate_per_sec must be between"):
            RateLimiter(rate_per_sec=20000)


class TestRateLimiterAcquire:
    def test_sync_acquire(self):
        limiter = RateLimiter(rate_per_sec=10000)
        for _ in range(10):
            limiter.acquire_sync()
        assert limiter.metrics["total_acquired"] == 10

    @pytest.mark.asyncio
    async def test_async_acquire(self):
        limiter = RateLimiter(rate_per_sec=10000)
        for _ in range(10):
            await limiter.acquire()
        assert limiter.metrics["total_acquired"] == 10

    def test_reset(self):
        limiter = RateLimiter(rate_per_sec=10000)
        limiter.acquire_sync()
        limiter.acquire_sync()
        limiter.reset()
        assert limiter.metrics["total_acquired"] == 0


class TestBurstSimulation:
    def test_burst_config_defaults(self):
        bc = BurstConfig()
        assert bc.enabled is False
        assert bc.burst_size == 10000

    def test_start_burst(self):
        limiter = RateLimiter(
            rate_per_sec=1000,
            burst_config=BurstConfig(enabled=True, burst_size=5000, burst_duration_sec=5),
        )
        limiter.start_burst()
        assert limiter.is_bursting is True
        assert limiter.metrics["burst_count"] == 1

    def test_burst_not_active_when_disabled(self):
        limiter = RateLimiter(rate_per_sec=1000)
        limiter.start_burst()
        assert limiter.is_bursting is False


# --- Producer Tests ---
class TestProducerSerialization:
    def test_serialize_transaction(self, sample_transaction):
        data = TransactionProducer._serialize_transaction(sample_transaction)
        assert isinstance(data, bytes)
        assert b"TXN-TEST001" in data
        assert b"5000.0" in data

    def test_serialize_contains_required_fields(self, sample_transaction):
        import json
        data = json.loads(TransactionProducer._serialize_transaction(sample_transaction))
        assert "transaction_id" in data
        assert "timestamp" in data
        assert "amount" in data
        assert "channel" in data


class TestProducerWithMock:
    @pytest.mark.asyncio
    async def test_start_with_mock(self):
        producer = TransactionProducer()
        await producer.start()
        assert producer._started is True
        await producer.close()

    @pytest.mark.asyncio
    async def test_send_transaction(self, sample_transaction):
        producer = TransactionProducer()
        await producer.start()
        result = await producer.send_transaction(sample_transaction)
        assert result is True
        assert producer.metrics["sent_count"] == 1
        await producer.close()

    @pytest.mark.asyncio
    async def test_send_without_start_raises(self, sample_transaction):
        producer = TransactionProducer()
        with pytest.raises(RuntimeError, match="Producer not started"):
            await producer.send_transaction(sample_transaction)

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, sample_transaction):
        producer = TransactionProducer()
        await producer.start()
        await producer.send_transaction(sample_transaction)
        await producer.send_transaction(sample_transaction)
        metrics = producer.metrics
        assert metrics["sent_count"] == 2
        assert metrics["error_count"] == 0
        await producer.close()

    @pytest.mark.asyncio
    async def test_close_sets_not_started(self):
        producer = TransactionProducer()
        await producer.start()
        assert producer._started is True
        await producer.close()
        assert producer._started is False

    @pytest.mark.asyncio
    async def test_flush(self, sample_transaction):
        producer = TransactionProducer()
        await producer.start()
        await producer.send_transaction(sample_transaction)
        await producer.flush()  # Should not raise
        await producer.close()


class TestProducerRetry:
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, sample_transaction):
        producer = TransactionProducer(retries=2, retry_backoff_ms=10)
        await producer.start()

        # Make mock raise on first 2 calls then succeed
        call_count = 0
        original_send = producer._producer.send_and_wait

        async def failing_send(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionError("Kafka unavailable")
            return await original_send(*args, **kwargs)

        producer._producer.send_and_wait = failing_send
        result = await producer.send_transaction(sample_transaction)
        assert result is True
        assert producer.metrics["retry_count"] == 2
        await producer.close()

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self, sample_transaction):
        producer = TransactionProducer(retries=1, retry_backoff_ms=10)
        await producer.start()

        async def always_fail(*args, **kwargs):
            raise ConnectionError("Kafka down")

        producer._producer.send_and_wait = always_fail
        result = await producer.send_transaction(sample_transaction)
        assert result is False
        assert producer.metrics["error_count"] == 1
        await producer.close()


class TestProducerStream:
    @pytest.mark.asyncio
    async def test_start_stream(self, sample_transaction):
        producer = TransactionProducer()
        txns = [sample_transaction] * 5
        metrics = await producer.start_stream(txns, rate_per_sec=10000)
        assert metrics["total"] == 5
        assert metrics["sent"] == 5
        assert metrics["errors"] == 0
        await producer.close()

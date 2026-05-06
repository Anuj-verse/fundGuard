"""
Pytest configuration and fixtures for Synthetic Data Generator tests.

This module provides shared fixtures for testing the synthetic data generator
components including configuration, account factory, and transaction generator.

Usage:
    Import fixtures in test modules:
    
    ```python
    def test_something(default_config, account_factory):
        # Use fixtures in tests
        pass
    ```
"""

import pytest
from datetime import datetime, timedelta
from typing import Any


# Placeholder fixtures - will be updated as components are implemented


@pytest.fixture
def sample_seed() -> int:
    """Default seed for reproducible tests."""
    return 42


@pytest.fixture
def sample_timestamp() -> datetime:
    """Sample timestamp for testing."""
    return datetime(2024, 1, 15, 10, 30, 0)


@pytest.fixture
def sample_time_range(sample_timestamp: datetime) -> tuple[datetime, datetime]:
    """Sample time range for transaction generation."""
    start = sample_timestamp
    end = sample_timestamp + timedelta(hours=24)
    return start, end


@pytest.fixture
def sample_indian_banking_config() -> dict[str, Any]:
    """Sample Indian banking configuration for tests."""
    return {
        "banks": [
            {"name": "SBI", "weight": 0.25},
            {"name": "PNB", "weight": 0.15},
            {"name": "BOB", "weight": 0.15},
            {"name": "UNION_BANK", "weight": 0.15},
            {"name": "HDFC", "weight": 0.15},
            {"name": "ICICI", "weight": 0.15},
        ],
        "account_types": {
            "savings": 0.60,
            "current": 0.15,
            "jan_dhan": 0.10,
            "nri": 0.05,
            "corporate": 0.10,
        },
        "channels": {
            "UPI": 0.45,
            "NEFT": 0.15,
            "RTGS": 0.05,
            "IMPS": 0.20,
            "ATM": 0.08,
            "POS": 0.05,
            "INTERNET_BANKING": 0.02,
        },
        "cities": [
            {"name": "Mumbai", "state": "Maharashtra", "weight": 0.15},
            {"name": "Delhi", "state": "Delhi", "weight": 0.12},
            {"name": "Bangalore", "state": "Karnataka", "weight": 0.10},
        ],
        "amount_range": {
            "min": 100.0,
            "max": 10000000.0,
            "distribution": "log_normal",
            "mean_log": 8.5,
            "std_log": 1.5,
        },
        "temporal": {
            "peak_hours": [10, 11, 15, 16, 17],
            "peak_weight": 2.0,
            "off_peak_weight": 0.5,
        },
    }


@pytest.fixture
def sample_fraud_pattern_config() -> dict[str, Any]:
    """Sample fraud pattern configuration for tests."""
    return {
        "layering": {
            "enabled": True,
            "weight": 0.167,
            "min_hops": 4,
            "max_hops": 8,
            "time_window_mins": 60,
        },
        "circular": {
            "enabled": True,
            "weight": 0.167,
            "min_cycle_length": 3,
            "max_cycle_length": 6,
        },
        "mule_activation": {
            "enabled": True,
            "weight": 0.167,
            "min_dormant_days": 30,
            "activation_burst_count": 15,
        },
        "structuring": {
            "enabled": True,
            "weight": 0.167,
            "threshold": 999999.0,
            "time_window_mins": 120,
        },
        "round_tripping": {
            "enabled": True,
            "weight": 0.167,
            "duration_days": 7,
        },
        "hub_spoke": {
            "enabled": True,
            "weight": 0.166,
            "min_receivers": 10,
            "distribution_window_mins": 60,
        },
    }


# Fixtures will be expanded as components are implemented:
# - default_config: GeneratorConfig
# - account_factory: AccountFactory
# - transaction_generator: TransactionGenerator
# - sample_accounts: list[Account]
# - sample_transactions: list[Transaction]

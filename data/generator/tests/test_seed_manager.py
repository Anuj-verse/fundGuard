"""
Unit tests for SeedManager.

Tests cover:
- Deterministic seed derivation from master seed
- Reproducibility across numpy, Python random, and Faker
- Checkpoint (get_seed_state) and restore (restore_seed_state)
- Different master seeds produce different outputs
- Edge cases: seed=0, very large seeds

Requirements: 12.1, 12.4, 12.5
"""

from __future__ import annotations

import random

import numpy as np
import pytest
from faker import Faker

from synthetic_generator.core.seed_manager import SeedManager


class TestSeedManagerInit:
    """Tests for SeedManager initialization."""

    def test_init_stores_master_seed(self) -> None:
        """Test that master seed is stored correctly."""
        mgr = SeedManager(master_seed=42)
        assert mgr.master_seed == 42

    def test_init_derives_subsystem_seeds(self) -> None:
        """Test that subsystem seeds are derived and are integers."""
        mgr = SeedManager(master_seed=42)
        assert isinstance(mgr.numpy_seed, int)
        assert isinstance(mgr.python_seed, int)
        assert isinstance(mgr.faker_seed, int)

    def test_init_seeds_are_deterministic(self) -> None:
        """Test that the same master seed always produces the same derived seeds."""
        mgr1 = SeedManager(master_seed=42)
        mgr2 = SeedManager(master_seed=42)

        assert mgr1.numpy_seed == mgr2.numpy_seed
        assert mgr1.python_seed == mgr2.python_seed
        assert mgr1.faker_seed == mgr2.faker_seed

    def test_init_different_master_seeds_produce_different_derived_seeds(self) -> None:
        """Test that different master seeds produce different derived seeds."""
        mgr1 = SeedManager(master_seed=42)
        mgr2 = SeedManager(master_seed=99)

        assert mgr1.numpy_seed != mgr2.numpy_seed
        assert mgr1.python_seed != mgr2.python_seed
        assert mgr1.faker_seed != mgr2.faker_seed

    def test_init_subsystem_seeds_are_independent(self) -> None:
        """Test that derived seeds for different subsystems are different."""
        mgr = SeedManager(master_seed=42)
        seeds = {mgr.numpy_seed, mgr.python_seed, mgr.faker_seed}
        assert len(seeds) == 3, "All three subsystem seeds should be distinct"

    def test_faker_instance_available(self) -> None:
        """Test that a Faker instance is available via the property."""
        mgr = SeedManager(master_seed=42)
        assert isinstance(mgr.faker, Faker)


class TestSetAllSeeds:
    """Tests for set_all_seeds method."""

    def test_set_all_seeds_numpy_reproducible(self) -> None:
        """Test that numpy produces identical results after set_all_seeds."""
        mgr = SeedManager(master_seed=42)
        result1 = np.random.rand(10).tolist()

        mgr.set_all_seeds(42)
        result2 = np.random.rand(10).tolist()

        assert result1 == result2

    def test_set_all_seeds_python_random_reproducible(self) -> None:
        """Test that Python random produces identical results after set_all_seeds."""
        mgr = SeedManager(master_seed=42)
        result1 = [random.random() for _ in range(10)]

        mgr.set_all_seeds(42)
        result2 = [random.random() for _ in range(10)]

        assert result1 == result2

    def test_set_all_seeds_faker_reproducible(self) -> None:
        """Test that Faker produces identical results after set_all_seeds."""
        mgr = SeedManager(master_seed=42)
        result1 = [mgr.faker.name() for _ in range(10)]

        mgr.set_all_seeds(42)
        result2 = [mgr.faker.name() for _ in range(10)]

        assert result1 == result2

    def test_set_all_seeds_updates_master_seed(self) -> None:
        """Test that set_all_seeds updates the stored master seed."""
        mgr = SeedManager(master_seed=42)
        mgr.set_all_seeds(99)
        assert mgr.master_seed == 99

    def test_set_all_seeds_updates_derived_seeds(self) -> None:
        """Test that set_all_seeds updates all derived seeds."""
        mgr = SeedManager(master_seed=42)
        old_numpy = mgr.numpy_seed
        old_python = mgr.python_seed
        old_faker = mgr.faker_seed

        mgr.set_all_seeds(99)

        assert mgr.numpy_seed != old_numpy
        assert mgr.python_seed != old_python
        assert mgr.faker_seed != old_faker


class TestGetSeedState:
    """Tests for get_seed_state method."""

    def test_get_seed_state_returns_dict(self) -> None:
        """Test that get_seed_state returns a dictionary."""
        mgr = SeedManager(master_seed=42)
        state = mgr.get_seed_state()
        assert isinstance(state, dict)

    def test_get_seed_state_contains_required_keys(self) -> None:
        """Test that state contains all required keys."""
        mgr = SeedManager(master_seed=42)
        state = mgr.get_seed_state()

        required_keys = {
            "master_seed", "numpy_seed", "python_seed",
            "faker_seed", "numpy_state", "python_state",
        }
        assert required_keys.issubset(set(state.keys()))

    def test_get_seed_state_captures_master_seed(self) -> None:
        """Test that state captures the correct master seed."""
        mgr = SeedManager(master_seed=42)
        state = mgr.get_seed_state()
        assert state["master_seed"] == 42

    def test_get_seed_state_captures_derived_seeds(self) -> None:
        """Test that state captures correct derived seeds."""
        mgr = SeedManager(master_seed=42)
        state = mgr.get_seed_state()
        assert state["numpy_seed"] == mgr.numpy_seed
        assert state["python_seed"] == mgr.python_seed
        assert state["faker_seed"] == mgr.faker_seed


class TestRestoreSeedState:
    """Tests for restore_seed_state method."""

    def test_restore_numpy_state(self) -> None:
        """Test that numpy state is correctly restored."""
        mgr = SeedManager(master_seed=42)

        # Generate some values to advance the state
        np.random.rand(5)

        # Capture state
        state = mgr.get_seed_state()

        # Generate more values
        expected = np.random.rand(10).tolist()

        # Restore and regenerate
        mgr.restore_seed_state(state)
        actual = np.random.rand(10).tolist()

        assert expected == actual

    def test_restore_python_random_state(self) -> None:
        """Test that Python random state is correctly restored."""
        mgr = SeedManager(master_seed=42)

        # Generate some values to advance the state
        for _ in range(5):
            random.random()

        # Capture state
        state = mgr.get_seed_state()

        # Generate more values
        expected = [random.random() for _ in range(10)]

        # Restore and regenerate
        mgr.restore_seed_state(state)
        actual = [random.random() for _ in range(10)]

        assert expected == actual

    def test_restore_updates_attributes(self) -> None:
        """Test that restore updates SeedManager's attributes."""
        mgr = SeedManager(master_seed=42)
        state = mgr.get_seed_state()

        mgr.set_all_seeds(99)  # Change to different seed
        assert mgr.master_seed == 99

        mgr.restore_seed_state(state)
        assert mgr.master_seed == 42
        assert mgr.numpy_seed == state["numpy_seed"]
        assert mgr.python_seed == state["python_seed"]
        assert mgr.faker_seed == state["faker_seed"]

    def test_restore_missing_key_raises_error(self) -> None:
        """Test that missing keys in state dict raises KeyError."""
        mgr = SeedManager(master_seed=42)

        with pytest.raises(KeyError, match="Missing required keys"):
            mgr.restore_seed_state({"master_seed": 42})

    def test_checkpoint_restore_round_trip(self) -> None:
        """Test full checkpoint and restore round-trip preserves generation."""
        mgr = SeedManager(master_seed=42)

        # Advance state
        np.random.rand(100)
        for _ in range(100):
            random.random()

        # Checkpoint
        state = mgr.get_seed_state()

        # Generate "future" data
        numpy_future = np.random.rand(50).tolist()
        random_future = [random.random() for _ in range(50)]

        # Restore checkpoint
        mgr.restore_seed_state(state)

        # Regenerate — must match
        numpy_replayed = np.random.rand(50).tolist()
        random_replayed = [random.random() for _ in range(50)]

        assert numpy_future == numpy_replayed
        assert random_future == random_replayed


class TestDeriveSeed:
    """Tests for _derive_seed static method."""

    def test_derive_seed_is_deterministic(self) -> None:
        """Test that _derive_seed returns the same value for same inputs."""
        seed1 = SeedManager._derive_seed(42, "numpy")
        seed2 = SeedManager._derive_seed(42, "numpy")
        assert seed1 == seed2

    def test_derive_seed_different_subsystems(self) -> None:
        """Test that different subsystem names produce different seeds."""
        numpy_seed = SeedManager._derive_seed(42, "numpy")
        python_seed = SeedManager._derive_seed(42, "python")
        faker_seed = SeedManager._derive_seed(42, "faker")
        assert len({numpy_seed, python_seed, faker_seed}) == 3

    def test_derive_seed_different_master_seeds(self) -> None:
        """Test that different master seeds produce different derived seeds."""
        seed1 = SeedManager._derive_seed(42, "numpy")
        seed2 = SeedManager._derive_seed(99, "numpy")
        assert seed1 != seed2

    def test_derive_seed_returns_32_bit_int(self) -> None:
        """Test that derived seed fits in 32 bits."""
        seed = SeedManager._derive_seed(42, "numpy")
        assert 0 <= seed < 2**32


class TestEdgeCases:
    """Tests for edge cases."""

    def test_seed_zero(self) -> None:
        """Test that seed=0 works correctly."""
        mgr = SeedManager(master_seed=0)
        assert mgr.master_seed == 0

        # Should produce deterministic output
        mgr.set_all_seeds(0)
        result1 = np.random.rand(5).tolist()

        mgr.set_all_seeds(0)
        result2 = np.random.rand(5).tolist()

        assert result1 == result2

    def test_very_large_seed(self) -> None:
        """Test that very large seed values work correctly."""
        large_seed = 2**31 - 1
        mgr = SeedManager(master_seed=large_seed)
        assert mgr.master_seed == large_seed

        # Should produce deterministic output
        mgr.set_all_seeds(large_seed)
        result1 = np.random.rand(5).tolist()

        mgr.set_all_seeds(large_seed)
        result2 = np.random.rand(5).tolist()

        assert result1 == result2

    def test_repr(self) -> None:
        """Test __repr__ returns a useful string."""
        mgr = SeedManager(master_seed=42)
        repr_str = repr(mgr)
        assert "SeedManager" in repr_str
        assert "master_seed=42" in repr_str
        assert "numpy_seed=" in repr_str
        assert "python_seed=" in repr_str
        assert "faker_seed=" in repr_str


class TestReproducibility:
    """Integration-style tests for full reproducibility guarantee."""

    def test_full_reproducibility_across_instances(self) -> None:
        """Test that two SeedManager instances with same seed produce identical outputs."""
        mgr1 = SeedManager(master_seed=42)
        numpy_1 = np.random.rand(20).tolist()
        random_1 = [random.random() for _ in range(20)]
        faker_1 = [mgr1.faker.name() for _ in range(10)]

        mgr2 = SeedManager(master_seed=42)
        numpy_2 = np.random.rand(20).tolist()
        random_2 = [random.random() for _ in range(20)]
        faker_2 = [mgr2.faker.name() for _ in range(10)]

        assert numpy_1 == numpy_2
        assert random_1 == random_2
        assert faker_1 == faker_2

    def test_different_seeds_produce_different_outputs(self) -> None:
        """Test that different master seeds produce different outputs."""
        mgr1 = SeedManager(master_seed=42)
        numpy_1 = np.random.rand(20).tolist()

        mgr2 = SeedManager(master_seed=99)
        numpy_2 = np.random.rand(20).tolist()

        assert numpy_1 != numpy_2

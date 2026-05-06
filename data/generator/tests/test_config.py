"""
Unit tests for configuration loader and validator.

Tests cover:
- Pydantic model validation
- YAML and JSON file loading
- CLI override merging
- Configuration validation logic
- Edge cases and error handling

Requirements: 12.2, 12.3
"""

import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from synthetic_generator.config import (
    AmountRangeConfig,
    CircularConfig,
    EvaluationConfig,
    FraudPatternsConfig,
    GeneratorConfig,
    HubSpokeConfig,
    IndianBankingConfig,
    KafkaConfig,
    LayeringConfig,
    MuleActivationConfig,
    RoundTrippingConfig,
    StreamingConfig,
    StructuringConfig,
    TemporalConfig,
    _deep_merge,
    get_effective_config,
    load_config,
    validate_config,
)


class TestKafkaConfig:
    """Tests for KafkaConfig model."""

    def test_default_values(self) -> None:
        """Test default Kafka configuration values."""
        config = KafkaConfig()
        assert config.bootstrap_servers == "localhost:9092"
        assert config.topic == "transactions"
        assert config.acks == "all"
        assert config.compression_type == "snappy"
        assert config.security_protocol == "PLAINTEXT"

    def test_valid_acks_values(self) -> None:
        """Test valid acks values are accepted."""
        for acks in ("0", "1", "all"):
            config = KafkaConfig(acks=acks)
            assert config.acks == acks

    def test_invalid_acks_raises_error(self) -> None:
        """Test invalid acks value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            KafkaConfig(acks="invalid")
        assert "acks must be one of" in str(exc_info.value)

    def test_valid_compression_types(self) -> None:
        """Test valid compression types are accepted."""
        for comp_type in ("none", "gzip", "snappy", "lz4", "zstd"):
            config = KafkaConfig(compression_type=comp_type)
            assert config.compression_type == comp_type

    def test_compression_type_case_insensitive(self) -> None:
        """Test compression type is case-insensitive."""
        config = KafkaConfig(compression_type="SNAPPY")
        assert config.compression_type == "snappy"

    def test_invalid_compression_type_raises_error(self) -> None:
        """Test invalid compression type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            KafkaConfig(compression_type="invalid")
        assert "compression_type must be one of" in str(exc_info.value)

    def test_valid_security_protocols(self) -> None:
        """Test valid security protocols are accepted."""
        for protocol in ("PLAINTEXT", "SSL", "SASL_PLAINTEXT", "SASL_SSL"):
            config = KafkaConfig(security_protocol=protocol)
            assert config.security_protocol == protocol

    def test_security_protocol_case_insensitive(self) -> None:
        """Test security protocol is case-insensitive."""
        config = KafkaConfig(security_protocol="ssl")
        assert config.security_protocol == "SSL"


class TestStreamingConfig:
    """Tests for StreamingConfig model."""

    def test_default_values(self) -> None:
        """Test default streaming configuration values."""
        config = StreamingConfig()
        assert config.rate_per_sec == 1000
        assert config.burst_enabled is False
        assert config.burst_size == 10000

    def test_rate_per_sec_bounds(self) -> None:
        """Test rate_per_sec validation bounds."""
        config = StreamingConfig(rate_per_sec=100)
        assert config.rate_per_sec == 100

        config = StreamingConfig(rate_per_sec=10000)
        assert config.rate_per_sec == 10000

    def test_rate_per_sec_below_minimum(self) -> None:
        """Test rate_per_sec below minimum raises error."""
        with pytest.raises(ValidationError):
            StreamingConfig(rate_per_sec=99)

    def test_rate_per_sec_above_maximum(self) -> None:
        """Test rate_per_sec above maximum raises error."""
        with pytest.raises(ValidationError):
            StreamingConfig(rate_per_sec=10001)


class TestAmountRangeConfig:
    """Tests for AmountRangeConfig model."""

    def test_default_values(self) -> None:
        """Test default amount range values."""
        config = AmountRangeConfig()
        assert config.min == 100.0
        assert config.max == 10000000.0
        assert config.distribution == "log_normal"

    def test_valid_distribution_types(self) -> None:
        """Test valid distribution types."""
        for dist in ("log_normal", "uniform"):
            config = AmountRangeConfig(distribution=dist)
            assert config.distribution == dist

    def test_invalid_distribution_raises_error(self) -> None:
        """Test invalid distribution raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AmountRangeConfig(distribution="invalid")
        assert "distribution must be one of" in str(exc_info.value)

    def test_min_greater_than_max_raises_error(self) -> None:
        """Test min > max raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AmountRangeConfig(min=1000.0, max=100.0)
        assert "must be <=" in str(exc_info.value)


class TestTemporalConfig:
    """Tests for TemporalConfig model."""

    def test_default_values(self) -> None:
        """Test default temporal configuration values."""
        config = TemporalConfig()
        assert config.peak_hours == [10, 11, 15, 16, 17]
        assert config.peak_weight == 2.0
        assert config.off_peak_weight == 0.5

    def test_valid_peak_hours(self) -> None:
        """Test valid peak hours are accepted."""
        config = TemporalConfig(peak_hours=[0, 12, 23])
        assert config.peak_hours == [0, 12, 23]

    def test_peak_hour_out_of_range_raises_error(self) -> None:
        """Test peak hour outside 0-23 raises error."""
        with pytest.raises(ValidationError):
            TemporalConfig(peak_hours=[24])

        with pytest.raises(ValidationError):
            TemporalConfig(peak_hours=[-1])


class TestIndianBankingConfig:
    """Tests for IndianBankingConfig model."""

    def test_default_values(self) -> None:
        """Test default Indian banking configuration."""
        config = IndianBankingConfig()
        assert config.banks == []
        assert config.account_types == {}

    def test_valid_bank_weights(self) -> None:
        """Test bank weights summing to ~1.0."""
        config = IndianBankingConfig(
            banks=[
                {"name": "SBI", "weight": 0.5},
                {"name": "HDFC", "weight": 0.5},
            ]
        )
        assert len(config.banks) == 2

    def test_invalid_bank_weights_raises_error(self) -> None:
        """Test bank weights not summing to ~1.0 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            IndianBankingConfig(
                banks=[
                    {"name": "SBI", "weight": 0.3},
                    {"name": "HDFC", "weight": 0.3},
                ]
            )
        assert "Bank weights must sum to ~1.0" in str(exc_info.value)

    def test_valid_account_type_weights(self) -> None:
        """Test account type weights summing to ~1.0."""
        config = IndianBankingConfig(
            account_types={
                "savings": 0.6,
                "current": 0.15,
                "jan_dhan": 0.10,
                "nri": 0.05,
                "corporate": 0.10,
            }
        )
        assert config.account_types["savings"] == 0.6

    def test_invalid_account_type_weights_raises_error(self) -> None:
        """Test account type weights not summing to ~1.0 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            IndianBankingConfig(
                account_types={
                    "savings": 0.3,
                    "current": 0.3,
                }
            )
        assert "Account type weights must sum to ~1.0" in str(exc_info.value)


class TestFraudPatternConfigs:
    """Tests for fraud pattern configuration models."""

    def test_layering_config_defaults(self) -> None:
        """Test default layering configuration."""
        config = LayeringConfig()
        assert config.enabled is True
        assert config.min_hops == 4
        assert config.max_hops == 8
        assert config.time_window_mins == 60

    def test_layering_hops_range_validation(self) -> None:
        """Test min_hops > max_hops raises error."""
        with pytest.raises(ValidationError) as exc_info:
            LayeringConfig(min_hops=8, max_hops=4)
        assert "must be <=" in str(exc_info.value)

    def test_circular_config_defaults(self) -> None:
        """Test default circular configuration."""
        config = CircularConfig()
        assert config.enabled is True
        assert config.min_cycle_length == 3
        assert config.max_cycle_length == 6

    def test_circular_cycle_range_validation(self) -> None:
        """Test min_cycle_length > max_cycle_length raises error."""
        with pytest.raises(ValidationError) as exc_info:
            CircularConfig(min_cycle_length=6, max_cycle_length=3)
        assert "must be <=" in str(exc_info.value)

    def test_mule_activation_config_defaults(self) -> None:
        """Test default mule activation configuration."""
        config = MuleActivationConfig()
        assert config.enabled is True
        assert config.min_dormant_days == 30
        assert config.activation_burst_count == 15

    def test_structuring_config_defaults(self) -> None:
        """Test default structuring configuration."""
        config = StructuringConfig()
        assert config.enabled is True
        assert config.threshold == 999999.0
        assert config.time_window_mins == 120

    def test_round_tripping_config_defaults(self) -> None:
        """Test default round-tripping configuration."""
        config = RoundTrippingConfig()
        assert config.enabled is True
        assert config.duration_days == 7

    def test_hub_spoke_config_defaults(self) -> None:
        """Test default hub-and-spoke configuration."""
        config = HubSpokeConfig()
        assert config.enabled is True
        assert config.min_receivers == 10
        assert config.distribution_window_mins == 60


class TestFraudPatternsConfig:
    """Tests for FraudPatternsConfig model."""

    def test_default_values(self) -> None:
        """Test default fraud patterns configuration."""
        config = FraudPatternsConfig()
        assert config.layering.enabled is True
        assert config.circular.enabled is True
        assert config.mule_activation.enabled is True

    def test_pattern_weights_validation(self) -> None:
        """Test enabled pattern weights must sum to ~1.0."""
        config = FraudPatternsConfig(
            layering=LayeringConfig(enabled=True, weight=0.5),
            circular=CircularConfig(enabled=True, weight=0.5),
            mule_activation=MuleActivationConfig(enabled=False),
            structuring=StructuringConfig(enabled=False),
            round_tripping=RoundTrippingConfig(enabled=False),
            hub_spoke=HubSpokeConfig(enabled=False),
        )
        assert config.layering.weight == 0.5

    def test_invalid_pattern_weights_raises_error(self) -> None:
        """Test pattern weights not summing to ~1.0 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            FraudPatternsConfig(
                layering=LayeringConfig(enabled=True, weight=0.3),
                circular=CircularConfig(enabled=True, weight=0.3),
            )
        assert "Enabled fraud pattern weights must sum to ~1.0" in str(exc_info.value)


class TestGeneratorConfig:
    """Tests for GeneratorConfig model."""

    def test_default_values(self) -> None:
        """Test default generator configuration values."""
        config = GeneratorConfig()
        assert config.seed == 42
        assert config.num_transactions == 100000
        assert config.fraud_rate == 0.02
        assert config.output_format == "file"

    def test_valid_output_formats(self) -> None:
        """Test valid output formats are accepted."""
        for fmt in ("kafka", "file", "both"):
            config = GeneratorConfig(output_format=fmt)
            assert config.output_format == fmt

    def test_output_format_case_insensitive(self) -> None:
        """Test output format is case-insensitive."""
        config = GeneratorConfig(output_format="KAFKA")
        assert config.output_format == "kafka"

    def test_invalid_output_format_raises_error(self) -> None:
        """Test invalid output format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GeneratorConfig(output_format="invalid")
        assert "output_format must be one of" in str(exc_info.value)

    def test_fraud_rate_bounds(self) -> None:
        """Test fraud rate must be between 0 and 1."""
        config = GeneratorConfig(fraud_rate=0.0)
        assert config.fraud_rate == 0.0

        config = GeneratorConfig(fraud_rate=1.0)
        assert config.fraud_rate == 1.0

    def test_fraud_rate_out_of_bounds_raises_error(self) -> None:
        """Test fraud rate outside 0-1 raises error."""
        with pytest.raises(ValidationError):
            GeneratorConfig(fraud_rate=-0.1)

        with pytest.raises(ValidationError):
            GeneratorConfig(fraud_rate=1.1)


class TestDeepMerge:
    """Tests for _deep_merge function."""

    def test_simple_merge(self) -> None:
        """Test simple dictionary merge."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self) -> None:
        """Test nested dictionary merge."""
        base = {"level1": {"a": 1, "b": 2}}
        override = {"level1": {"b": 3, "c": 4}}
        result = _deep_merge(base, override)
        assert result == {"level1": {"a": 1, "b": 3, "c": 4}}

    def test_deeply_nested_merge(self) -> None:
        """Test deeply nested dictionary merge."""
        base = {"l1": {"l2": {"a": 1, "b": 2}}}
        override = {"l1": {"l2": {"b": 3}}}
        result = _deep_merge(base, override)
        assert result == {"l1": {"l2": {"a": 1, "b": 3}}}

    def test_override_non_dict(self) -> None:
        """Test override replaces non-dict values."""
        base = {"a": {"nested": 1}}
        override = {"a": "simple"}
        result = _deep_merge(base, override)
        assert result == {"a": "simple"}


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_yaml_config(self, tmp_path: Path) -> None:
        """Test loading configuration from YAML file."""
        config_content = """
generator:
  seed: 123
  num_transactions: 5000
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = load_config(str(config_file))
        assert config.seed == 123
        assert config.num_transactions == 5000

    def test_load_json_config(self, tmp_path: Path) -> None:
        """Test loading configuration from JSON file."""
        config_content = json.dumps({
            "generator": {
                "seed": 456,
                "num_transactions": 10000
            }
        })
        config_file = tmp_path / "config.json"
        config_file.write_text(config_content)

        config = load_config(str(config_file))
        assert config.seed == 456
        assert config.num_transactions == 10000

    def test_load_nonexistent_file_raises_error(self) -> None:
        """Test loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_invalid_yaml_raises_error(self, tmp_path: Path) -> None:
        """Test invalid YAML syntax raises ValueError."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: :syntax")

        with pytest.raises(ValueError) as exc_info:
            load_config(str(config_file))
        assert "Invalid YAML syntax" in str(exc_info.value)

    def test_invalid_json_raises_error(self, tmp_path: Path) -> None:
        """Test invalid JSON syntax raises ValueError."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{invalid json}")

        with pytest.raises(ValueError) as exc_info:
            load_config(str(config_file))
        assert "Invalid JSON syntax" in str(exc_info.value)

    def test_unsupported_format_raises_error(self, tmp_path: Path) -> None:
        """Test unsupported file format raises ValueError."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("key = 'value'")

        with pytest.raises(ValueError) as exc_info:
            load_config(str(config_file))
        assert "Unsupported config file format" in str(exc_info.value)

    def test_cli_overrides_take_precedence(self, tmp_path: Path) -> None:
        """Test CLI overrides take precedence over file config."""
        config_content = """
generator:
  seed: 100
  num_transactions: 1000
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = load_config(
            str(config_file),
            cli_overrides={"seed": 999, "fraud_rate": 0.05},
        )
        assert config.seed == 999
        assert config.num_transactions == 1000  # From file
        assert config.fraud_rate == 0.05  # From CLI

    def test_default_config_when_no_file(self) -> None:
        """Test default configuration when no file provided."""
        config = load_config()
        assert config.seed == 42
        assert config.output_format == "file"

    def test_nested_cli_overrides(self, tmp_path: Path) -> None:
        """Test nested CLI overrides are merged correctly."""
        config_content = """
kafka:
  bootstrap_servers: "localhost:9092"
  topic: "original-topic"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = load_config(
            str(config_file),
            cli_overrides={"kafka": {"topic": "override-topic"}},
        )
        assert config.kafka.bootstrap_servers == "localhost:9092"
        assert config.kafka.topic == "override-topic"

    def test_flat_config_without_generator_wrapper(self, tmp_path: Path) -> None:
        """Test loading flat config without generator wrapper."""
        config_content = """
seed: 789
num_transactions: 2000
fraud_rate: 0.03
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = load_config(str(config_file))
        assert config.seed == 789
        assert config.num_transactions == 2000
        assert config.fraud_rate == 0.03


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_valid_config_returns_empty_list(self) -> None:
        """Test valid configuration returns empty error list."""
        config = GeneratorConfig()
        errors = validate_config(config)
        assert errors == []

    def test_kafka_required_for_kafka_output(self) -> None:
        """Test Kafka config required when output_format is 'kafka'."""
        config = GeneratorConfig(
            output_format="kafka",
            kafka=KafkaConfig(bootstrap_servers=""),
        )
        errors = validate_config(config)
        assert any("bootstrap_servers is required" in e for e in errors)

    def test_sasl_required_for_sasl_protocol(self) -> None:
        """Test SASL config required when using SASL protocol."""
        config = GeneratorConfig(
            kafka=KafkaConfig(
                security_protocol="SASL_SSL",
                sasl_mechanism=None,
                sasl_username=None,
            )
        )
        errors = validate_config(config)
        assert any("sasl_mechanism is required" in e for e in errors)
        assert any("sasl_username is required" in e for e in errors)

    def test_fraud_pattern_required_when_fraud_rate_positive(self) -> None:
        """Test at least one fraud pattern enabled when fraud_rate > 0."""
        config = GeneratorConfig(
            fraud_rate=0.02,
            fraud_patterns=FraudPatternsConfig(
                layering=LayeringConfig(enabled=False),
                circular=CircularConfig(enabled=False),
                mule_activation=MuleActivationConfig(enabled=False),
                structuring=StructuringConfig(enabled=False),
                round_tripping=RoundTrippingConfig(enabled=False),
                hub_spoke=HubSpokeConfig(enabled=False),
            ),
        )
        errors = validate_config(config)
        assert any("At least one fraud pattern must be enabled" in e for e in errors)

    def test_missing_account_types_warning(self) -> None:
        """Test warning for missing account types."""
        config = GeneratorConfig(
            indian_banking=IndianBankingConfig(
                account_types={"savings": 1.0}
            )
        )
        errors = validate_config(config)
        assert any("Account type distribution missing required types" in e for e in errors)

    def test_missing_channels_warning(self) -> None:
        """Test warning for missing channels."""
        config = GeneratorConfig(
            indian_banking=IndianBankingConfig(
                channels={"UPI": 1.0}
            )
        )
        errors = validate_config(config)
        assert any("Channel distribution missing required channels" in e for e in errors)

    def test_evaluation_fraud_rate_mismatch(self) -> None:
        """Test warning for fraud rate mismatch in evaluation config."""
        config = GeneratorConfig(
            fraud_rate=0.02,
            evaluation=EvaluationConfig(
                enabled=True,
                fraud_rate=0.05,
            ),
        )
        errors = validate_config(config)
        assert any("Fraud rate mismatch" in e for e in errors)

    def test_streaming_rate_validation(self) -> None:
        """Test streaming rate validation for streaming config."""
        # Pydantic validates rate_per_sec bounds at model creation
        with pytest.raises(ValidationError):
            StreamingConfig(rate_per_sec=50)


class TestGetEffectiveConfig:
    """Tests for get_effective_config function."""

    def test_returns_complete_config(self) -> None:
        """Test returns complete configuration dictionary."""
        config = GeneratorConfig(seed=123)
        result = get_effective_config(config)

        assert result["seed"] == 123
        assert "kafka" in result
        assert "fraud_patterns" in result

    def test_includes_metadata(self, tmp_path: Path) -> None:
        """Test includes metadata about config source."""
        config_content = "generator:\n  seed: 456\n"
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = load_config(str(config_file), cli_overrides={"fraud_rate": 0.03})
        result = get_effective_config(config)

        assert "_metadata" in result
        assert result["_metadata"]["config_path"] == str(config_file)
        assert result["_metadata"]["cli_overrides"] == {"fraud_rate": 0.03}

    def test_default_config_no_metadata(self) -> None:
        """Test default config has null metadata."""
        config = GeneratorConfig()
        result = get_effective_config(config)

        assert "_metadata" in result
        assert result["_metadata"]["config_path"] is None


class TestLoadDefaultYaml:
    """Tests for loading the actual default.yaml file."""

    def test_load_default_config(self) -> None:
        """Test loading the default.yaml configuration file."""
        default_config_path = Path(__file__).parent.parent / "config" / "default.yaml"

        if default_config_path.exists():
            config = load_config(str(default_config_path))
            assert config.seed == 42
            assert config.num_transactions == 100000
            assert config.fraud_rate == 0.02
            assert config.output_format == "file"

            # Validate loaded config
            errors = validate_config(config)
            assert errors == []

    def test_load_evaluation_config(self) -> None:
        """Test loading the evaluation.yaml configuration file."""
        eval_config_path = Path(__file__).parent.parent / "config" / "evaluation.yaml"

        if eval_config_path.exists():
            config = load_config(str(eval_config_path))
            # Evaluation config should have evaluation enabled
            assert config.evaluation.enabled is True

    def test_load_load_test_config(self) -> None:
        """Test loading the load_test.yaml configuration file."""
        load_test_path = Path(__file__).parent.parent / "config" / "load_test.yaml"

        if load_test_path.exists():
            config = load_config(str(load_test_path))
            # Load test config should have kafka output
            assert config.output_format in ("kafka", "both")


class TestConfigEdgeCases:
    """Tests for edge cases in configuration handling."""

    def test_empty_file_config(self, tmp_path: Path) -> None:
        """Test empty configuration file uses defaults."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("{}")

        config = load_config(str(config_file))
        assert config.seed == 42  # Default value

    def test_config_with_extra_fields_ignored(self, tmp_path: Path) -> None:
        """Test extra fields in config are ignored by Pydantic."""
        config_content = """
generator:
  seed: 789
  unknown_field: "should_be_ignored"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = load_config(str(config_file))
        assert config.seed == 789

    def test_unicode_in_config(self, tmp_path: Path) -> None:
        """Test Unicode characters in configuration."""
        config_content = """
generator:
  output_path: "./output/₹_transactions"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content, encoding="utf-8")

        config = load_config(str(config_file))
        assert "₹" in config.output_path

    def test_very_large_seed(self) -> None:
        """Test very large seed value."""
        config = GeneratorConfig(seed=2**31 - 1)
        assert config.seed == 2**31 - 1

    def test_zero_seed(self) -> None:
        """Test zero as seed value."""
        config = GeneratorConfig(seed=0)
        assert config.seed == 0

    def test_zero_fraud_rate(self) -> None:
        """Test zero fraud rate is valid."""
        config = GeneratorConfig(fraud_rate=0.0)
        errors = validate_config(config)
        # Should not require fraud patterns when fraud_rate is 0
        assert not any("fraud pattern" in e.lower() for e in errors)

    def test_cli_overrides_flat_config(self, tmp_path: Path) -> None:
        """Test CLI overrides work with flat config format."""
        config_content = """
seed: 100
num_transactions: 1000
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = load_config(str(config_file), cli_overrides={"seed": 200})
        assert config.seed == 200
        assert config.num_transactions == 1000

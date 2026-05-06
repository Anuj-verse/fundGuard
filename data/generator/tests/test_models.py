"""
Property tests for core data models.

These tests use Hypothesis to verify universal correctness properties
across all valid generated inputs for Transaction, Account, and FraudRing models.

Properties tested:
- Property 1: Valid Indian Banking Attributes
- Property 2: Amount Range Constraint
- Property 3: Valid Geographic Attributes
- Property 4: Complete Required Fields

Validates: Requirements 1.1, 1.2, 1.3, 1.5
"""

from __future__ import annotations

from datetime import datetime

import pytest
from hypothesis import given, settings, assume
from hypothesis.strategies import (
    builds,
    composite,
    datetimes,
    floats,
    from_type,
    integers,
    just,
    lists,
    sampled_from,
    sets,
    text,
)
from pydantic import ValidationError

from synthetic_generator.models.enums import AccountType, Bank, Channel, FraudType
from synthetic_generator.models.transaction import (
    Address,
    GeoLocation,
    HourDistribution,
    Transaction,
)
from synthetic_generator.models.account import Account
from synthetic_generator.models.fraud_ring import FraudRing


# ---------------------------------------------------------------------------
# Hypothesis strategies for generating valid model instances
# ---------------------------------------------------------------------------

@composite
def geo_location_strategy(draw):
    """Strategy for generating valid GeoLocation instances."""
    city = draw(sampled_from(["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad",
                               "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow"]))
    state = draw(sampled_from(["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu",
                                "Telangana", "West Bengal", "Gujarat", "Rajasthan",
                                "Uttar Pradesh"]))
    latitude = draw(floats(min_value=6.0, max_value=36.0, allow_nan=False, allow_infinity=False))
    longitude = draw(floats(min_value=68.0, max_value=98.0, allow_nan=False, allow_infinity=False))
    return GeoLocation(city=city, state=state, latitude=latitude, longitude=longitude)


@composite
def address_strategy(draw):
    """Strategy for generating valid Address instances."""
    city = draw(sampled_from(["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata"]))
    state = draw(sampled_from(["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "West Bengal"]))
    pin_codes = ["400001", "110001", "560001", "600001", "700001",
                 "500001", "411001", "380001", "302001", "226001"]
    pin_code = draw(sampled_from(pin_codes))
    return Address(line1="123 Test Road", city=city, state=state, pin_code=pin_code)


@composite
def transaction_strategy(draw):
    """Strategy for generating valid Transaction instances."""
    return Transaction(
        transaction_id=f"TXN-{draw(integers(min_value=1, max_value=999999))}",
        timestamp=draw(datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2025, 12, 31),
        )),
        sender_account=f"ACC-{draw(integers(min_value=1, max_value=999999))}",
        receiver_account=f"ACC-{draw(integers(min_value=1, max_value=999999))}",
        amount=draw(floats(min_value=100.0, max_value=10_000_000.0,
                           allow_nan=False, allow_infinity=False)),
        channel=draw(sampled_from(list(Channel))),
        sender_bank=draw(sampled_from(list(Bank))),
        receiver_bank=draw(sampled_from(list(Bank))),
        sender_geo=draw(geo_location_strategy()),
        receiver_geo=draw(geo_location_strategy()),
        sender_account_type=draw(sampled_from(list(AccountType))),
        receiver_account_type=draw(sampled_from(list(AccountType))),
        is_fraud=False,
        fraud_type=None,
        fraud_ring_id=None,
    )


@composite
def account_strategy(draw):
    """Strategy for generating valid Account instances."""
    pan_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    pan = "".join([
        draw(sampled_from(list(pan_letters))),
        draw(sampled_from(list(pan_letters))),
        draw(sampled_from(list(pan_letters))),
        draw(sampled_from(list(pan_letters))),
        draw(sampled_from(list(pan_letters))),
        str(draw(integers(min_value=0, max_value=9))),
        str(draw(integers(min_value=0, max_value=9))),
        str(draw(integers(min_value=0, max_value=9))),
        str(draw(integers(min_value=0, max_value=9))),
        draw(sampled_from(list(pan_letters))),
    ])
    mobile_suffix = str(draw(integers(min_value=100000000, max_value=999999999)))
    mobile_first = draw(sampled_from(["6", "7", "8", "9"]))
    mobile = f"+91{mobile_first}{mobile_suffix}"

    return Account(
        account_id=f"ACC-{draw(integers(min_value=1, max_value=999999))}",
        account_type=draw(sampled_from(list(AccountType))),
        bank=draw(sampled_from(list(Bank))),
        account_holder_name=draw(sampled_from(["Raj Kumar", "Priya Sharma", "Amit Patel",
                                                "Sita Devi", "Vijay Singh"])),
        mobile=mobile,
        pan=pan,
        address=draw(address_strategy()),
        pin_code=draw(sampled_from(["400001", "110001", "560001", "600001", "700001"])),
    )


# ---------------------------------------------------------------------------
# Property 1: Valid Indian Banking Attributes
# ---------------------------------------------------------------------------

class TestProperty1ValidBankingAttributes:
    """Feature: synthetic-data-generator, Property 1: Valid Indian Banking Attributes

    For any generated transaction, all banking attributes must be valid enum values.
    Validates: Requirements 1.1
    """

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_channel_is_valid_enum(self, txn: Transaction) -> None:
        """Verify channel is a valid Channel enum value."""
        assert txn.channel in Channel

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_sender_bank_is_valid_enum(self, txn: Transaction) -> None:
        """Verify sender_bank is a valid Bank enum value."""
        assert txn.sender_bank in Bank

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_receiver_bank_is_valid_enum(self, txn: Transaction) -> None:
        """Verify receiver_bank is a valid Bank enum value."""
        assert txn.receiver_bank in Bank

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_sender_account_type_is_valid_enum(self, txn: Transaction) -> None:
        """Verify sender_account_type is a valid AccountType enum value."""
        assert txn.sender_account_type in AccountType

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_receiver_account_type_is_valid_enum(self, txn: Transaction) -> None:
        """Verify receiver_account_type is a valid AccountType enum value."""
        assert txn.receiver_account_type in AccountType

    @given(acct=account_strategy())
    @settings(max_examples=100)
    def test_account_type_is_valid_enum(self, acct: Account) -> None:
        """Verify account_type is a valid AccountType enum value."""
        assert acct.account_type in AccountType

    @given(acct=account_strategy())
    @settings(max_examples=100)
    def test_account_bank_is_valid_enum(self, acct: Account) -> None:
        """Verify account bank is a valid Bank enum value."""
        assert acct.bank in Bank


# ---------------------------------------------------------------------------
# Property 2: Amount Range Constraint
# ---------------------------------------------------------------------------

class TestProperty2AmountRange:
    """Feature: synthetic-data-generator, Property 2: Amount Range Constraint

    For any generated transaction, the amount must be within [₹100, ₹1,00,00,000].
    Validates: Requirements 1.2
    """

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_amount_within_range(self, txn: Transaction) -> None:
        """Verify amount is within ₹100 to ₹1 Crore."""
        assert 100.0 <= txn.amount <= 10_000_000.0

    def test_amount_below_minimum_rejected(self) -> None:
        """Verify amount below ₹100 is rejected by Pydantic."""
        with pytest.raises(ValidationError):
            Transaction(
                transaction_id="TXN-1", timestamp=datetime(2024, 1, 1),
                sender_account="ACC-1", receiver_account="ACC-2",
                amount=99.99, channel=Channel.UPI,
                sender_bank=Bank.SBI, receiver_bank=Bank.HDFC,
                sender_geo=GeoLocation(city="Mumbai", state="Maharashtra",
                                       latitude=19.0, longitude=72.0),
                receiver_geo=GeoLocation(city="Delhi", state="Delhi",
                                         latitude=28.0, longitude=77.0),
                sender_account_type=AccountType.SAVINGS,
                receiver_account_type=AccountType.SAVINGS,
            )

    def test_amount_above_maximum_rejected(self) -> None:
        """Verify amount above ₹1 Crore is rejected by Pydantic."""
        with pytest.raises(ValidationError):
            Transaction(
                transaction_id="TXN-1", timestamp=datetime(2024, 1, 1),
                sender_account="ACC-1", receiver_account="ACC-2",
                amount=10_000_000.01, channel=Channel.UPI,
                sender_bank=Bank.SBI, receiver_bank=Bank.HDFC,
                sender_geo=GeoLocation(city="Mumbai", state="Maharashtra",
                                       latitude=19.0, longitude=72.0),
                receiver_geo=GeoLocation(city="Delhi", state="Delhi",
                                         latitude=28.0, longitude=77.0),
                sender_account_type=AccountType.SAVINGS,
                receiver_account_type=AccountType.SAVINGS,
            )


# ---------------------------------------------------------------------------
# Property 3: Valid Geographic Attributes
# ---------------------------------------------------------------------------

class TestProperty3GeographicAttributes:
    """Feature: synthetic-data-generator, Property 3: Valid Geographic Attributes

    For any generated transaction, geo coordinates must be within Indian bounds.
    Validates: Requirements 1.3
    """

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_sender_geo_latitude_in_indian_bounds(self, txn: Transaction) -> None:
        """Verify sender latitude is within 6°N - 36°N."""
        assert 6.0 <= txn.sender_geo.latitude <= 36.0

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_sender_geo_longitude_in_indian_bounds(self, txn: Transaction) -> None:
        """Verify sender longitude is within 68°E - 98°E."""
        assert 68.0 <= txn.sender_geo.longitude <= 98.0

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_receiver_geo_latitude_in_indian_bounds(self, txn: Transaction) -> None:
        """Verify receiver latitude is within 6°N - 36°N."""
        assert 6.0 <= txn.receiver_geo.latitude <= 36.0

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_receiver_geo_longitude_in_indian_bounds(self, txn: Transaction) -> None:
        """Verify receiver longitude is within 68°E - 98°E."""
        assert 68.0 <= txn.receiver_geo.longitude <= 98.0

    @given(geo=geo_location_strategy())
    @settings(max_examples=100)
    def test_geo_city_is_non_empty(self, geo: GeoLocation) -> None:
        """Verify city name is non-empty."""
        assert len(geo.city.strip()) > 0

    @given(geo=geo_location_strategy())
    @settings(max_examples=100)
    def test_geo_state_is_non_empty(self, geo: GeoLocation) -> None:
        """Verify state name is non-empty."""
        assert len(geo.state.strip()) > 0

    def test_latitude_below_minimum_rejected(self) -> None:
        """Verify latitude below 6°N is rejected."""
        with pytest.raises(ValidationError):
            GeoLocation(city="Test", state="Test", latitude=5.9, longitude=72.0)

    def test_latitude_above_maximum_rejected(self) -> None:
        """Verify latitude above 36°N is rejected."""
        with pytest.raises(ValidationError):
            GeoLocation(city="Test", state="Test", latitude=36.1, longitude=72.0)

    def test_longitude_below_minimum_rejected(self) -> None:
        """Verify longitude below 68°E is rejected."""
        with pytest.raises(ValidationError):
            GeoLocation(city="Test", state="Test", latitude=19.0, longitude=67.9)

    def test_longitude_above_maximum_rejected(self) -> None:
        """Verify longitude above 98°E is rejected."""
        with pytest.raises(ValidationError):
            GeoLocation(city="Test", state="Test", latitude=19.0, longitude=98.1)


# ---------------------------------------------------------------------------
# Property 4: Complete Required Fields
# ---------------------------------------------------------------------------

class TestProperty4CompleteRequiredFields:
    """Feature: synthetic-data-generator, Property 4: Complete Required Fields

    For any generated transaction, all required fields must be present and non-null.
    Validates: Requirements 1.5
    """

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_all_required_fields_present(self, txn: Transaction) -> None:
        """Verify all required fields are present and non-null."""
        assert txn.transaction_id is not None
        assert len(txn.transaction_id.strip()) > 0
        assert txn.timestamp is not None
        assert txn.sender_account is not None
        assert len(txn.sender_account.strip()) > 0
        assert txn.receiver_account is not None
        assert len(txn.receiver_account.strip()) > 0
        assert txn.amount is not None
        assert txn.channel is not None
        assert txn.sender_bank is not None
        assert txn.receiver_bank is not None
        assert txn.sender_geo is not None
        assert txn.receiver_geo is not None

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_geo_fields_complete(self, txn: Transaction) -> None:
        """Verify geo fields have all sub-fields present."""
        for geo in [txn.sender_geo, txn.receiver_geo]:
            assert geo.city is not None
            assert geo.state is not None
            assert geo.latitude is not None
            assert geo.longitude is not None

    @given(txn=transaction_strategy())
    @settings(max_examples=100)
    def test_account_types_present(self, txn: Transaction) -> None:
        """Verify sender and receiver account types are present."""
        assert txn.sender_account_type is not None
        assert txn.receiver_account_type is not None

    def test_missing_required_field_rejected(self) -> None:
        """Verify missing required field raises ValidationError."""
        with pytest.raises(ValidationError):
            Transaction(
                # Missing transaction_id
                timestamp=datetime(2024, 1, 1),
                sender_account="ACC-1", receiver_account="ACC-2",
                amount=5000.0, channel=Channel.UPI,
                sender_bank=Bank.SBI, receiver_bank=Bank.HDFC,
                sender_geo=GeoLocation(city="Mumbai", state="Maharashtra",
                                       latitude=19.0, longitude=72.0),
                receiver_geo=GeoLocation(city="Delhi", state="Delhi",
                                         latitude=28.0, longitude=77.0),
                sender_account_type=AccountType.SAVINGS,
                receiver_account_type=AccountType.SAVINGS,
            )

    def test_empty_transaction_id_rejected(self) -> None:
        """Verify empty transaction_id is rejected."""
        with pytest.raises(ValidationError):
            Transaction(
                transaction_id="   ",
                timestamp=datetime(2024, 1, 1),
                sender_account="ACC-1", receiver_account="ACC-2",
                amount=5000.0, channel=Channel.UPI,
                sender_bank=Bank.SBI, receiver_bank=Bank.HDFC,
                sender_geo=GeoLocation(city="Mumbai", state="Maharashtra",
                                       latitude=19.0, longitude=72.0),
                receiver_geo=GeoLocation(city="Delhi", state="Delhi",
                                         latitude=28.0, longitude=77.0),
                sender_account_type=AccountType.SAVINGS,
                receiver_account_type=AccountType.SAVINGS,
            )


# ---------------------------------------------------------------------------
# Additional: Account model validation tests
# ---------------------------------------------------------------------------

class TestAccountValidation:
    """Additional validation tests for Account model."""

    @given(acct=account_strategy())
    @settings(max_examples=100)
    def test_account_pan_format(self, acct: Account) -> None:
        """Verify PAN format: 5 letters + 4 digits + 1 letter."""
        pan = acct.pan
        assert len(pan) == 10
        assert pan[:5].isalpha()
        assert pan[5:9].isdigit()
        assert pan[9].isalpha()

    @given(acct=account_strategy())
    @settings(max_examples=100)
    def test_account_mobile_format(self, acct: Account) -> None:
        """Verify mobile starts with +91 and has valid digits."""
        mobile = acct.mobile
        digits = mobile.replace("+91", "").replace(" ", "").replace("-", "")
        assert len(digits) == 10
        assert digits[0] in "6789"

    def test_invalid_pan_rejected(self) -> None:
        """Verify invalid PAN format is rejected."""
        with pytest.raises(ValidationError):
            Account(
                account_id="ACC-1", account_type=AccountType.SAVINGS,
                bank=Bank.SBI, account_holder_name="Test User",
                mobile="+919876543210", pan="INVALID",
                address=Address(line1="Test", city="Mumbai",
                               state="Maharashtra", pin_code="400001"),
                pin_code="400001",
            )

    def test_invalid_mobile_rejected(self) -> None:
        """Verify invalid mobile number is rejected."""
        with pytest.raises(ValidationError):
            Account(
                account_id="ACC-1", account_type=AccountType.SAVINGS,
                bank=Bank.SBI, account_holder_name="Test User",
                mobile="12345", pan="ABCDE1234F",
                address=Address(line1="Test", city="Mumbai",
                               state="Maharashtra", pin_code="400001"),
                pin_code="400001",
            )

    def test_invalid_pin_code_rejected(self) -> None:
        """Verify invalid PIN code is rejected."""
        with pytest.raises(ValidationError):
            Address(line1="Test", city="Mumbai",
                    state="Maharashtra", pin_code="012345")


# ---------------------------------------------------------------------------
# Additional: FraudRing model validation tests
# ---------------------------------------------------------------------------

class TestFraudRingValidation:
    """Validation tests for FraudRing model."""

    def test_valid_fraud_ring(self) -> None:
        """Verify valid FraudRing creation."""
        ring = FraudRing(
            fraud_ring_id="FR-001",
            fraud_type=FraudType.LAYERING,
            accounts={"ACC-1", "ACC-2", "ACC-3"},
            transactions=["TXN-1", "TXN-2"],
            total_amount=50000.0,
            created_at=datetime(2024, 1, 15),
        )
        assert ring.fraud_ring_id == "FR-001"
        assert ring.fraud_type == FraudType.LAYERING
        assert len(ring.accounts) == 3
        assert len(ring.transactions) == 2

    def test_all_fraud_types_valid(self) -> None:
        """Verify FraudRing accepts all FraudType values."""
        for fraud_type in FraudType:
            ring = FraudRing(
                fraud_ring_id=f"FR-{fraud_type.value}",
                fraud_type=fraud_type,
                created_at=datetime(2024, 1, 1),
            )
            assert ring.fraud_type == fraud_type

    def test_empty_fraud_ring_id_rejected(self) -> None:
        """Verify empty fraud_ring_id is rejected."""
        with pytest.raises(ValidationError):
            FraudRing(
                fraud_ring_id="   ",
                fraud_type=FraudType.CIRCULAR,
                created_at=datetime(2024, 1, 1),
            )

    def test_negative_total_amount_rejected(self) -> None:
        """Verify negative total_amount is rejected."""
        with pytest.raises(ValidationError):
            FraudRing(
                fraud_ring_id="FR-001",
                fraud_type=FraudType.LAYERING,
                total_amount=-100.0,
                created_at=datetime(2024, 1, 1),
            )

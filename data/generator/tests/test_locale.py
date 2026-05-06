"""
Property tests for Indian locale data and Faker provider.

Tests cover:
- IndianProvider generates valid Indian names
- Mobile numbers follow +91 format with 10 digits starting 6-9
- PAN numbers follow 5 letters + 4 digits + 1 letter format
- Addresses have valid 6-digit PIN codes (first digit 1-9)
- Bank account numbers and IFSC codes follow correct formats
- Cities have valid Indian geographic coordinates

Property 20: Indian Locale Validity
Validates: Requirements 11.1, 11.2, 11.3, 11.4
"""

from __future__ import annotations

import random
import re

import pytest
from faker import Faker
from hypothesis import given, settings
from hypothesis.strategies import integers

from synthetic_generator.locale.faker_provider import IndianProvider
from synthetic_generator.locale.banks import INDIAN_BANKS, BANK_NAMES
from synthetic_generator.locale.cities import INDIAN_CITIES, CITY_DATA
from synthetic_generator.locale.names import (
    INDIAN_FIRST_NAMES,
    INDIAN_LAST_NAMES,
    INDIAN_BUSINESS_PREFIXES,
    INDIAN_BUSINESS_SUFFIXES,
)


@pytest.fixture
def fake() -> Faker:
    """Create a seeded Faker with IndianProvider."""
    f = Faker("en_IN")
    Faker.seed(42)
    f.seed_instance(42)
    random.seed(42)
    f.add_provider(IndianProvider)
    return f


class TestIndianNames:
    """Tests for Indian name generation."""

    def test_first_name_from_list(self, fake: Faker) -> None:
        """Verify generated first names come from the data list."""
        for _ in range(100):
            name = fake.indian_first_name()
            assert name in INDIAN_FIRST_NAMES, f"'{name}' not in INDIAN_FIRST_NAMES"

    def test_last_name_from_list(self, fake: Faker) -> None:
        """Verify generated last names come from the data list."""
        for _ in range(100):
            name = fake.indian_last_name()
            assert name in INDIAN_LAST_NAMES, f"'{name}' not in INDIAN_LAST_NAMES"

    def test_full_name_format(self, fake: Faker) -> None:
        """Verify full name is 'FirstName LastName' format."""
        for _ in range(100):
            name = fake.indian_name()
            parts = name.split(" ")
            assert len(parts) == 2, f"Expected 2 parts, got {len(parts)}: '{name}'"
            assert parts[0] in INDIAN_FIRST_NAMES
            assert parts[1] in INDIAN_LAST_NAMES

    def test_names_are_non_empty(self, fake: Faker) -> None:
        """Verify names are never empty."""
        for _ in range(50):
            assert len(fake.indian_first_name()) > 0
            assert len(fake.indian_last_name()) > 0
            assert len(fake.indian_name()) > 0


class TestIndianMobile:
    """Property 20: Indian mobile number validation."""

    def test_mobile_starts_with_plus91(self, fake: Faker) -> None:
        """Verify mobile number starts with +91."""
        for _ in range(100):
            mobile = fake.indian_mobile()
            assert mobile.startswith("+91"), f"Mobile should start with +91: '{mobile}'"

    def test_mobile_has_correct_length(self, fake: Faker) -> None:
        """Verify mobile number is +91 followed by 10 digits."""
        for _ in range(100):
            mobile = fake.indian_mobile()
            digits = mobile[3:]  # Remove +91
            assert len(digits) == 10, f"Expected 10 digits after +91, got {len(digits)}"

    def test_mobile_first_digit_6_to_9(self, fake: Faker) -> None:
        """Verify mobile first digit (after +91) is 6, 7, 8, or 9."""
        for _ in range(100):
            mobile = fake.indian_mobile()
            first_digit = mobile[3]
            assert first_digit in "6789", f"First digit should be 6-9, got '{first_digit}'"

    def test_mobile_all_digits(self, fake: Faker) -> None:
        """Verify mobile number contains only digits after +91."""
        for _ in range(100):
            mobile = fake.indian_mobile()
            digits = mobile[3:]
            assert digits.isdigit(), f"Expected all digits, got '{digits}'"


class TestIndianPAN:
    """Property 20: Indian PAN card validation."""

    def test_pan_length(self, fake: Faker) -> None:
        """Verify PAN is exactly 10 characters."""
        for _ in range(100):
            pan = fake.indian_pan()
            assert len(pan) == 10, f"PAN should be 10 chars, got {len(pan)}: '{pan}'"

    def test_pan_first_five_letters(self, fake: Faker) -> None:
        """Verify PAN first 5 characters are uppercase letters."""
        for _ in range(100):
            pan = fake.indian_pan()
            assert pan[:5].isalpha() and pan[:5].isupper(), \
                f"PAN first 5 should be uppercase letters: '{pan[:5]}'"

    def test_pan_digits_6_to_9(self, fake: Faker) -> None:
        """Verify PAN characters 6-9 are digits."""
        for _ in range(100):
            pan = fake.indian_pan()
            assert pan[5:9].isdigit(), f"PAN chars 6-9 should be digits: '{pan[5:9]}'"

    def test_pan_last_character_letter(self, fake: Faker) -> None:
        """Verify PAN last character is an uppercase letter."""
        for _ in range(100):
            pan = fake.indian_pan()
            assert pan[9].isalpha() and pan[9].isupper(), \
                f"PAN last char should be uppercase letter: '{pan[9]}'"

    def test_pan_full_format(self, fake: Faker) -> None:
        """Verify PAN matches full format regex."""
        pattern = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
        for _ in range(100):
            pan = fake.indian_pan()
            assert pattern.match(pan), f"PAN doesn't match format: '{pan}'"


class TestIndianAddress:
    """Property 20: Indian address validation."""

    def test_address_has_required_fields(self, fake: Faker) -> None:
        """Verify address contains all required fields."""
        for _ in range(50):
            addr = fake.indian_address()
            assert "line1" in addr
            assert "city" in addr
            assert "state" in addr
            assert "pin_code" in addr

    def test_address_pin_code_format(self, fake: Faker) -> None:
        """Verify PIN code is 6 digits with first digit 1-9."""
        for _ in range(100):
            addr = fake.indian_address()
            pin = addr["pin_code"]
            assert len(pin) == 6, f"PIN should be 6 digits: '{pin}'"
            assert pin.isdigit(), f"PIN should be all digits: '{pin}'"
            assert pin[0] != "0", f"PIN first digit should not be 0: '{pin}'"

    def test_address_city_in_data(self, fake: Faker) -> None:
        """Verify city comes from the cities data."""
        for _ in range(50):
            addr = fake.indian_address()
            assert addr["city"] in CITY_DATA, f"City not found: '{addr['city']}'"

    def test_address_city_state_match(self, fake: Faker) -> None:
        """Verify city-state pairs are consistent with data."""
        for _ in range(50):
            addr = fake.indian_address()
            city = addr["city"]
            state = addr["state"]
            expected_state = CITY_DATA[city]["state"]
            assert state == expected_state, \
                f"City {city} should be in {expected_state}, got {state}"


class TestIndianBankAccount:
    """Tests for bank account number generation."""

    def test_account_number_all_digits(self, fake: Faker) -> None:
        """Verify account number contains only digits."""
        for _ in range(50):
            acct = fake.indian_bank_account_number()
            assert acct.isdigit(), f"Account number should be digits: '{acct}'"

    def test_account_number_correct_length_per_bank(self, fake: Faker) -> None:
        """Verify account number matches bank-specific length."""
        for bank_name in BANK_NAMES:
            acct = fake.indian_bank_account_number(bank=bank_name)
            expected_length = INDIAN_BANKS[bank_name]["account_length"]
            assert len(acct) == expected_length, \
                f"{bank_name} account should be {expected_length} digits, got {len(acct)}"

    def test_ifsc_code_format(self, fake: Faker) -> None:
        """Verify IFSC code is 11 characters: 4 letters + 0 + 6 digits."""
        pattern = re.compile(r"^[A-Z]{4}0[0-9]{6}$")
        for _ in range(50):
            ifsc = fake.indian_ifsc_code()
            assert pattern.match(ifsc), f"IFSC doesn't match format: '{ifsc}'"

    def test_ifsc_bank_specific_prefix(self, fake: Faker) -> None:
        """Verify IFSC uses correct bank prefix."""
        for bank_name in BANK_NAMES:
            ifsc = fake.indian_ifsc_code(bank=bank_name)
            expected_prefix = INDIAN_BANKS[bank_name]["ifsc_prefix"]
            assert ifsc.startswith(expected_prefix), \
                f"{bank_name} IFSC should start with {expected_prefix}: '{ifsc}'"


class TestIndianBusiness:
    """Tests for business name generation."""

    def test_business_name_non_empty(self, fake: Faker) -> None:
        """Verify business name is non-empty."""
        for _ in range(50):
            name = fake.indian_business_name()
            assert len(name.strip()) > 0

    def test_business_name_has_parts(self, fake: Faker) -> None:
        """Verify business name has at least 3 parts."""
        for _ in range(50):
            name = fake.indian_business_name()
            # At minimum: prefix + suffix + entity type
            assert len(name.split()) >= 3


class TestIndianCitiesData:
    """Tests for Indian cities data integrity."""

    def test_all_cities_have_valid_coordinates(self) -> None:
        """Verify all cities have Indian-valid lat/lon."""
        for city in INDIAN_CITIES:
            assert 6.0 <= city["latitude"] <= 36.0, \
                f"{city['name']} latitude {city['latitude']} out of Indian bounds"
            assert 68.0 <= city["longitude"] <= 98.0, \
                f"{city['name']} longitude {city['longitude']} out of Indian bounds"

    def test_all_cities_have_weights(self) -> None:
        """Verify all cities have positive weights."""
        for city in INDIAN_CITIES:
            assert city["weight"] > 0, f"{city['name']} has zero weight"

    def test_weights_approximately_sum_to_one(self) -> None:
        """Verify city weights sum to approximately 1.0."""
        total = sum(c["weight"] for c in INDIAN_CITIES)
        assert 0.95 <= total <= 1.05, f"Weights sum to {total}, expected ~1.0"

    def test_all_cities_have_pin_prefix(self) -> None:
        """Verify all cities have PIN prefixes starting with 1-9."""
        for city in INDIAN_CITIES:
            pin = city["pin_prefix"]
            assert len(pin) >= 2, f"{city['name']} PIN prefix too short: '{pin}'"
            assert pin[0] != "0", f"{city['name']} PIN prefix starts with 0: '{pin}'"


class TestReproducibility:
    """Test that Indian provider is reproducible with seeded random."""

    def test_same_seed_same_names(self) -> None:
        """Verify identical seeds produce identical name sequences."""
        fake1 = Faker("en_IN")
        Faker.seed(42)
        fake1.seed_instance(42)
        random.seed(42)
        fake1.add_provider(IndianProvider)
        names1 = [fake1.indian_name() for _ in range(20)]

        fake2 = Faker("en_IN")
        Faker.seed(42)
        fake2.seed_instance(42)
        random.seed(42)
        fake2.add_provider(IndianProvider)
        names2 = [fake2.indian_name() for _ in range(20)]

        assert names1 == names2

    def test_same_seed_same_mobiles(self) -> None:
        """Verify identical seeds produce identical mobile sequences."""
        fake1 = Faker("en_IN")
        Faker.seed(42)
        fake1.seed_instance(42)
        random.seed(42)
        fake1.add_provider(IndianProvider)
        mobiles1 = [fake1.indian_mobile() for _ in range(20)]

        fake2 = Faker("en_IN")
        Faker.seed(42)
        fake2.seed_instance(42)
        random.seed(42)
        fake2.add_provider(IndianProvider)
        mobiles2 = [fake2.indian_mobile() for _ in range(20)]

        assert mobiles1 == mobiles2

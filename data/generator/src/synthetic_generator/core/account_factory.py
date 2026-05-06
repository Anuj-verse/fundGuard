from __future__ import annotations
import random
from faker import Faker

from synthetic_generator.core.seed_manager import SeedManager
from synthetic_generator.models.account import Account
from synthetic_generator.models.enums import AccountType, Bank
from synthetic_generator.locale.faker_provider import IndianProvider

class AccountFactory:
    """Factory to generate and manage a pool of synthetic Indian bank accounts."""

    def __init__(self, seed_manager: SeedManager) -> None:
        self.seed_manager = seed_manager
        self.faker = Faker('en_IN')
        self.faker.add_provider(IndianProvider)
        self.pool: list[Account] = []
        
    def generate_account_pool(self, size: int) -> None:
        """Generate a pool of synthetic accounts."""
        self.pool.clear()
        faker_seed = self.seed_manager.faker_seed
        self.faker.seed_instance(faker_seed)
        rnd = random.Random(self.seed_manager.python_seed)
        
        for i in range(size):
            try:
                mobile = self.faker.indian_mobile_number()
            except AttributeError:
                mobile = f"9{rnd.randint(100000000, 999999999)}"
                
            try:
                pan = self.faker.indian_pan()
            except AttributeError:
                pan = "ABCDE1234F"
                
            try:
                addr = self.faker.indian_address_obj()
            except AttributeError:
                # Mock if the custom provider doesn't have it
                addr = {"line1": self.faker.street_address(), "city": self.faker.city(), "state": self.faker.state(), "pin_code": str(rnd.randint(110000, 990000))}
                
            account_id = f"ACC-{i:07d}"
            acc_type = rnd.choice(list(AccountType))
            bank = rnd.choice(list(Bank))
            name = self.faker.name()
            pin_code = str(rnd.randint(110000, 990000))
            
            account = Account(
                account_id=account_id,
                account_type=acc_type,
                bank=bank,
                account_holder_name=name,
                mobile=mobile,
                pan=pan,
                address=addr,
                pin_code=pin_code
            )
            self.pool.append(account)
            
    def get_random_account(self, rnd: random.Random = None, exclude: set[str] | None = None) -> Account:
        """Get a random account from the pool."""
        if rnd is None:
            rnd = random
            
        if exclude:
            for _ in range(100):
                a = rnd.choice(self.pool)
                if a.account_id not in exclude:
                    return a
                    
        return rnd.choice(self.pool)

    def get_account(self, account_id: str) -> Account | None:
        """Get an account by ID."""
        for a in self.pool:
            if a.account_id == account_id:
                return a
        return None
        
    def mark_activity(self, account_id, timestamp, counterparty_id: str = None) -> None:
        """Mark activity for an account."""
        acc = account_id if isinstance(account_id, Account) else self.get_account(account_id)
        if acc:
            acc.last_activity = timestamp
            acc.transaction_count += 1
            if counterparty_id:
                acc.counterparties.add(counterparty_id)

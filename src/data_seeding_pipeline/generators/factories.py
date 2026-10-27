"""Deterministic relational data factories with cascade seeding."""

import hashlib
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from faker import Faker

from data_seeding_pipeline.masking.algorithms import (
    generate_valid_cnpj,
    generate_valid_cpf,
    mask_cnpj,
    mask_cpf,
    mask_email,
)
from data_seeding_pipeline.models.schema import (
    Account,
    Tenant,
    TenantStatus,
    Transaction,
    TransactionStatus,
    User,
    UserRole,
    WebhookDelivery,
)
from data_seeding_pipeline.storage.database import DatabaseManager


@dataclass(frozen=True)
class SeedingPlan:
    num_tenants: int = 2
    users_per_tenant: int = 3
    accounts_per_tenant: int = 2
    transactions_per_account: int = 5
    webhooks_per_tenant: int = 2


class DataSeeder:
    def __init__(
        self,
        seed: int = 42,
        run_id: str | None = None,
        mask_pii: bool = False,
        db: DatabaseManager | None = None,
        base_timestamp: str | None = None,
    ):
        self.seed = seed
        self.run_id = run_id or f"run_{uuid.uuid4().hex[:8]}"
        self.mask_pii = mask_pii
        self.db = db
        self.base_timestamp = base_timestamp or datetime.now(timezone.utc).isoformat()

        # Seeded determinism
        self.rng = random.Random(seed)
        self.faker = Faker("pt_BR")
        Faker.seed(seed)

    def generate_tenant(self, index: int) -> Tenant:
        raw_cnpj = generate_valid_cnpj(self.rng)
        cnpj = mask_cnpj(raw_cnpj) if self.mask_pii else raw_cnpj
        tenant_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.seed}-{index}").hex[:8]
        tenant_id = f"tenant_{self.seed}_{index}_{tenant_uuid}"

        return Tenant(
            id=tenant_id,
            name=f"Fintech Enterprise {index + 1} LTDA",
            cnpj=cnpj,
            status=TenantStatus.ACTIVE,
            created_at=self.base_timestamp,
            run_id=self.run_id,
        )

    def generate_user(self, tenant: Tenant, index: int) -> User:
        user_id = f"user_{tenant.id}_{index}"
        raw_cpf = generate_valid_cpf(self.rng)
        cpf = mask_cpf(raw_cpf) if self.mask_pii else raw_cpf

        raw_email = f"user_{index}_{tenant.id[:8]}@example.com"
        email = mask_email(raw_email) if self.mask_pii else raw_email
        role = UserRole.ADMIN if index == 0 else UserRole.OPERATOR

        return User(
            id=user_id,
            tenant_id=tenant.id,
            name=f"Tester {index + 1} {tenant.name.split()[0]}",
            email=email,
            cpf=cpf,
            role=role,
            run_id=self.run_id,
        )

    def generate_account(self, tenant: Tenant, index: int) -> Account:
        account_id = f"acc_{tenant.id}_{index}"
        acc_num = f"{self.rng.randint(10000, 99999)}-{self.rng.randint(0, 9)}"
        currency = "BRL" if index == 0 else "USD"
        initial_balance = round(self.rng.uniform(1000.0, 50000.0), 2)

        return Account(
            id=account_id,
            tenant_id=tenant.id,
            account_number=acc_num,
            currency=currency,
            balance=initial_balance,
            status="active",
            run_id=self.run_id,
        )

    def generate_transaction(self, tenant: Tenant, account: Account, index: int) -> Transaction:
        tx_id = f"tx_{account.id}_{index}"
        # Deterministic idempotency key derived from account + index + seed
        idempotency_raw = f"{account.id}:{index}:{self.seed}"
        idempotency_key = hashlib.sha256(idempotency_raw.encode("utf-8")).hexdigest()[:16]

        amount = round(self.rng.uniform(10.0, 500.0), 2)

        return Transaction(
            id=tx_id,
            tenant_id=tenant.id,
            account_id=account.id,
            amount=amount,
            currency=account.currency,
            idempotency_key=f"idemp_{idempotency_key}",
            status=TransactionStatus.COMPLETED,
            created_at=self.base_timestamp,
            run_id=self.run_id,
        )

    def generate_webhook(self, tenant: Tenant, index: int) -> WebhookDelivery:
        hook_id = f"hook_{tenant.id}_{index}"
        event_types = ["payment.received", "account.created", "transfer.completed"]
        event = event_types[index % len(event_types)]
        raw_hash = f"{tenant.id}:{event}:{index}".encode("utf-8")
        payload_hash = hashlib.sha256(raw_hash).hexdigest()[:12]

        return WebhookDelivery(
            id=hook_id,
            tenant_id=tenant.id,
            event_type=event,
            target_url=f"https://api.partner.com/webhook/{tenant.id[:8]}",
            payload_hash=payload_hash,
            status_code=200,
            delivered_at=self.base_timestamp,
            run_id=self.run_id,
        )

    def seed_all(self, plan: SeedingPlan) -> dict[str, list]:
        """Execute full relational cascade seeding and insert into database if connected."""
        results: dict[str, list] = {
            "tenants": [],
            "users": [],
            "accounts": [],
            "transactions": [],
            "webhook_deliveries": [],
        }

        for t_idx in range(plan.num_tenants):
            tenant = self.generate_tenant(t_idx)
            results["tenants"].append(tenant)
            if self.db:
                self.db.insert_tenant(tenant)

            for u_idx in range(plan.users_per_tenant):
                user = self.generate_user(tenant, u_idx)
                results["users"].append(user)
                if self.db:
                    self.db.insert_user(user)

            for a_idx in range(plan.accounts_per_tenant):
                account = self.generate_account(tenant, a_idx)
                results["accounts"].append(account)
                if self.db:
                    self.db.insert_account(account)

                for tx_idx in range(plan.transactions_per_account):
                    tx = self.generate_transaction(tenant, account, tx_idx)
                    results["transactions"].append(tx)
                    if self.db:
                        self.db.insert_transaction(tx)

            for w_idx in range(plan.webhooks_per_tenant):
                hook = self.generate_webhook(tenant, w_idx)
                results["webhook_deliveries"].append(hook)
                if self.db:
                    self.db.insert_webhook(hook)

        return results

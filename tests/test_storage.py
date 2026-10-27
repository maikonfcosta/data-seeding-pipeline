"""Tests for SQLite DatabaseManager: FK enforcement, idempotency, and cascading teardown."""

import sqlite3

import pytest

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


@pytest.fixture
def db() -> DatabaseManager:
    manager = DatabaseManager(":memory:")
    yield manager
    manager.close()


def test_foreign_key_enforcement(db: DatabaseManager) -> None:
    # Attempt inserting user without tenant should fail with IntegrityError
    orphan_user = User(
        id="usr_orphan",
        tenant_id="tenant_nonexistent",
        name="Orphan Tester",
        email="orphan@example.com",
        cpf="12345678909",
        role=UserRole.OPERATOR,
        run_id="run_test",
    )
    with pytest.raises(sqlite3.IntegrityError):
        db.insert_user(orphan_user)


def test_cascade_teardown(db: DatabaseManager) -> None:
    run_id = "run_abc123"

    tenant = Tenant(
        id="tenant_1",
        name="Fintech Alpha LTDA",
        cnpj="12345678000195",
        status=TenantStatus.ACTIVE,
        created_at="2026-10-27T10:00:00Z",
        run_id=run_id,
    )
    assert db.insert_tenant(tenant) is True

    user = User(
        id="usr_1",
        tenant_id=tenant.id,
        name="User Alpha",
        email="alpha@example.com",
        cpf="12345678909",
        role=UserRole.ADMIN,
        run_id=run_id,
    )
    assert db.insert_user(user) is True

    account = Account(
        id="acc_1",
        tenant_id=tenant.id,
        account_number="12345-6",
        currency="BRL",
        balance=5000.0,
        status="active",
        run_id=run_id,
    )
    assert db.insert_account(account) is True

    tx = Transaction(
        id="tx_1",
        tenant_id=tenant.id,
        account_id=account.id,
        amount=150.0,
        currency="BRL",
        idempotency_key="idemp_123",
        status=TransactionStatus.COMPLETED,
        created_at="2026-10-27T10:05:00Z",
        run_id=run_id,
    )
    assert db.insert_transaction(tx) is True

    hook = WebhookDelivery(
        id="hook_1",
        tenant_id=tenant.id,
        event_type="payment.received",
        target_url="https://api.test.com/hook",
        payload_hash="hash123",
        status_code=200,
        delivered_at="2026-10-27T10:06:00Z",
        run_id=run_id,
    )
    assert db.insert_webhook(hook) is True

    counts_before = db.count_records()
    assert counts_before["tenants"] == 1
    assert counts_before["users"] == 1
    assert counts_before["accounts"] == 1
    assert counts_before["transactions"] == 1
    assert counts_before["webhook_deliveries"] == 1

    # Teardown the run
    deleted = db.teardown_run(run_id)
    assert deleted == 1

    # Verify cascade cleaned up all related tables
    counts_after = db.count_records()
    assert all(count == 0 for count in counts_after.values())


def test_idempotent_inserts(db: DatabaseManager) -> None:
    run_id = "run_idemp"
    tenant = Tenant(
        id="tenant_idemp",
        name="Idempotent Fintech",
        cnpj="12345678000195",
        status=TenantStatus.ACTIVE,
        created_at="2026-10-27T10:00:00Z",
        run_id=run_id,
    )
    # First insert succeeds
    assert db.insert_tenant(tenant) is True
    # Second duplicate insert ignored safely without error
    assert db.insert_tenant(tenant) is False

    account = Account(
        id="acc_idemp",
        tenant_id=tenant.id,
        account_number="99999-9",
        currency="BRL",
        balance=100.0,
        status="active",
        run_id=run_id,
    )
    assert db.insert_account(account) is True

    tx1 = Transaction(
        id="tx_idemp_1",
        tenant_id=tenant.id,
        account_id=account.id,
        amount=10.0,
        currency="BRL",
        idempotency_key="same_key",
        status=TransactionStatus.COMPLETED,
        created_at="2026-10-27T10:00:00Z",
        run_id=run_id,
    )
    tx2 = Transaction(
        id="tx_idemp_2",
        tenant_id=tenant.id,
        account_id=account.id,
        amount=20.0,
        currency="BRL",
        idempotency_key="same_key",  # Duplicate key for same tenant
        status=TransactionStatus.COMPLETED,
        created_at="2026-10-27T10:01:00Z",
        run_id=run_id,
    )
    assert db.insert_transaction(tx1) is True
    assert db.insert_transaction(tx2) is False  # Ignored due to unique constraint

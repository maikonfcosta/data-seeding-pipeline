"""Relational SQLite database manager with enforced foreign keys and idempotency."""

import sqlite3
from pathlib import Path

from data_seeding_pipeline.models.schema import Account, Tenant, Transaction, User, WebhookDelivery


class DatabaseManager:
    def __init__(self, db_path: str | Path = ":memory:"):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._enable_foreign_keys()
        self._create_tables()

    def _enable_foreign_keys(self) -> None:
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def _create_tables(self) -> None:
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tenants (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    cnpj TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    run_id TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    cpf TEXT NOT NULL,
                    role TEXT NOT NULL,
                    run_id TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    account_number TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    balance REAL NOT NULL,
                    status TEXT NOT NULL,
                    run_id TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    CONSTRAINT uq_tenant_idempotency UNIQUE(tenant_id, idempotency_key)
                );

                CREATE TABLE IF NOT EXISTS webhook_deliveries (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    event_type TEXT NOT NULL,
                    target_url TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    delivered_at TEXT NOT NULL,
                    run_id TEXT NOT NULL
                );
                """
            )

    def insert_tenant(self, tenant: Tenant) -> bool:
        """Insert tenant idempotently. Returns True if inserted, False if already exists."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO tenants (id, name, cnpj, status, created_at, run_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                tenant.id,
                tenant.name,
                tenant.cnpj,
                tenant.status.value,
                tenant.created_at,
                tenant.run_id,
            ),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def insert_user(self, user: User) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (id, tenant_id, name, email, cpf, role, run_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user.id,
                user.tenant_id,
                user.name,
                user.email,
                user.cpf,
                user.role.value,
                user.run_id,
            ),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def insert_account(self, account: Account) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO accounts (
                id, tenant_id, account_number, currency, balance, status, run_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account.id,
                account.tenant_id,
                account.account_number,
                account.currency,
                account.balance,
                account.status,
                account.run_id,
            ),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def insert_transaction(self, tx: Transaction) -> bool:
        """Insert financial transaction enforcing idempotency key constraint per tenant."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO transactions (
                id, tenant_id, account_id, amount, currency,
                idempotency_key, status, created_at, run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tx.id,
                tx.tenant_id,
                tx.account_id,
                tx.amount,
                tx.currency,
                tx.idempotency_key,
                tx.status.value,
                tx.created_at,
                tx.run_id,
            ),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def insert_webhook(self, hook: WebhookDelivery) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO webhook_deliveries (
                id, tenant_id, event_type, target_url,
                payload_hash, status_code, delivered_at, run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hook.id,
                hook.tenant_id,
                hook.event_type,
                hook.target_url,
                hook.payload_hash,
                hook.status_code,
                hook.delivered_at,
                hook.run_id,
            ),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def teardown_run(self, run_id: str) -> int:
        """Delete all entities associated with a specific test run_id using cascade."""
        cursor = self.conn.cursor()
        # Deleting tenants cascades down to users, accounts, transactions and webhooks
        cursor.execute("DELETE FROM tenants WHERE run_id = ?", (run_id,))
        deleted_count = cursor.rowcount
        self.conn.commit()
        return deleted_count

    def count_records(self) -> dict[str, int]:
        tables = ["tenants", "users", "accounts", "transactions", "webhook_deliveries"]
        counts = {}
        for table in tables:
            cur = self.conn.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
        return counts

    def close(self) -> None:
        self.conn.close()

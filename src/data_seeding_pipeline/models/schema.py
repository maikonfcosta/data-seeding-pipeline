"""Pydantic data schemas representing the multi-tenant financial domain."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class TransactionStatus(str, Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"


class Tenant(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    cnpj: str
    status: TenantStatus = TenantStatus.ACTIVE
    created_at: str
    run_id: str = Field(description="Unique test execution ID for isolated cleanup")


class User(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    tenant_id: str
    name: str
    email: str
    cpf: str
    role: UserRole = UserRole.OPERATOR
    run_id: str


class Account(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    tenant_id: str
    account_number: str
    currency: str = "BRL"
    balance: float = 0.0
    status: str = "active"
    run_id: str


class Transaction(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    tenant_id: str
    account_id: str
    amount: float
    currency: str = "BRL"
    idempotency_key: str
    status: TransactionStatus = TransactionStatus.COMPLETED
    created_at: str
    run_id: str


class WebhookDelivery(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    tenant_id: str
    event_type: str
    target_url: str
    payload_hash: str
    status_code: int = 200
    delivered_at: str
    run_id: str

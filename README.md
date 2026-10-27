# data-seeding-pipeline 🧬

[![CI Pipeline](https://github.com/maikonfcosta/data-seeding-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/maikonfcosta/data-seeding-pipeline/actions/workflows/ci.yml)
[![Python 3.12 | 3.13](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Coverage: 96%](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)]()

> **Deterministic, relational, PII-sanitized test data management (TDM) pipeline for financial APIs.**

---

## 📌 Problem Statement / O Problema de Engenharia

In integration and E2E testing for fintech and FX systems, test flakiness and environment pollution frequently stem from **shared mutable test data** and **state collisions**:
1. **Flaky assertions caused by state pollution:** Tests executing concurrently share bank accounts, mutating balances and generating false negative pipeline failures.
2. **PII and LGPD/GDPR exposure:** Dumping production databases into staging/QA environments leaks sensitive customer credentials, tax IDs (CPF/CNPJ), and financial records.
3. **Broken referential integrity:** Naive random mocks insert transactions referencing nonexistent accounts or tenants, failing strict database foreign keys.
4. **Hard-to-reproduce test failures:** Random generation without fixed seeds makes re-running a failed integration scenario nearly impossible to reproduce deterministically.

---

## 💡 Solution / A Solução

`data-seeding-pipeline` implements an isolated, self-contained Test Data Management (TDM) engine:
- **Seed-driven Determinism:** Uses `random.Random(seed)` and deterministic UUID5 generators so passing `--seed 42` produces identical, repeatable relational datasets across any machine or CI container.
- **Strict Referential Integrity Cascade:** Enforces multi-tenant hierarchies (`Tenant` ➔ `User` + `Account` ➔ `Transaction` + `WebhookDelivery`) with `PRAGMA foreign_keys = ON` in SQLite.
- **Cryptographic PII Algorithms:** Pure Modulus-11 checksum algorithms generate mathematically valid Brazilian CPFs and CNPJs that bypass frontend/backend validators without impersonating real people or companies, with visual masking toggles (`123.***.***-45`).
- **Idempotency & Zero-residue Teardown:** Idempotency keys (`idemp_<sha256>`) prevent duplicate entries on retry, and cascading run identifiers (`run_id`) allow instantaneous purging of test data post-run without affecting baseline state.

---

## 🏛️ Architecture & Data Cascade / Arquitetura

```
[SeedingPlan] ── (Seed: 42, Tenants: 2, Accounts: 2, Txs: 5)
      │
      ▼
┌──────────────┐
│    Tenant    │  (CNPJ validado Mod-11, status ativo)
└──────┬───────┘
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
┌──────────────┐                  ┌──────────────┐
│     User     │ (CPF Mod-11)     │   Account    │ (BRL / USD balance)
└──────────────┘                  └──────┬───────┘
       │                                 │
       ▼                                 ▼
┌──────────────┐                  ┌──────────────┐
│   Webhook    │ (Event hash)     │ Transaction  │ (UNIQUE tenant + idempotency_key)
└──────────────┘                  └──────────────┘
```

---

## 🚀 Quickstart / Como Executar

### 1. Requirements & Installation

Using `uv` (recommended):
```bash
git clone https://github.com/maikonfcosta/data-seeding-pipeline.git
cd data-seeding-pipeline
uv sync --all-groups
```

### 2. Generate Deterministic Test Data (CLI)

```bash
# Seed isolated database with fixed seed 42 and export JSON artifacts
uv run seed-pipeline seed --seed 42 --tenants 3 --export-json seeded_data/sample.json
```

Output:
```text
Starting seed pipeline (seed=42, mask_pii=False, run_id=run_b74e84d1)...
  Seeding Pipeline Execution Summary   
┌────────────────────┬────────────────┐
│ Entity Table       │ Inserted Count │
├────────────────────┼────────────────┤
│ tenants            │              3 │
│ users              │              9 │
│ accounts           │              6 │
│ transactions       │             30 │
│ webhook_deliveries │              6 │
└────────────────────┴────────────────┘
SUCCESS: Seeded database at seeded_data/test_db.sqlite
SUCCESS: Exported JSON to seeded_data/sample.json
```

### 3. Verify Database Integrity

```bash
uv run seed-pipeline verify --db-path seeded_data/test_db.sqlite
```

### 4. Teardown Test Run

```bash
uv run seed-pipeline teardown run_b74e84d1 --db-path seeded_data/test_db.sqlite
```

---

## 🧪 Testing & Quality Gates

Run linter and test suite with coverage report:

```bash
uv run ruff check .
uv run pytest --cov=src/data_seeding_pipeline --cov-report=term-missing
```

Current quality benchmarks:
- **Unit & Integration Coverage:** **96%** (target: $\ge 85\%$)
- **Execution Speed:** Sub-second in-memory SQLite execution
- **Ruff Linting:** Zero warnings / 100% PEP 8 compliant

---

## ⚖️ Engineering Trade-offs / Trade-offs

1. **Embedded SQLite vs Real Database Service:**
   - *Choice:* Embedded SQLite with enforced foreign keys (`PRAGMA foreign_keys = ON`).
   - *Why:* Zero external infrastructure overhead. Sub-second boot times in CI without requiring Docker or network daemon spin-ups, while testing relational constraints faithfully.
2. **Deterministic Pseudorandomness vs Pure Static Fixtures:**
   - *Choice:* Seeded RNG (`random.Random(seed)`) paired with UUID5.
   - *Why:* Static JSON fixtures decay rapidly as schemas evolve and don't allow scaling data volumes. Seeded generation allows generating 10 or 10,000 records on demand while keeping tests 100% reproducible.
3. **Synthetic Checksum Generation vs Production Data Masking:**
   - *Choice:* Algorithmic generation from scratch rather than scrubbing production dumps.
   - *Why:* Eliminates data breach liabilities and LGPD/GDPR non-compliance at the source. Synthetic data never contains real identities.

---

## 👤 Author

**Maikon Costa** — QA Tech Lead / Senior QA Automation Engineer  
Focusing on Quality Engineering, Performance & Resilient Test Architecture.
- LinkedIn: [linkedin.com/in/maikoncosta](https://www.linkedin.com/in/maikoncosta/)
- GitHub: [@maikonfcosta](https://github.com/maikonfcosta)

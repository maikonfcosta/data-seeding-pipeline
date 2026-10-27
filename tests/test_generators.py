"""Tests for deterministic generation, seeding plans, and PII masking."""

from data_seeding_pipeline.generators.factories import DataSeeder, SeedingPlan
from data_seeding_pipeline.masking.algorithms import is_valid_cnpj, is_valid_cpf


def test_determinism_across_instances() -> None:
    fixed_ts = "2026-10-27T10:00:00+00:00"
    seeder_a = DataSeeder(seed=999, run_id="fixed_run", base_timestamp=fixed_ts)
    seeder_b = DataSeeder(seed=999, run_id="fixed_run", base_timestamp=fixed_ts)

    plan = SeedingPlan(
        num_tenants=2,
        users_per_tenant=2,
        accounts_per_tenant=1,
        transactions_per_account=2,
        webhooks_per_tenant=1,
    )

    results_a = seeder_a.seed_all(plan)
    results_b = seeder_b.seed_all(plan)

    # Identical seed and run_id must produce byte-for-byte identical datasets
    assert [t.model_dump() for t in results_a["tenants"]] == [
        t.model_dump() for t in results_b["tenants"]
    ]
    assert [u.model_dump() for u in results_a["users"]] == [
        u.model_dump() for u in results_b["users"]
    ]
    assert [a.model_dump() for a in results_a["accounts"]] == [
        a.model_dump() for a in results_b["accounts"]
    ]
    assert [tx.model_dump() for tx in results_a["transactions"]] == [
        tx.model_dump() for tx in results_b["transactions"]
    ]
    assert [w.model_dump() for w in results_a["webhook_deliveries"]] == [
        w.model_dump() for w in results_b["webhook_deliveries"]
    ]


def test_pii_masking_flag() -> None:
    seeder_raw = DataSeeder(seed=123, mask_pii=False)
    seeder_masked = DataSeeder(seed=123, mask_pii=True)

    t_raw = seeder_raw.generate_tenant(0)
    t_masked = seeder_masked.generate_tenant(0)

    # Raw must be valid CNPJ and have no asterisks
    assert "*" not in t_raw.cnpj
    assert is_valid_cnpj(t_raw.cnpj) is True

    # Masked must have asterisks
    assert "*" in t_masked.cnpj

    u_raw = seeder_raw.generate_user(t_raw, 0)
    u_masked = seeder_masked.generate_user(t_masked, 0)

    assert "*" not in u_raw.cpf
    assert is_valid_cpf(u_raw.cpf) is True
    assert "*" in u_masked.cpf
    assert "*" in u_masked.email

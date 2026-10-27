"""Tests for Typer CLI commands: version, seed, verify, and teardown."""

import json
from pathlib import Path

from typer.testing import CliRunner

from data_seeding_pipeline.cli import app

runner = CliRunner()


def test_cli_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "seed-pipeline version:" in result.stdout


def test_cli_full_lifecycle(tmp_path: Path) -> None:
    db_file = tmp_path / "test_lifecycle.sqlite"
    json_export = tmp_path / "lifecycle_export.json"

    # 1. Seed database
    res_seed = runner.invoke(
        app,
        [
            "seed",
            "--db-path",
            str(db_file),
            "--seed",
            "77",
            "--tenants",
            "2",
            "--export-json",
            str(json_export),
        ],
    )
    assert res_seed.exit_code == 0
    assert "SUCCESS: Seeded database" in res_seed.stdout
    assert db_file.exists()
    assert json_export.exists()

    # Verify JSON content
    data = json.loads(json_export.read_text(encoding="utf-8"))
    assert len(data["tenants"]) == 2
    assert len(data["users"]) == 6
    run_id = data["tenants"][0]["run_id"]

    # 2. Verify integrity
    res_verify = runner.invoke(app, ["verify", "--db-path", str(db_file)])
    assert res_verify.exit_code == 0
    assert "ALL INTEGRITY CHECKS PASSED" in res_verify.stdout

    # 3. Teardown by run_id
    res_teardown = runner.invoke(app, ["teardown", run_id, "--db-path", str(db_file)])
    assert res_teardown.exit_code == 0
    assert "Teardown complete: expunged 2 root tenant(s)" in res_teardown.stdout

    # 4. Verify database is now empty
    res_verify_post = runner.invoke(app, ["verify", "--db-path", str(db_file)])
    assert res_verify_post.exit_code == 0
    assert "tenants: 0 records verified" in res_verify_post.stdout

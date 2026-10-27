"""Command Line Interface for the data-seeding-pipeline."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from data_seeding_pipeline import __version__
from data_seeding_pipeline.generators.factories import DataSeeder, SeedingPlan
from data_seeding_pipeline.masking.algorithms import is_valid_cnpj, is_valid_cpf
from data_seeding_pipeline.storage.database import DatabaseManager

app = typer.Typer(
    name="seed-pipeline",
    help="Deterministic, relational, PII-sanitized test data seeding pipeline.",
)
console = Console()


@app.callback()
def main_callback() -> None:
    """Deterministic, relational, PII-sanitized test data seeding pipeline."""
    pass


@app.command()
def version() -> None:
    """Show the CLI version."""
    console.print(f"[bold green]seed-pipeline[/bold green] version: {__version__}")


@app.command()
def seed(
    db_path: str = typer.Option("seeded_data/test_db.sqlite", help="Path to SQLite database"),
    seed: int = typer.Option(42, help="Deterministic random seed"),
    tenants: int = typer.Option(2, help="Number of tenants to generate"),
    users_per_tenant: int = typer.Option(3, help="Users per tenant"),
    accounts_per_tenant: int = typer.Option(2, help="Accounts per tenant"),
    transactions_per_account: int = typer.Option(5, help="Transactions per account"),
    webhooks_per_tenant: int = typer.Option(2, help="Webhooks per tenant"),
    mask_pii: bool = typer.Option(False, help="Enable visual PII masking for CPFs/CNPJs"),
    export_json: str | None = typer.Option(
        None, help="Optional path to export seeded data as JSON"
    ),
) -> None:
    """Generate and insert deterministic relational test data into SQLite."""
    out_db = Path(db_path)
    out_db.parent.mkdir(parents=True, exist_ok=True)

    db = DatabaseManager(out_db)
    seeder = DataSeeder(seed=seed, mask_pii=mask_pii, db=db)
    plan = SeedingPlan(
        num_tenants=tenants,
        users_per_tenant=users_per_tenant,
        accounts_per_tenant=accounts_per_tenant,
        transactions_per_account=transactions_per_account,
        webhooks_per_tenant=webhooks_per_tenant,
    )

    console.print(
        f"[bold cyan]Starting seed pipeline[/bold cyan] "
        f"(seed={seed}, mask_pii={mask_pii}, run_id={seeder.run_id})..."
    )
    results = seeder.seed_all(plan)

    counts = db.count_records()
    table = Table(title="Seeding Pipeline Execution Summary")
    table.add_column("Entity Table", style="cyan")
    table.add_column("Inserted Count", style="green", justify="right")

    for entity, count in counts.items():
        table.add_row(entity, str(count))

    console.print(table)
    console.print(
        f"[bold green]SUCCESS:[/bold green] Seeded database at [underline]{out_db}[/underline]"
    )
    db.close()

    if export_json:
        export_path = Path(export_json)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        serializable = {
            k: [item.model_dump() for item in v]
            for k, v in results.items()
        }
        export_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
        console.print(
            f"[bold green]SUCCESS:[/bold green] Exported JSON to [underline]{export_path}[/]"
        )


@app.command()
def teardown(
    run_id: str = typer.Argument(..., help="Run ID of the test execution to expunge"),
    db_path: str = typer.Option("seeded_data/test_db.sqlite", help="Path to SQLite database"),
) -> None:
    """Teardown and purge all entities associated with a specific test run ID."""
    out_db = Path(db_path)
    if not out_db.exists():
        console.print(f"[red]Database not found at {out_db}[/red]")
        raise typer.Exit(code=1)

    db = DatabaseManager(out_db)
    deleted = db.teardown_run(run_id)
    db.close()

    console.print(
        f"[bold green]Teardown complete:[/bold green] expunged {deleted} root tenant(s) "
        f"and cascading records for run_id='{run_id}'."
    )


@app.command()
def verify(
    db_path: str = typer.Option("seeded_data/test_db.sqlite", help="Path to SQLite database"),
) -> None:
    """Verify integrity of seeded database (foreign keys and check constraints)."""
    out_db = Path(db_path)
    if not out_db.exists():
        console.print(f"[red]Database not found at {out_db}[/red]")
        raise typer.Exit(code=1)

    db = DatabaseManager(out_db)
    cursor = db.conn.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()

    if fk_violations:
        console.print(
            f"[bold red]INTEGRITY ERROR:[/bold red] Found {len(fk_violations)} FK violations!"
        )
        for row in fk_violations:
            console.print(f"Table: {row[0]}, rowid: {row[1]}, parent: {row[2]}, fkid: {row[3]}")
        raise typer.Exit(code=1)

    # Check validity of CNPJs/CPFs
    tenants_cur = db.conn.execute("SELECT cnpj FROM tenants")
    invalid_cnpjs = [row[0] for row in tenants_cur if not ("*" in row[0] or is_valid_cnpj(row[0]))]

    users_cur = db.conn.execute("SELECT cpf FROM users")
    invalid_cpfs = [row[0] for row in users_cur if not ("*" in row[0] or is_valid_cpf(row[0]))]

    if invalid_cnpjs or invalid_cpfs:
        console.print(
            f"[bold red]VALIDATION ERROR:[/bold red] Invalid documents detected "
            f"(CNPJs: {len(invalid_cnpjs)}, CPFs: {len(invalid_cpfs)})"
        )
        raise typer.Exit(code=1)

    counts = db.count_records()
    console.print(
        "[bold green]ALL INTEGRITY CHECKS PASSED:[/bold green] "
        "Zero FK violations and valid synthetic document checksums."
    )
    for k, v in counts.items():
        console.print(f" - {k}: {v} records verified")
    db.close()


if __name__ == "__main__":
    app()

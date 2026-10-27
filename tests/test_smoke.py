"""Smoke tests for pipeline bootstrap and CLI initialization."""

from typer.testing import CliRunner

from data_seeding_pipeline import __version__
from data_seeding_pipeline.cli import app

runner = CliRunner()


def test_package_version():
    assert __version__ == "0.1.0"


def test_cli_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output

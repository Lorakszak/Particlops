"""Tests for CLI -- flag parsing and validation."""

from click.testing import CliRunner

from particle_gen.cli import cli


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "generate" in result.output
    assert "preview" in result.output
    assert "list-presets" in result.output


def test_list_presets() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["list-presets"])
    assert result.exit_code == 0
    assert "gentle_snow" in result.output
    assert "rising_sparks" in result.output


def test_generate_validates_crossfade() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [
        "generate", "--duration", "10", "--crossfade", "8",
        "--output", "/tmp/test.mp4",
    ])
    assert result.exit_code != 0


def test_generate_validates_resolution_format() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["generate", "--resolution", "invalid"])
    assert result.exit_code != 0

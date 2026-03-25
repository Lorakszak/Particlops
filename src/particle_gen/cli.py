"""Click CLI for particle-gen -- generate, preview, list-presets."""

import logging
import re
import sys
from pathlib import Path

import click

from particle_gen.core.export import ExportPipeline, validate_export_params
from particle_gen.presets.manager import list_builtin_presets, load_builtin_preset
from particle_gen.presets.schema import ParticlePreset, load_preset, save_preset

logger = logging.getLogger(__name__)


def _parse_resolution(value: str) -> tuple[int, int]:
    """Parse a WxH resolution string."""
    match = re.match(r"^(\d+)x(\d+)$", value)
    if not match:
        raise click.BadParameter(f"Invalid resolution format: '{value}'. Use WxH (e.g. 1920x1080)")
    return int(match.group(1)), int(match.group(2))


def _build_preset(
    preset_name: str | None,
    preset_path: str | None,
    overrides: dict,
) -> ParticlePreset:
    """Build a preset from a base + CLI overrides."""
    if preset_path:
        base = load_preset(Path(preset_path))
    elif preset_name:
        base = load_builtin_preset(preset_name)
    else:
        base = ParticlePreset(name="default", description="Default preset")

    for key, value in overrides.items():
        if value is not None and hasattr(base, key):
            setattr(base, key, value)

    # Re-validate after overrides
    base.__post_init__()
    return base


# Shared particle parameter options
_particle_options = [
    click.option("--particles", "max_particles", type=int, default=None),
    click.option("--size", "particle_size", type=float, default=None),
    click.option("--spawn-rate", type=float, default=None),
    click.option("--lifetime", type=float, default=None),
    click.option("--spread", type=float, default=None),
    click.option("--spawn-mode", type=click.Choice(
        ["point", "line", "circle", "edges", "random"]), default=None),
    click.option("--spawn-x", type=float, default=None),
    click.option("--spawn-y", type=float, default=None),
    click.option("--spawn-radius", type=float, default=None),
    click.option("--gravity-x", type=float, default=None),
    click.option("--gravity-y", type=float, default=None),
    click.option("--speed-min", type=float, default=None),
    click.option("--speed-max", type=float, default=None),
    click.option("--drag", type=float, default=None),
    click.option("--turbulence", type=float, default=None),
    click.option("--radial-force", type=float, default=None),
    click.option("--vortex", type=float, default=None),
    click.option("--size-min", type=float, default=None,
                 help="Min size multiplier (default 0.5)"),
    click.option("--size-max", type=float, default=None,
                 help="Max size multiplier (default 1.5)"),
    click.option("--lifetime-min", type=float, default=None,
                 help="Min lifetime multiplier (default 0.5)"),
    click.option("--lifetime-max", type=float, default=None,
                 help="Max lifetime multiplier (default 1.5)"),
    click.option("--particle-shapes", type=str, default=None,
                 help="Comma-separated shapes (circle,square,triangle,diamond,star,ring)"),
    click.option("--size-over-life", type=click.Choice(
        ["constant", "grow", "shrink", "pulse"]), default=None),
    click.option("--fade-curve", type=click.Choice(
        ["linear", "ease_out", "flash"]), default=None),
    click.option("--color-over-life", is_flag=True, default=None),
    click.option("--colors", type=str, default=None,
                 help="Comma-separated hex colors"),
]


def _add_particle_options(func):  # type: ignore[no-untyped-def]
    for option in reversed(_particle_options):
        func = option(func)
    return func


def _collect_overrides(**kwargs: object) -> dict:
    """Collect non-None particle parameter overrides from CLI kwargs."""
    param_keys = {
        "max_particles", "particle_size", "spawn_rate", "lifetime", "spread",
        "spawn_mode", "spawn_x", "spawn_y", "spawn_radius",
        "gravity_x", "gravity_y", "speed_min", "speed_max",
        "drag", "turbulence", "radial_force", "vortex",
        "size_min", "size_max", "lifetime_min", "lifetime_max", "particle_shapes",
        "size_over_life", "fade_curve", "color_over_life", "colors",
    }
    overrides = {}
    for key in param_keys:
        val = kwargs.get(key)
        if val is not None:
            if key == "colors" and isinstance(val, str):
                overrides[key] = [c.strip() for c in val.split(",")]
            elif key == "particle_shapes" and isinstance(val, str):
                overrides[key] = [s.strip() for s in val.split(",")]
            else:
                overrides[key] = val
    return overrides


@click.group()
def cli() -> None:
    """particle-gen: Seamlessly looped particle video generator."""


@cli.command()
@click.option("--duration", type=float, default=30.0, help="Video length in seconds")
@click.option("--crossfade", type=float, default=10.0, help="Loop overlap in seconds")
@click.option("--output", type=click.Path(), default="particles.mp4", help="Output file path")
@click.option("--preset", "preset_name", type=str, default=None, help="Built-in preset name")
@click.option("--preset-file", type=click.Path(exists=True), default=None,
              help="Path to preset JSON file")
@click.option("--seed", type=int, default=None, help="Random seed for reproducibility")
@click.option("--preroll", type=float, default=None, help="Pre-roll seconds")
@click.option("--resolution", type=str, default="1920x1080", help="Output resolution (WxH)")
@click.option("--fps", type=int, default=60, help="Frames per second")
@click.option("--crf", type=int, default=18, help="H.264 CRF quality (lower = better)")
@click.option("--codec", type=str, default="libx264", help="Video codec")
@click.option("--save-preset", "save_preset_path", type=click.Path(), default=None,
              help="Save current settings to JSON")
@_add_particle_options
def generate(
    duration: float,
    crossfade: float,
    output: str,
    preset_name: str | None,
    preset_file: str | None,
    seed: int | None,
    preroll: float | None,
    resolution: str,
    fps: int,
    crf: int,
    codec: str,
    save_preset_path: str | None,
    **kwargs: object,
) -> None:
    """Generate a seamlessly looped particle video."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        res = _parse_resolution(resolution)
    except click.BadParameter as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    try:
        validate_export_params(duration, crossfade)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    overrides = _collect_overrides(**kwargs)

    try:
        preset = _build_preset(preset_name, preset_file, overrides)
    except (ValueError, FileNotFoundError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if save_preset_path:
        save_preset(preset, Path(save_preset_path))
        click.echo(f"Preset saved to {save_preset_path}")

    def progress(p: float) -> None:
        bar_len = 40
        filled = int(bar_len * p)
        bar = "=" * filled + "-" * (bar_len - filled)
        click.echo(f"\rRendering [{bar}] {p * 100:.1f}%", nl=False)

    pipeline = ExportPipeline(
        preset=preset,
        duration=duration,
        crossfade=crossfade,
        resolution=res,
        fps=fps,
        crf=crf,
        codec=codec,
        output=Path(output),
        seed=seed,
        preroll=preroll,
        progress_callback=progress,
    )

    try:
        result = pipeline.run()
        click.echo()
        click.echo(f"Done: {result}")
    except Exception as e:
        click.echo(f"\nError during export: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--preset", "preset_name", type=str, default=None, help="Built-in preset name")
@click.option("--preset-file", type=click.Path(exists=True), default=None,
              help="Path to preset JSON file")
@_add_particle_options
def preview(
    preset_name: str | None,
    preset_file: str | None,
    **kwargs: object,
) -> None:
    """Launch the GUI with live particle preview."""
    overrides = _collect_overrides(**kwargs)

    try:
        preset = _build_preset(preset_name, preset_file, overrides)
    except (ValueError, FileNotFoundError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    from particle_gen.app import run_gui
    run_gui(preset)


@cli.command("list-presets")
def list_presets() -> None:
    """List built-in particle presets."""
    presets = list_builtin_presets()
    for p in presets:
        click.echo(f"  {p.name:<20s} {p.description}")

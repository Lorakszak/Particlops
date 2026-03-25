"""Built-in preset discovery and loading."""

from importlib import resources
from pathlib import Path

from particle_gen.presets.schema import ParticlePreset, load_preset


def _defaults_dir() -> Path:
    """Get path to the built-in defaults directory."""
    return Path(str(resources.files("particle_gen.presets") / "defaults"))


def list_builtin_presets() -> list[ParticlePreset]:
    """Load and return all built-in presets."""
    defaults = _defaults_dir()
    presets = []
    for path in sorted(defaults.glob("*.json")):
        presets.append(load_preset(path))
    return presets


def load_builtin_preset(name: str) -> ParticlePreset:
    """Load a specific built-in preset by name."""
    path = _defaults_dir() / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Built-in preset '{name}' not found")
    return load_preset(path)

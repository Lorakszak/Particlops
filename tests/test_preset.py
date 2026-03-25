"""Tests for ParticlePreset dataclass -- serialization, validation, loading."""

import json
import tempfile
from pathlib import Path

import pytest

from particle_gen.presets.schema import ParticlePreset, load_preset, save_preset


def test_default_values() -> None:
    p = ParticlePreset(name="test", description="test preset")
    assert p.max_particles == 2000
    assert p.spawn_rate == 100.0
    assert p.colors == ["#00ff99"]


def test_round_trip_json() -> None:
    p = ParticlePreset(
        name="test",
        description="round trip",
        max_particles=5000,
        vortex=0.5,
        colors=["#ff0000", "#00ff00"],
    )
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        save_preset(p, Path(f.name))
        loaded = load_preset(Path(f.name))
    assert loaded.name == "test"
    assert loaded.max_particles == 5000
    assert loaded.vortex == 0.5
    assert loaded.colors == ["#ff0000", "#00ff00"]


def test_validation_speed_min_max() -> None:
    with pytest.raises(ValueError, match="speed_min.*speed_max"):
        ParticlePreset(name="bad", description="", speed_min=0.5, speed_max=0.1)


def test_validation_spawn_mode() -> None:
    with pytest.raises(ValueError, match="spawn_mode"):
        ParticlePreset(name="bad", description="", spawn_mode="invalid")


def test_unknown_keys_in_json_ignored() -> None:
    data = {"name": "x", "description": "x", "future_field": 42}
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(data, f)
    loaded = load_preset(Path(f.name))
    assert loaded.name == "x"

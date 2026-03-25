"""ParticlePreset dataclass -- configuration for particle generation."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

VALID_SPAWN_MODES = {"point", "line", "circle", "edges", "random"}
VALID_SIZE_OVER_LIFE = {"constant", "grow", "shrink", "pulse"}
VALID_FADE_CURVES = {"linear", "ease_out", "flash"}


@dataclass
class ParticlePreset:
    """Complete configuration for a particle video."""

    name: str
    description: str

    # Core
    max_particles: int = 2000
    particle_size: float = 4.0
    spawn_rate: float = 100.0
    lifetime: float = 2.0
    spread: float = 0.5

    # Spawn
    spawn_mode: str = "point"
    spawn_x: float = 0.5
    spawn_y: float = 0.5
    spawn_radius: float = 0.3

    # Physics
    gravity_x: float = 0.0
    gravity_y: float = -0.1
    speed_min: float = 0.05
    speed_max: float = 0.3
    drag: float = 0.0
    turbulence: float = 0.0
    radial_force: float = 0.0
    vortex: float = 0.0

    # Lifecycle
    size_over_life: str = "constant"
    fade_curve: str = "linear"
    color_over_life: bool = False

    # Colors
    colors: list[str] = field(default_factory=lambda: ["#00ff99"])

    def __post_init__(self) -> None:
        if self.speed_min > self.speed_max:
            raise ValueError(
                f"speed_min ({self.speed_min}) must be <= speed_max ({self.speed_max})"
            )
        if self.spawn_mode not in VALID_SPAWN_MODES:
            raise ValueError(
                f"spawn_mode must be one of {VALID_SPAWN_MODES}, got '{self.spawn_mode}'"
            )
        if self.size_over_life not in VALID_SIZE_OVER_LIFE:
            raise ValueError(
                f"size_over_life must be one of {VALID_SIZE_OVER_LIFE}, "
                f"got '{self.size_over_life}'"
            )
        if self.fade_curve not in VALID_FADE_CURVES:
            raise ValueError(
                f"fade_curve must be one of {VALID_FADE_CURVES}, got '{self.fade_curve}'"
            )


def save_preset(preset: ParticlePreset, path: Path) -> None:
    """Save a preset to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(preset), indent=2), encoding="utf-8")


def load_preset(path: Path) -> ParticlePreset:
    """Load a preset from a JSON file. Unknown keys are ignored."""
    data = json.loads(path.read_text(encoding="utf-8"))
    valid_fields = {f.name for f in ParticlePreset.__dataclass_fields__.values()}
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    return ParticlePreset(**filtered)

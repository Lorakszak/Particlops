# Particlops

A CLI + GUI tool for generating seamlessly looped particle videos on black backgrounds. The output videos are designed to be composited onto other footage using additive or screen blend modes in video editors.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- ffmpeg (must be on your PATH)
- OpenGL 3.3+ capable GPU

### System dependencies

**Fedora:**

```bash
sudo dnf install ffmpeg mesa-libGL
```

**Ubuntu/Debian:**

```bash
sudo apt install ffmpeg libgl1-mesa-glx libegl1
```

**macOS:**

```bash
brew install ffmpeg
```

## Installation

```bash
git clone <repo-url> && cd particle_gen
uv sync
```

For development tools (pytest, ruff, pyright):

```bash
uv sync --extra dev
```

## Usage

### GUI (live preview)

Launch the GUI with a live particle preview and sidebar controls:

```bash
uv run particlops preview
```

Start with a built-in preset:

```bash
uv run particlops preview --preset stardust
```

Load a custom preset file:

```bash
uv run particlops preview --preset-file my_preset.json
```

The GUI window has:

- **Left panel** -- live OpenGL particle preview at ~60fps
- **Right sidebar** -- all particle parameters grouped into sections (Core, Spawn, Physics, Lifecycle, Colors). Changes apply immediately to the preview.
- **Export section** -- set duration, crossfade, resolution, fps, CRF, and output path. Click "Generate" to render the video in the background with a progress dialog.

You can also load/save presets via the buttons at the top of the sidebar.

### CLI (headless rendering)

Generate a looped particle video:

```bash
uv run particlops generate --preset rising_sparks --duration 30 --output sparks.mp4
```

With custom parameters:

```bash
uv run particlops generate \
  --duration 15 \
  --crossfade 5 \
  --resolution 1920x1080 \
  --fps 60 \
  --crf 18 \
  --particles 3000 \
  --spawn-rate 200 \
  --lifetime 3 \
  --spawn-mode circle \
  --vortex 0.5 \
  --turbulence 0.2 \
  --colors "#ff00ff,#00ffff,#ffff00" \
  --output vortex.mp4
```

Quick test render (low-res, short):

```bash
uv run particlops generate \
  --preset stardust \
  --duration 5 \
  --crossfade 2 \
  --resolution 640x360 \
  --fps 30 \
  --output /tmp/test_loop.mp4
```

Verify the loop by playing it:

```bash
mpv --loop /tmp/test_loop.mp4
```

### List built-in presets

```bash
uv run particlops list-presets
```

Available presets:

| Preset | Description |
|--------|-------------|
| `gentle_snow` | Slow drifting white and blue particles |
| `rising_sparks` | Upward embers with warm orange, red, and yellow |
| `vortex_swirl` | Spiral motion with multi-color particles |
| `stardust` | Gentle outward drift with white, cyan, and purple |
| `fireflies` | Random slow pulsing particles in green and yellow |

### Save/load custom presets

Save current CLI settings to a JSON file:

```bash
uv run particlops generate --preset stardust --vortex 0.3 --save-preset my_preset.json --output out.mp4
```

Use a saved preset:

```bash
uv run particlops generate --preset-file my_preset.json --output out.mp4
```

### Reproducible renders

Use `--seed` for deterministic output:

```bash
uv run particlops generate --preset fireflies --seed 42 --output fireflies.mp4
```

## How the seamless loop works

The export pipeline runs the particle simulation in a single pass, rendering `duration + crossfade` total frames:

1. **Pre-roll** -- the simulation runs without recording for several seconds so the screen starts populated with particles
2. **Head frames** (first `crossfade` seconds) -- compressed as PNGs and held in RAM
3. **Middle frames** -- streamed directly to a lossless intermediate file
4. **Tail frames** (last `crossfade` seconds) -- alpha-blended with the corresponding head frames

The blended head and middle segments are concatenated and encoded to the final H.264 MP4. When the video loops, the transition from the last frame back to the first is seamless because the crossfade region smoothly blends between them.

## CLI reference

```
particlops generate [OPTIONS]

Core:
  --duration FLOAT       Video length in seconds (default: 30)
  --crossfade FLOAT      Loop overlap in seconds (default: 10)
  --output PATH          Output file path (default: particles.mp4)
  --preset NAME          Built-in preset name
  --preset-file PATH     Path to preset JSON file
  --seed INT             Random seed for reproducibility
  --preroll FLOAT        Pre-roll seconds (default: auto)

Video:
  --resolution WxH       Output resolution (default: 1920x1080)
  --fps INT              Frames per second (default: 60)
  --crf INT              H.264 CRF quality, lower = better (default: 18)
  --codec STR            Video codec (default: libx264)

Particles:
  --particles INT        Max particles alive at once
  --size FLOAT           Base particle size in pixels
  --spawn-rate FLOAT     Particles per second
  --lifetime FLOAT       Seconds per particle
  --spread FLOAT         Spawn velocity spread
  --spawn-mode STR       point | line | circle | edges | random
  --spawn-x FLOAT        Horizontal spawn position (0-1)
  --spawn-y FLOAT        Vertical spawn position (0-1)
  --spawn-radius FLOAT   Radius for circle mode
  --gravity-x FLOAT      Horizontal gravity
  --gravity-y FLOAT      Vertical gravity
  --speed-min FLOAT      Min initial speed
  --speed-max FLOAT      Max initial speed
  --drag FLOAT           Velocity damping
  --turbulence FLOAT     Noise perturbation
  --radial-force FLOAT   Attract/repel from spawn
  --vortex FLOAT         Rotational force
  --size-over-life STR   constant | grow | shrink | pulse
  --fade-curve STR       linear | ease_out | flash
  --color-over-life      Shift through palette over lifetime
  --colors STR           Comma-separated hex colors

Other:
  --save-preset PATH     Save current settings to JSON
```

## Development

```bash
uv run pytest tests/ -v       # run tests
uv run ruff check src/ tests/ # lint
uv run pyright src/            # type check
```

## License

MIT

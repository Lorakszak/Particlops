# Particlops

Standalone CLI + GUI tool for generating seamlessly looped particle videos on black backgrounds. Forked from wavern's particle system with all audio-reactive functionality stripped.

## Commands

```bash
uv sync --extra dev          # install deps
uv run pytest tests/ -v      # run tests (42 tests)
uv run ruff check src/ tests/ # lint
uv run pyright src/           # type check
uv run particlops --help      # CLI help
```

## Architecture

```
src/particle_gen/
  cli.py              -- click CLI entry point (generate | preview | list-presets)
  app.py              -- PySide6 QApplication bootstrap, called by `preview` command
  core/
    particles.py      -- CPU-side particle simulation (numpy arrays, no GPU)
                         13-column particle array: x, y, vx, vy, age, lifetime, base_size, r, g, b, alpha, color_idx, shape
                         Spawn modes: point, line, circle, edges, random
                         Physics: gravity, turbulence, radial force, vortex, drag
                         Lifecycle: size_over_life, fade_curve, color_over_life
    renderer.py       -- moderngl renderer: creates FBO, clears black, draws particles with additive blending, reads pixels
    export.py         -- ExportPipeline: three-phase render (pre-roll -> single-pass with head/middle/tail -> ffmpeg concat)
                         Cross-fade blending: head frames compressed as PNG in RAM, tail frames blended with head, assembled via FFV1 intermediates
    timeline.py       -- Frame/time conversion (copied from wavern as-is)
  gui/
    gl_widget.py      -- QOpenGLWidget with 60fps QTimer, creates moderngl context + Renderer
    sidebar.py        -- QScrollArea with grouped controls, emits params_changed(str, object) signal
    main_window.py    -- QSplitter layout (GL left, sidebar right), export runs in QThread
  shaders/
    __init__.py       -- load_shader() using importlib.resources
    particles.vert    -- maps [0,1] position to clip space, passes size/color/alpha
    particles.frag    -- circular soft-edge point sprite with alpha
  presets/
    schema.py         -- ParticlePreset dataclass with __post_init__ validation, JSON load/save via dataclasses.asdict
    manager.py        -- list_builtin_presets() / load_builtin_preset(name) from defaults/ dir
    defaults/         -- 5 JSON presets: gentle_snow, rising_sparks, vortex_swirl, stardust, fireflies
```

## Key design decisions

- **No audio dependency**: All wavern audio refs (FrameAnalysis, amplitude, beat_intensity) removed. Spawn rate is constant particles/second with fractional accumulator.
- **Seamless loop**: Single simulation pass renders `duration + crossfade` frames. Head frames stored as compressed PNGs in RAM (~180 MB for 10s/1080p/60fps). Tail frames alpha-blended with corresponding head frames. Final video assembled via ffmpeg concat of FFV1 lossless intermediates.
- **Deterministic**: Optional `--seed INT` creates `np.random.default_rng(seed)` instance (not global state).
- **ParticleSystem is pure numpy**: No GPU/moderngl dependency. Renderer handles all GPU interaction. This separation allows testing particle physics without an OpenGL context.
- **Presets are plain dataclasses**: No pydantic. Validation in `__post_init__`. JSON round-trip via `dataclasses.asdict()` / filtered `**kwargs` construction. Unknown keys silently ignored on load.

## Conventions

- Python 3.12, src layout, hatchling build
- ruff for linting (line-length 100), pyright for type checking (standard mode)
- All functions have type hints
- Tests in `tests/`, no GPU-dependent tests (particle/preset/export/CLI tests are all CPU-only)
- Atomic commits with conventional messages (feat:, fix:, chore:, refactor:)
- External dependency: ffmpeg must be on PATH (checked in test_export.py)

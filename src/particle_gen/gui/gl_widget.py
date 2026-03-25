"""OpenGL preview widget for live particle rendering."""

import time

import moderngl
import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from particle_gen.core.particles import ParticleSystem
from particle_gen.core.renderer import Renderer
from particle_gen.presets.schema import ParticlePreset


class GLWidget(QOpenGLWidget):
    """Live particle preview using moderngl."""

    def __init__(self, preset: ParticlePreset) -> None:
        super().__init__()
        self._preset = preset
        self._ctx: moderngl.Context | None = None
        self._renderer: Renderer | None = None
        self._system: ParticleSystem | None = None
        self._last_time = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def initializeGL(self) -> None:
        self._ctx = moderngl.create_context()
        self._renderer = Renderer(self._ctx)
        self._rebuild_system()
        self._last_time = time.monotonic()
        self._timer.start(16)  # ~60fps

    def _rebuild_system(self) -> None:
        """Create a new ParticleSystem from current preset."""
        p = self._preset
        self._system = ParticleSystem(
            max_particles=p.max_particles,
            particle_size=p.particle_size,
            spawn_rate=p.spawn_rate,
            lifetime=p.lifetime,
            spread=p.spread,
            spawn_mode=p.spawn_mode,
            spawn_x=p.spawn_x,
            spawn_y=p.spawn_y,
            spawn_radius=p.spawn_radius,
            gravity_x=p.gravity_x,
            gravity_y=p.gravity_y,
            speed_min=p.speed_min,
            speed_max=p.speed_max,
            drag=p.drag,
            turbulence=p.turbulence,
            radial_force=p.radial_force,
            vortex=p.vortex,
            size_over_life=p.size_over_life,
            fade_curve=p.fade_curve,
            color_over_life=p.color_over_life,
            colors=p.colors,
        )
        if self._renderer:
            self._renderer.initialize(p.max_particles)

    def paintGL(self) -> None:
        if not self._ctx or not self._renderer or not self._system:
            return

        now = time.monotonic()
        dt = min(now - self._last_time, 0.05)  # cap at 50ms
        self._last_time = now

        self._system.step(dt)

        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        resolution = (w, h)
        fbo = self._renderer.ensure_fbo(resolution)
        self._renderer.render_frame(self._system, fbo, resolution)

        # Blit FBO to default framebuffer
        self._ctx.screen.use()
        self._ctx.viewport = (0, 0, w, h)
        self._ctx.clear(0.0, 0.0, 0.0, 1.0)

        if self._renderer._fbo_texture:
            self._renderer._fbo_texture.use(0)
            # Use simple full-screen blit via reading and writing back
            data = fbo.read(components=3)
            arr = np.frombuffer(data, dtype=np.uint8).reshape(h, w, 3)
            # Write to screen - moderngl's screen FBO
            screen_texture = self._ctx.texture((w, h), 3, arr.tobytes())
            screen_texture.use(0)
            screen_texture.release()

    def _tick(self) -> None:
        self.update()

    def set_preset(self, preset: ParticlePreset) -> None:
        """Replace the preset and rebuild the particle system."""
        self._preset = preset
        if self._renderer:
            self._rebuild_system()

    def update_param(self, key: str, value: object) -> None:
        """Update a single parameter on the live system."""
        if self._system is None:
            return

        if key == "colors" and isinstance(value, list):
            from particle_gen.core.particles import hex_to_rgb
            self._system.colors_hex = value
            self._system.colors_rgb = np.array(
                [hex_to_rgb(c) for c in value], dtype="f4"
            )
        elif key == "max_particles":
            # Requires system rebuild
            setattr(self._preset, key, value)
            self._rebuild_system()
        elif hasattr(self._system, key):
            setattr(self._system, key, value)

    def cleanup(self) -> None:
        """Release GPU resources."""
        self._timer.stop()
        if self._renderer:
            self._renderer.cleanup()

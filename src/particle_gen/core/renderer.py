"""Simplified renderer -- black background + particles."""

import logging

import moderngl
import numpy as np
from numpy.typing import NDArray

from particle_gen.core.particles import ParticleSystem
from particle_gen.shaders import load_shader

logger = logging.getLogger(__name__)


class Renderer:
    """Renders particle system to an FBO. Display-agnostic."""

    def __init__(self, ctx: moderngl.Context) -> None:
        self.ctx = ctx
        self._program: moderngl.Program | None = None
        self._vao: moderngl.VertexArray | None = None
        self._vbo: moderngl.Buffer | None = None
        self._fbo: moderngl.Framebuffer | None = None
        self._fbo_texture: moderngl.Texture | None = None

    def initialize(self, max_particles: int) -> None:
        """Create GPU resources."""
        vert_src = load_shader("particles.vert")
        frag_src = load_shader("particles.frag")
        self._program = self.ctx.program(
            vertex_shader=vert_src, fragment_shader=frag_src,
        )
        self._vbo = self.ctx.buffer(reserve=max_particles * 8 * 4)
        self._vao = self.ctx.vertex_array(
            self._program,
            [(self._vbo, "2f 1f 3f 1f 1f", "in_position", "in_size", "in_color", "in_alpha", "in_shape")],
        )

    def ensure_fbo(self, resolution: tuple[int, int]) -> moderngl.Framebuffer:
        """Create or resize the offscreen FBO."""
        if self._fbo is not None and self._fbo_texture is not None:
            if self._fbo_texture.size == resolution:
                return self._fbo
            self._fbo.release()
            self._fbo_texture.release()

        self._fbo_texture = self.ctx.texture(resolution, 4)
        self._fbo = self.ctx.framebuffer(color_attachments=[self._fbo_texture])
        return self._fbo

    def render_frame(
        self,
        system: ParticleSystem,
        fbo: moderngl.Framebuffer,
        resolution: tuple[int, int],
    ) -> None:
        """Render one frame: clear black, draw particles."""
        fbo.use()
        self.ctx.viewport = (0, 0, resolution[0], resolution[1])
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

        render_data = system.get_render_data()
        if len(render_data) == 0:
            return

        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE | moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)

        assert self._vbo is not None
        assert self._vao is not None
        self._vbo.write(render_data.tobytes())

        if self._program is not None and "u_resolution" in self._program:
            self._program["u_resolution"].value = resolution

        self._vao.render(moderngl.POINTS, vertices=len(render_data))
        self.ctx.disable(moderngl.PROGRAM_POINT_SIZE | moderngl.BLEND)

    def read_pixels(
        self, fbo: moderngl.Framebuffer, resolution: tuple[int, int],
    ) -> NDArray[np.uint8]:
        """Read RGB pixels from FBO, flipped for top-down order."""
        fbo.use()
        data = fbo.read(components=3)
        arr = np.frombuffer(data, dtype=np.uint8).reshape(
            resolution[1], resolution[0], 3,
        )
        return np.flipud(arr).copy()

    def cleanup(self) -> None:
        """Release all GPU resources."""
        for resource in (self._vao, self._vbo, self._program, self._fbo, self._fbo_texture):
            if resource is not None:
                resource.release()

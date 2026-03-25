"""Export pipeline -- cross-fade seamless loop rendering via ffmpeg."""

import io
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

import moderngl
import numpy as np
from numpy.typing import NDArray
from PIL import Image

from particle_gen.core.particles import ParticleSystem
from particle_gen.core.renderer import Renderer
from particle_gen.core.timeline import Timeline
from particle_gen.presets.schema import ParticlePreset

logger = logging.getLogger(__name__)


def validate_export_params(duration: float, crossfade: float) -> None:
    """Validate export parameters."""
    if duration <= 0:
        raise ValueError("duration must be > 0")
    if crossfade >= duration / 2:
        raise ValueError(
            f"crossfade ({crossfade}) must be < duration/2 ({duration / 2})"
        )


def blend_crossfade(
    head: NDArray[np.uint8], tail: NDArray[np.uint8], alpha: float,
) -> NDArray[np.uint8]:
    """Alpha-blend two frames: output = tail * (1 - alpha) + head * alpha."""
    blended = tail.astype(np.float32) * (1.0 - alpha) + head.astype(np.float32) * alpha
    return np.clip(blended, 0, 255).astype(np.uint8)


def _compress_frame(frame: NDArray[np.uint8]) -> bytes:
    """Compress an RGB frame to PNG bytes in RAM."""
    img = Image.fromarray(frame)
    buf = io.BytesIO()
    img.save(buf, format="PNG", compress_level=1)
    return buf.getvalue()


def _decompress_frame(data: bytes) -> NDArray[np.uint8]:
    """Decompress PNG bytes back to an RGB numpy array."""
    img = Image.open(io.BytesIO(data))
    return np.array(img, dtype=np.uint8)


def _start_ffmpeg_lossless(
    path: Path, resolution: tuple[int, int], fps: int,
) -> subprocess.Popen[bytes]:
    """Start an ffmpeg process for lossless FFV1 intermediate encoding."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pixel_format", "rgb24",
        "-video_size", f"{resolution[0]}x{resolution[1]}",
        "-framerate", str(fps),
        "-i", "pipe:0",
        "-c:v", "ffv1",
        "-level", "3",
        str(path),
    ]
    return subprocess.Popen(
        cmd, stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _concat_and_encode(
    blended_path: Path,
    middle_path: Path,
    output_path: Path,
    codec: str,
    crf: int,
) -> None:
    """Concatenate blended-head + middle intermediates and encode to final output."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="concat_",
    ) as f:
        f.write(f"file '{blended_path}'\n")
        f.write(f"file '{middle_path}'\n")
        concat_list = Path(f.name)

    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c:v", codec,
            "-crf", str(crf),
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    finally:
        concat_list.unlink(missing_ok=True)


class ExportPipeline:
    """Renders a seamlessly looped particle video."""

    def __init__(
        self,
        preset: ParticlePreset,
        duration: float = 30.0,
        crossfade: float = 10.0,
        resolution: tuple[int, int] = (1920, 1080),
        fps: int = 60,
        crf: int = 18,
        codec: str = "libx264",
        output: Path = Path("particles.mp4"),
        seed: int | None = None,
        preroll: float | None = None,
        progress_callback: Callable[[float], None] | None = None,
    ) -> None:
        validate_export_params(duration, crossfade)
        self.preset = preset
        self.duration = duration
        self.crossfade = crossfade
        self.resolution = resolution
        self.fps = fps
        self.crf = crf
        self.codec = codec
        self.output = output
        self.seed = seed
        self.preroll = preroll if preroll is not None else max(preset.lifetime * 3, 5.0)
        self.progress_callback = progress_callback

    def run(self) -> Path:
        """Execute the full export pipeline. Returns the output path."""
        rng = np.random.default_rng(self.seed) if self.seed is not None else None

        system = ParticleSystem(
            max_particles=self.preset.max_particles,
            particle_size=self.preset.particle_size,
            spawn_rate=self.preset.spawn_rate,
            lifetime=self.preset.lifetime,
            spread=self.preset.spread,
            spawn_mode=self.preset.spawn_mode,
            spawn_x=self.preset.spawn_x,
            spawn_y=self.preset.spawn_y,
            spawn_radius=self.preset.spawn_radius,
            gravity_x=self.preset.gravity_x,
            gravity_y=self.preset.gravity_y,
            speed_min=self.preset.speed_min,
            speed_max=self.preset.speed_max,
            drag=self.preset.drag,
            turbulence=self.preset.turbulence,
            radial_force=self.preset.radial_force,
            vortex=self.preset.vortex,
            size_min=self.preset.size_min,
            size_max=self.preset.size_max,
            lifetime_min=self.preset.lifetime_min,
            lifetime_max=self.preset.lifetime_max,
            particle_shapes=self.preset.particle_shapes,
            size_over_life=self.preset.size_over_life,
            fade_curve=self.preset.fade_curve,
            color_over_life=self.preset.color_over_life,
            colors=self.preset.colors,
            rng=rng,
        )

        ctx = moderngl.create_standalone_context()
        renderer = Renderer(ctx)
        renderer.initialize(self.preset.max_particles)
        fbo = renderer.ensure_fbo(self.resolution)

        dt = 1.0 / self.fps
        timeline = Timeline(self.duration, self.fps)
        duration_frames = timeline.total_frames
        crossfade_frames = int(self.crossfade * self.fps)
        total_render_frames = duration_frames + crossfade_frames
        preroll_frames = int(self.preroll * self.fps)

        # Phase 1: Pre-roll
        logger.info("Pre-roll: %d frames (%.1fs)", preroll_frames, self.preroll)
        for _ in range(preroll_frames):
            system.step(dt)

        # Phase 2: Single-pass render
        head_buffer: list[bytes] = []
        tmp_dir = tempfile.mkdtemp(prefix="particle_gen_")
        blended_path = Path(tmp_dir) / "blended.mkv"
        middle_path = Path(tmp_dir) / "middle.mkv"

        middle_proc: subprocess.Popen[bytes] | None = None
        blended_proc: subprocess.Popen[bytes] | None = None

        try:
            for frame_idx in range(total_render_frames):
                system.step(dt)
                renderer.render_frame(system, fbo, self.resolution)
                pixels = renderer.read_pixels(fbo, self.resolution)

                if frame_idx < crossfade_frames:
                    # Head frames: compress to RAM
                    head_buffer.append(_compress_frame(pixels))
                elif frame_idx < duration_frames:
                    # Middle frames: stream to FFV1
                    if middle_proc is None:
                        middle_proc = _start_ffmpeg_lossless(
                            middle_path, self.resolution, self.fps,
                        )
                    assert middle_proc.stdin is not None
                    middle_proc.stdin.write(pixels.tobytes())
                else:
                    # Tail frames: blend with head and stream
                    tail_idx = frame_idx - duration_frames
                    alpha = tail_idx / crossfade_frames if crossfade_frames > 0 else 1.0
                    head_frame = _decompress_frame(head_buffer[tail_idx])
                    blended = blend_crossfade(head_frame, pixels, alpha)

                    if blended_proc is None:
                        blended_proc = _start_ffmpeg_lossless(
                            blended_path, self.resolution, self.fps,
                        )
                    assert blended_proc.stdin is not None
                    blended_proc.stdin.write(blended.tobytes())

                if self.progress_callback:
                    progress = (frame_idx + 1) / total_render_frames
                    self.progress_callback(progress)

            # Close ffmpeg processes
            if middle_proc and middle_proc.stdin:
                middle_proc.stdin.close()
                middle_proc.wait()
            if blended_proc and blended_proc.stdin:
                blended_proc.stdin.close()
                blended_proc.wait()

            # Phase 3: Final assembly
            logger.info("Assembling final video: %s", self.output)
            self.output.parent.mkdir(parents=True, exist_ok=True)
            _concat_and_encode(
                blended_path, middle_path,
                self.output, self.codec, self.crf,
            )

        finally:
            renderer.cleanup()
            ctx.release()
            # Clean up intermediates
            for p in (blended_path, middle_path):
                p.unlink(missing_ok=True)
            try:
                Path(tmp_dir).rmdir()
            except OSError:
                pass

        logger.info("Export complete: %s", self.output)
        return self.output

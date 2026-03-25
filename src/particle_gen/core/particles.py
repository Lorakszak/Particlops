"""Particle system -- CPU-side simulation with no audio dependency."""

import numpy as np

# Particle array columns
_COL_COUNT = 12
_X, _Y, _VX, _VY, _AGE, _LIFE, _BSIZE = 0, 1, 2, 3, 4, 5, 6
_R, _G, _B, _ALPHA, _CIDX = 7, 8, 9, 10, 11


def _simple_noise(x: np.ndarray, y: np.ndarray, t: float) -> tuple[np.ndarray, np.ndarray]:
    """Cheap sin-based turbulence -- returns (dx, dy) offset vectors."""
    nx = np.sin(x * 7.3 + t * 2.1) * np.cos(y * 5.7 + t * 1.3)
    ny = np.cos(x * 6.1 + t * 1.7) * np.sin(y * 8.3 + t * 2.9)
    return nx.astype("f4"), ny.astype("f4")


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    """Convert hex color string to normalized RGB tuple."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)


class ParticleSystem:
    """CPU-side particle simulation. No GPU or audio dependencies."""

    def __init__(
        self,
        *,
        max_particles: int = 2000,
        particle_size: float = 4.0,
        spawn_rate: float = 100.0,
        lifetime: float = 2.0,
        spread: float = 0.5,
        spawn_mode: str = "point",
        spawn_x: float = 0.5,
        spawn_y: float = 0.5,
        spawn_radius: float = 0.3,
        gravity_x: float = 0.0,
        gravity_y: float = -0.1,
        speed_min: float = 0.05,
        speed_max: float = 0.3,
        drag: float = 0.0,
        turbulence: float = 0.0,
        radial_force: float = 0.0,
        vortex: float = 0.0,
        size_over_life: str = "constant",
        fade_curve: str = "linear",
        color_over_life: bool = False,
        colors: list[str] | None = None,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.max_particles = max_particles
        self.particle_size = particle_size
        self.spawn_rate = spawn_rate
        self.lifetime = lifetime
        self.spread = spread
        self.spawn_mode = spawn_mode
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.spawn_radius = spawn_radius
        self.gravity_x = gravity_x
        self.gravity_y = gravity_y
        self.speed_min = speed_min
        self.speed_max = speed_max
        self.drag = drag
        self.turbulence = turbulence
        self.radial_force = radial_force
        self.vortex = vortex
        self.size_over_life = size_over_life
        self.fade_curve = fade_curve
        self.color_over_life = color_over_life
        self.colors_hex = colors or ["#00ff99"]
        self.colors_rgb = np.array(
            [hex_to_rgb(c) for c in self.colors_hex], dtype="f4"
        )

        self._rng = rng or np.random.default_rng()
        self.particles = np.zeros((max_particles, _COL_COUNT), dtype="f4")
        self.active_count = 0
        self._time = 0.0
        self._spawn_accum = 0.0

    def step(self, dt: float) -> None:
        """Advance the simulation by dt seconds."""
        self._time += dt
        self._update(dt)
        self._spawn(dt)

    def get_render_data(self) -> np.ndarray:
        """Return VBO-ready array: (N, 7) with position(2), size(1), color(3), alpha(1)."""
        if self.active_count == 0:
            return np.zeros((0, 7), dtype="f4")

        active = self.particles[:self.active_count]
        result = np.zeros((self.active_count, 7), dtype="f4")

        age_ratio = active[:, _AGE] / np.maximum(active[:, _LIFE], 0.01)
        age_ratio = np.clip(age_ratio, 0.0, 1.0)

        # Size over life
        base_size = active[:, _BSIZE]
        if self.size_over_life == "grow":
            size = base_size * (0.3 + 0.7 * age_ratio)
        elif self.size_over_life == "shrink":
            size = base_size * (1.0 - 0.7 * age_ratio)
        elif self.size_over_life == "pulse":
            size = base_size * (0.6 + 0.4 * np.sin(age_ratio * np.pi * 4.0))
        else:
            size = base_size

        # Fade curve
        if self.fade_curve == "ease_out":
            alpha = (1.0 - age_ratio) ** 0.5
        elif self.fade_curve == "flash":
            alpha = np.where(age_ratio < 0.7, 1.0, 1.0 - (age_ratio - 0.7) / 0.3)
        else:
            alpha = 1.0 - age_ratio
        alpha = np.clip(alpha, 0.0, 1.0).astype("f4")

        # Color over life
        n_colors = len(self.colors_rgb)
        if self.color_over_life and n_colors > 1:
            palette_pos = age_ratio * (n_colors - 1)
            idx_lo = np.clip(np.floor(palette_pos).astype(int), 0, n_colors - 2)
            idx_hi = idx_lo + 1
            frac = (palette_pos - idx_lo).astype("f4")
            result[:, 3] = (
                self.colors_rgb[idx_lo, 0] * (1 - frac)
                + self.colors_rgb[idx_hi, 0] * frac
            )
            result[:, 4] = (
                self.colors_rgb[idx_lo, 1] * (1 - frac)
                + self.colors_rgb[idx_hi, 1] * frac
            )
            result[:, 5] = (
                self.colors_rgb[idx_lo, 2] * (1 - frac)
                + self.colors_rgb[idx_hi, 2] * frac
            )
        else:
            result[:, 3] = active[:, _R]
            result[:, 4] = active[:, _G]
            result[:, 5] = active[:, _B]

        result[:, 0] = active[:, _X]
        result[:, 1] = active[:, _Y]
        result[:, 2] = size
        result[:, 6] = alpha
        return result

    def _update(self, dt: float) -> None:
        """Update positions, velocities, and ages."""
        if self.active_count == 0:
            return

        active = self.particles[:self.active_count]

        # Gravity
        active[:, _VX] += self.gravity_x * dt
        active[:, _VY] += self.gravity_y * dt

        # Turbulence (no audio modulation)
        if self.turbulence > 0.0:
            nx, ny = _simple_noise(active[:, _X], active[:, _Y], self._time)
            strength = self.turbulence * 0.5 * dt
            active[:, _VX] += nx * strength
            active[:, _VY] += ny * strength

        # Radial force
        if self.radial_force != 0.0:
            dx = active[:, _X] - self.spawn_x
            dy = active[:, _Y] - self.spawn_y
            dist = np.maximum(np.sqrt(dx * dx + dy * dy), 0.01)
            force_mag = self.radial_force * 0.3 * dt
            active[:, _VX] += (dx / dist) * force_mag
            active[:, _VY] += (dy / dist) * force_mag

        # Vortex
        if self.vortex != 0.0:
            dx = active[:, _X] - self.spawn_x
            dy = active[:, _Y] - self.spawn_y
            vortex_strength = self.vortex * 0.5 * dt
            active[:, _VX] += -dy * vortex_strength
            active[:, _VY] += dx * vortex_strength

        # Drag
        if self.drag > 0.0:
            drag_factor = (1.0 - self.drag) ** (dt * 60.0)
            active[:, _VX] *= drag_factor
            active[:, _VY] *= drag_factor

        # Position
        active[:, _X] += active[:, _VX] * dt
        active[:, _Y] += active[:, _VY] * dt

        # Age
        active[:, _AGE] += dt

        # Remove dead
        alive_mask = (
            (active[:, _AGE] < active[:, _LIFE])
            & (active[:, _X] > -0.5) & (active[:, _X] < 1.5)
            & (active[:, _Y] > -0.5) & (active[:, _Y] < 1.5)
        )
        alive_count = int(np.sum(alive_mask))
        if alive_count < self.active_count:
            self.particles[:alive_count] = active[alive_mask]
            self.active_count = alive_count

    def _spawn(self, dt: float) -> None:
        """Spawn new particles at a constant rate."""
        self._spawn_accum += self.spawn_rate * dt
        spawn_count = int(self._spawn_accum)
        self._spawn_accum -= spawn_count

        spawn_count = min(spawn_count, self.max_particles - self.active_count)
        if spawn_count <= 0:
            return

        n = spawn_count
        rng = self._rng

        angles = rng.uniform(0, 2 * np.pi, n).astype("f4")
        speeds = rng.uniform(self.speed_min, self.speed_max, n).astype("f4") * self.spread

        pos_x, pos_y = self._spawn_positions(n)
        vx, vy = self._spawn_velocities(n, pos_x, pos_y, angles, speeds)

        n_colors = len(self.colors_rgb)
        color_indices = rng.integers(0, n_colors, n)

        start = self.active_count
        end = start + spawn_count
        batch = self.particles[start:end]
        batch[:, _X] = pos_x
        batch[:, _Y] = pos_y
        batch[:, _VX] = vx
        batch[:, _VY] = vy
        batch[:, _AGE] = 0.0
        batch[:, _LIFE] = self.lifetime * rng.uniform(0.5, 1.5, n).astype("f4")
        batch[:, _BSIZE] = self.particle_size * rng.uniform(0.5, 1.5, n).astype("f4")
        batch[:, _R:_B + 1] = self.colors_rgb[color_indices]
        batch[:, _ALPHA] = 1.0
        batch[:, _CIDX] = color_indices.astype("f4")
        self.active_count = end

    def _spawn_positions(self, n: int) -> tuple[np.ndarray, np.ndarray]:
        """Compute spawn positions based on spawn_mode."""
        rng = self._rng
        if self.spawn_mode == "line":
            pos_x = rng.uniform(0.0, 1.0, n).astype("f4")
            pos_y = np.full(n, self.spawn_y, dtype="f4")
        elif self.spawn_mode == "circle":
            ring_angles = rng.uniform(0, 2 * np.pi, n).astype("f4")
            r = self.spawn_radius * rng.uniform(0.9, 1.1, n).astype("f4")
            pos_x = (self.spawn_x + np.cos(ring_angles) * r).astype("f4")
            pos_y = (self.spawn_y + np.sin(ring_angles) * r).astype("f4")
        elif self.spawn_mode == "edges":
            edge = rng.integers(0, 4, n)
            pos_x = np.empty(n, dtype="f4")
            pos_y = np.empty(n, dtype="f4")
            rand_t = rng.uniform(0.0, 1.0, n).astype("f4")
            bottom, top = edge == 0, edge == 1
            left, right = edge == 2, edge == 3
            pos_x[bottom] = rand_t[bottom]
            pos_y[bottom] = 0.0
            pos_x[top] = rand_t[top]
            pos_y[top] = 1.0
            pos_x[left] = 0.0
            pos_y[left] = rand_t[left]
            pos_x[right] = 1.0
            pos_y[right] = rand_t[right]
        elif self.spawn_mode == "random":
            pos_x = rng.uniform(0.0, 1.0, n).astype("f4")
            pos_y = rng.uniform(0.0, 1.0, n).astype("f4")
        else:  # point
            pos_x = np.full(n, self.spawn_x, dtype="f4")
            pos_y = np.full(n, self.spawn_y, dtype="f4")
        return pos_x, pos_y

    def _spawn_velocities(
        self, n: int, pos_x: np.ndarray, pos_y: np.ndarray,
        angles: np.ndarray, speeds: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute initial velocities based on spawn_mode."""
        if self.spawn_mode == "edges":
            dx = self.spawn_x - pos_x
            dy = self.spawn_y - pos_y
            dist = np.maximum(np.sqrt(dx * dx + dy * dy), 0.01)
            spread_angle = self._rng.uniform(-0.4, 0.4, n).astype("f4")
            cos_s, sin_s = np.cos(spread_angle), np.sin(spread_angle)
            dir_x, dir_y = dx / dist, dy / dist
            vx = (dir_x * cos_s - dir_y * sin_s) * speeds
            vy = (dir_x * sin_s + dir_y * cos_s) * speeds
        elif self.spawn_mode == "circle":
            dx = pos_x - self.spawn_x
            dy = pos_y - self.spawn_y
            dist = np.maximum(np.sqrt(dx * dx + dy * dy), 0.01)
            vx = (dx / dist) * speeds
            vy = (dy / dist) * speeds
        else:
            vx = np.cos(angles) * speeds
            vy = np.sin(angles) * speeds
        return vx.astype("f4"), vy.astype("f4")

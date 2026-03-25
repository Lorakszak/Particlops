"""Tests for particle system -- physics, spawning, lifecycle."""

import numpy as np
import pytest

from particle_gen.core.particles import ParticleSystem


@pytest.fixture
def system() -> ParticleSystem:
    return ParticleSystem(
        max_particles=500,
        spawn_rate=100.0,
        lifetime=2.0,
        particle_size=4.0,
        spread=0.5,
        spawn_mode="point",
        spawn_x=0.5,
        spawn_y=0.5,
        spawn_radius=0.3,
        gravity_x=0.0,
        gravity_y=0.0,
        speed_min=0.05,
        speed_max=0.3,
        drag=0.0,
        turbulence=0.0,
        radial_force=0.0,
        vortex=0.0,
        size_over_life="constant",
        fade_curve="linear",
        color_over_life=False,
        colors=["#ff0000"],
    )


def test_initial_state(system: ParticleSystem) -> None:
    assert system.active_count == 0


def test_spawn_creates_particles(system: ParticleSystem) -> None:
    system.step(dt=0.1)
    assert system.active_count > 0


def test_particles_die_after_lifetime() -> None:
    s = ParticleSystem(
        max_particles=500, spawn_rate=100.0, lifetime=0.5,
        particle_size=4.0, spread=0.5, spawn_mode="point",
        spawn_x=0.5, spawn_y=0.5, spawn_radius=0.3,
        gravity_x=0.0, gravity_y=0.0, speed_min=0.01, speed_max=0.02,
        drag=0.0, turbulence=0.0, radial_force=0.0, vortex=0.0,
        size_over_life="constant", fade_curve="linear",
        color_over_life=False, colors=["#ff0000"],
    )
    s.step(dt=0.1)
    assert s.active_count > 0
    # Stop spawning and advance past lifetime
    s.spawn_rate = 0.0
    for _ in range(20):
        s.step(dt=0.1)
    assert s.active_count == 0


def test_gravity_moves_particles_down() -> None:
    s = ParticleSystem(
        max_particles=100, spawn_rate=1000.0, lifetime=10.0,
        particle_size=4.0, spread=0.0, spawn_mode="point",
        spawn_x=0.5, spawn_y=0.5, spawn_radius=0.3,
        gravity_x=0.0, gravity_y=-1.0, speed_min=0.0, speed_max=0.001,
        drag=0.0, turbulence=0.0, radial_force=0.0, vortex=0.0,
        size_over_life="constant", fade_curve="linear",
        color_over_life=False, colors=["#ff0000"],
    )
    s.step(dt=0.1)
    initial_y = s.particles[:s.active_count, 1].mean()
    for _ in range(10):
        s.step(dt=0.1)
    final_y = s.particles[:s.active_count, 1].mean()
    assert final_y < initial_y


def test_spawn_mode_random() -> None:
    s = ParticleSystem(
        max_particles=500, spawn_rate=5000.0, lifetime=10.0,
        particle_size=4.0, spread=0.5, spawn_mode="random",
        spawn_x=0.5, spawn_y=0.5, spawn_radius=0.3,
        gravity_x=0.0, gravity_y=0.0, speed_min=0.01, speed_max=0.02,
        drag=0.0, turbulence=0.0, radial_force=0.0, vortex=0.0,
        size_over_life="constant", fade_curve="linear",
        color_over_life=False, colors=["#ff0000"],
    )
    s.step(dt=0.1)
    active = s.particles[:s.active_count]
    assert active[:, 0].min() < 0.3
    assert active[:, 0].max() > 0.7


def test_spawn_mode_line() -> None:
    s = ParticleSystem(
        max_particles=500, spawn_rate=5000.0, lifetime=10.0,
        particle_size=4.0, spread=0.5, spawn_mode="line",
        spawn_x=0.5, spawn_y=0.3, spawn_radius=0.3,
        gravity_x=0.0, gravity_y=0.0, speed_min=0.0, speed_max=0.001,
        drag=0.0, turbulence=0.0, radial_force=0.0, vortex=0.0,
        size_over_life="constant", fade_curve="linear",
        color_over_life=False, colors=["#ff0000"],
    )
    s.step(dt=0.01)
    active = s.particles[:s.active_count]
    np.testing.assert_allclose(active[:, 1], 0.3, atol=0.05)


def test_max_particles_cap() -> None:
    s = ParticleSystem(
        max_particles=50, spawn_rate=5000.0, lifetime=10.0,
        particle_size=4.0, spread=0.5, spawn_mode="point",
        spawn_x=0.5, spawn_y=0.5, spawn_radius=0.3,
        gravity_x=0.0, gravity_y=0.0, speed_min=0.05, speed_max=0.3,
        drag=0.0, turbulence=0.0, radial_force=0.0, vortex=0.0,
        size_over_life="constant", fade_curve="linear",
        color_over_life=False, colors=["#ff0000"],
    )
    for _ in range(10):
        s.step(dt=0.1)
    assert s.active_count <= 50


def test_deterministic_with_seed() -> None:
    kwargs: dict = dict(
        max_particles=200, spawn_rate=100.0, lifetime=2.0,
        particle_size=4.0, spread=0.5, spawn_mode="point",
        spawn_x=0.5, spawn_y=0.5, spawn_radius=0.3,
        gravity_x=0.0, gravity_y=-0.1, speed_min=0.05, speed_max=0.3,
        drag=0.0, turbulence=0.1, radial_force=0.0, vortex=0.0,
        size_over_life="constant", fade_curve="linear",
        color_over_life=False, colors=["#ff0000"],
    )
    rng1 = np.random.default_rng(42)
    s1 = ParticleSystem(**kwargs, rng=rng1)
    for _ in range(10):
        s1.step(dt=1 / 60)

    rng2 = np.random.default_rng(42)
    s2 = ParticleSystem(**kwargs, rng=rng2)
    for _ in range(10):
        s2.step(dt=1 / 60)

    np.testing.assert_array_equal(s1.particles, s2.particles)
    assert s1.active_count == s2.active_count


def test_get_render_data_shape(system: ParticleSystem) -> None:
    system.step(dt=0.1)
    data = system.get_render_data()
    assert data.ndim == 2
    assert data.shape[1] == 7  # x, y, size, r, g, b, alpha
    assert data.shape[0] == system.active_count

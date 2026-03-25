"""Tests for Timeline frame/time conversion."""

from particle_gen.core.timeline import Timeline


def test_total_frames() -> None:
    t = Timeline(duration=10.0, fps=60)
    assert t.total_frames == 600


def test_frame_to_time() -> None:
    t = Timeline(duration=10.0, fps=60)
    assert t.frame_to_time(0) == 0.0
    assert t.frame_to_time(60) == 1.0
    assert t.frame_to_time(600) == 10.0


def test_time_to_frame() -> None:
    t = Timeline(duration=10.0, fps=60)
    assert t.time_to_frame(0.0) == 0
    assert t.time_to_frame(1.0) == 60


def test_progress() -> None:
    t = Timeline(duration=10.0, fps=60)
    assert t.progress(0.0) == 0.0
    assert t.progress(5.0) == 0.5
    assert t.progress(10.0) == 1.0
    assert t.progress(15.0) == 1.0  # clamped

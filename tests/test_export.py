"""Tests for export pipeline -- cross-fade blending logic."""

import shutil

import numpy as np
import pytest

from particle_gen.core.export import blend_crossfade, validate_export_params


def test_validate_export_params_ok() -> None:
    validate_export_params(duration=30.0, crossfade=10.0)


def test_validate_crossfade_too_large() -> None:
    with pytest.raises(ValueError, match="crossfade"):
        validate_export_params(duration=30.0, crossfade=20.0)


def test_validate_crossfade_equals_half() -> None:
    with pytest.raises(ValueError, match="crossfade"):
        validate_export_params(duration=30.0, crossfade=15.0)


def test_validate_duration_zero() -> None:
    with pytest.raises(ValueError, match="duration"):
        validate_export_params(duration=0.0, crossfade=0.0)


def test_blend_crossfade_alpha_zero() -> None:
    head = np.full((4, 4, 3), 200, dtype=np.uint8)
    tail = np.full((4, 4, 3), 50, dtype=np.uint8)
    result = blend_crossfade(head, tail, alpha=0.0)
    np.testing.assert_array_equal(result, tail)


def test_blend_crossfade_alpha_one() -> None:
    head = np.full((4, 4, 3), 200, dtype=np.uint8)
    tail = np.full((4, 4, 3), 50, dtype=np.uint8)
    result = blend_crossfade(head, tail, alpha=1.0)
    np.testing.assert_array_equal(result, head)


def test_blend_crossfade_midpoint() -> None:
    head = np.full((4, 4, 3), 200, dtype=np.uint8)
    tail = np.full((4, 4, 3), 100, dtype=np.uint8)
    result = blend_crossfade(head, tail, alpha=0.5)
    expected = np.full((4, 4, 3), 150, dtype=np.uint8)
    np.testing.assert_array_almost_equal(result, expected, decimal=0)


def test_ffmpeg_available() -> None:
    assert shutil.which("ffmpeg") is not None, "ffmpeg not found on PATH"

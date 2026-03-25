"""Shader loading utilities."""

from importlib import resources


def load_shader(name: str) -> str:
    """Load a shader source file from the shaders package."""
    shader_dir = resources.files("particle_gen.shaders")
    shader_file = shader_dir.joinpath(name)
    return shader_file.read_text(encoding="utf-8")

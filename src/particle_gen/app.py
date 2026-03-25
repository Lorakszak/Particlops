"""QApplication bootstrap for particle-gen GUI."""

import sys

from PySide6.QtWidgets import QApplication

from particle_gen.gui.main_window import MainWindow
from particle_gen.presets.schema import ParticlePreset


def run_gui(preset: ParticlePreset) -> None:
    """Launch the GUI application."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(preset)
    window.show()
    app.exec()

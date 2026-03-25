"""QApplication bootstrap for particle-gen GUI."""

import sys
from importlib import resources

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from particle_gen.gui.main_window import MainWindow
from particle_gen.gui.theme import DARK_STYLESHEET
from particle_gen.presets.schema import ParticlePreset


def _load_icon() -> QIcon:
    """Load the application icon from the assets package."""
    assets_dir = resources.files("particle_gen.assets")
    icon_path = str(assets_dir.joinpath("logo.png"))
    return QIcon(icon_path)


def run_gui(preset: ParticlePreset) -> None:
    """Launch the GUI application."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)  # type: ignore[union-attr]

    icon = _load_icon()
    app.setWindowIcon(icon)  # type: ignore[union-attr]

    window = MainWindow(preset)
    window.setWindowIcon(icon)
    window.show()
    app.exec()  # type: ignore[union-attr]

"""QApplication bootstrap for particle-gen GUI."""

import sys
from importlib import resources

from PySide6.QtGui import QIcon, QSurfaceFormat
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
    # Core profile required: gl_PointCoord is always (0,0) in compatibility
    # profile because GL_POINT_SPRITE is disabled by default.
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)  # type: ignore[union-attr]

    icon = _load_icon()
    app.setWindowIcon(icon)  # type: ignore[union-attr]

    window = MainWindow(preset)
    window.setWindowIcon(icon)
    window.showMaximized()
    app.exec()  # type: ignore[union-attr]

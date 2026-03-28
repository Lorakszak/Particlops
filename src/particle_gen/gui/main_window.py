"""Main window -- live preview + sidebar controls + export."""

import logging
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QSplitter,
)

from particle_gen.core.export import ExportPipeline
from particle_gen.gui.gl_widget import GLWidget
from particle_gen.gui.sidebar import Sidebar
from particle_gen.presets.manager import load_builtin_preset
from particle_gen.presets.schema import ParticlePreset, load_preset, save_preset

logger = logging.getLogger(__name__)


class ExportThread(QThread):
    """Runs ExportPipeline in a background thread."""

    progress = Signal(float)
    finished_ok = Signal(str)
    finished_err = Signal(str)

    def __init__(self, pipeline: ExportPipeline) -> None:
        super().__init__()
        self._pipeline = pipeline
        self._pipeline.progress_callback = self._on_progress

    def _on_progress(self, p: float) -> None:
        self.progress.emit(p)

    def run(self) -> None:
        try:
            result = self._pipeline.run()
            self.finished_ok.emit(str(result))
        except Exception as e:
            self.finished_err.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window with preview and sidebar."""

    def __init__(self, preset: ParticlePreset) -> None:
        super().__init__()
        self.setWindowTitle("Particlops")
        self.resize(1280, 720)
        self._preset = preset

        # Widgets
        self._gl_widget = GLWidget(preset)
        self._sidebar = Sidebar()
        self._sidebar.set_from_preset(preset)

        # Layout
        splitter = QSplitter()
        splitter.addWidget(self._gl_widget)
        splitter.addWidget(self._sidebar)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        self.setCentralWidget(splitter)

        # Connections
        self._sidebar.params_changed.connect(self._on_param_changed)
        self._sidebar.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        self._sidebar.load_btn.clicked.connect(self._on_load_preset)
        self._sidebar.save_btn.clicked.connect(self._on_save_preset)
        self._sidebar.generate_btn.clicked.connect(self._on_generate)

        self._export_thread: ExportThread | None = None
        self._progress_dialog: QProgressDialog | None = None

    def _on_param_changed(self, key: str, value: object) -> None:
        """Forward parameter changes to the GL widget."""
        # Update preset
        if hasattr(self._preset, key):
            setattr(self._preset, key, value)
        self._gl_widget.update_param(key, value)

    def _on_preset_selected(self, name: str) -> None:
        if name == "(default)":
            preset = ParticlePreset(name="default", description="Default preset")
        else:
            try:
                preset = load_builtin_preset(name)
            except FileNotFoundError:
                return
        self._preset = preset
        self._sidebar.set_from_preset(preset)
        self._gl_widget.set_preset(preset)

    def _on_load_preset(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Preset", "", "JSON Files (*.json)",
        )
        if path:
            try:
                preset = load_preset(Path(path))
                self._preset = preset
                self._sidebar.set_from_preset(preset)
                self._gl_widget.set_preset(preset)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load preset: {e}")

    def _on_save_preset(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Preset", "preset.json", "JSON Files (*.json)",
        )
        if path:
            try:
                save_preset(self._preset, Path(path))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save preset: {e}")

    def _on_generate(self) -> None:
        export_params = self._sidebar.collect_export_params()

        try:
            pipeline = ExportPipeline(
                preset=self._preset,
                duration=export_params["duration"],
                crossfade=export_params["crossfade"],
                resolution=export_params["resolution"],
                fps=export_params["fps"],
                crf=export_params["crf"],
                output=Path(export_params["output"]),
            )
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
            return

        self._progress_dialog = QProgressDialog("Rendering...", "Cancel", 0, 100, self)
        self._progress_dialog.setWindowTitle("Export")
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.show()

        self._export_thread = ExportThread(pipeline)
        self._export_thread.progress.connect(self._on_export_progress)
        self._export_thread.finished_ok.connect(self._on_export_done)
        self._export_thread.finished_err.connect(self._on_export_error)
        self._export_thread.start()

    def _on_export_progress(self, p: float) -> None:
        if self._progress_dialog:
            self._progress_dialog.setValue(int(p * 100))

    def _on_export_done(self, path: str) -> None:
        if self._progress_dialog:
            self._progress_dialog.close()
        QMessageBox.information(self, "Export Complete", f"Video saved to:\n{path}")

    def _on_export_error(self, error: str) -> None:
        if self._progress_dialog:
            self._progress_dialog.close()
        QMessageBox.critical(self, "Export Error", f"Export failed:\n{error}")

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._gl_widget.cleanup()
        super().closeEvent(event)

"""Parameter sidebar with all particle controls."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from particle_gen.presets.schema import ParticlePreset


class Sidebar(QScrollArea):
    """Scrollable sidebar with grouped particle parameter controls."""

    params_changed = Signal(str, object)

    def __init__(self) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.setMinimumWidth(320)
        self._block_signals = False

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setSpacing(8)

        self._widgets: dict[str, QWidget] = {}

        self._add_preset_section()
        self._add_core_section()
        self._add_spawn_section()
        self._add_physics_section()
        self._add_lifecycle_section()
        self._add_colors_section()
        self._add_export_section()

        self._layout.addStretch()
        self.setWidget(container)

    # --- Section builders ---

    def _add_preset_section(self) -> None:
        group = QGroupBox("Preset")
        layout = QVBoxLayout(group)

        self._preset_combo = QComboBox()
        self._preset_combo.addItem("(default)")
        from particle_gen.presets.manager import list_builtin_presets
        for p in list_builtin_presets():
            self._preset_combo.addItem(p.name)
        layout.addWidget(self._preset_combo)

        btn_row = QHBoxLayout()
        self._load_btn = QPushButton("Load...")
        self._save_btn = QPushButton("Save...")
        btn_row.addWidget(self._load_btn)
        btn_row.addWidget(self._save_btn)
        layout.addLayout(btn_row)

        self._layout.addWidget(group)

    def _add_core_section(self) -> None:
        group = QGroupBox("Core")
        layout = QVBoxLayout(group)
        self._add_int_spin(layout, "max_particles", "Max Particles", 100, 10000, 2000)
        self._add_float_spin(layout, "particle_size", "Particle Size", 0.5, 100.0, 4.0)
        self._add_float_spin(layout, "spawn_rate", "Spawn Rate", 1.0, 5000.0, 100.0)
        self._add_float_spin(layout, "lifetime", "Lifetime", 0.1, 30.0, 2.0)
        self._add_float_spin(layout, "spread", "Spread", 0.01, 5.0, 0.5)
        self._layout.addWidget(group)

    def _add_spawn_section(self) -> None:
        group = QGroupBox("Spawn")
        layout = QVBoxLayout(group)
        self._add_combo(layout, "spawn_mode", "Mode",
                        ["point", "line", "circle", "edges", "random"], "point")
        self._add_float_spin(layout, "spawn_x", "Spawn X", 0.0, 1.0, 0.5, step=0.05)
        self._add_float_spin(layout, "spawn_y", "Spawn Y", 0.0, 1.0, 0.5, step=0.05)
        self._add_float_spin(layout, "spawn_radius", "Radius", 0.01, 1.0, 0.3, step=0.05)
        self._layout.addWidget(group)

    def _add_physics_section(self) -> None:
        group = QGroupBox("Physics")
        layout = QVBoxLayout(group)
        self._add_float_spin(layout, "gravity_x", "Gravity X", -1.0, 1.0, 0.0, step=0.01)
        self._add_float_spin(layout, "gravity_y", "Gravity Y", -5.0, 5.0, -0.1, step=0.01)
        self._add_float_spin(layout, "speed_min", "Speed Min", 0.01, 0.5, 0.05, step=0.01)
        self._add_float_spin(layout, "speed_max", "Speed Max", 0.1, 1.0, 0.3, step=0.01)
        self._add_float_spin(layout, "drag", "Drag", 0.0, 0.99, 0.0, step=0.01)
        self._add_float_spin(layout, "turbulence", "Turbulence", 0.0, 1.0, 0.0, step=0.01)
        self._add_float_spin(layout, "radial_force", "Radial Force", -1.0, 1.0, 0.0, step=0.01)
        self._add_float_spin(layout, "vortex", "Vortex", -1.0, 1.0, 0.0, step=0.01)
        self._layout.addWidget(group)

    def _add_lifecycle_section(self) -> None:
        group = QGroupBox("Lifecycle")
        layout = QVBoxLayout(group)
        self._add_combo(layout, "size_over_life", "Size Over Life",
                        ["constant", "grow", "shrink", "pulse"], "constant")
        self._add_combo(layout, "fade_curve", "Fade Curve",
                        ["linear", "ease_out", "flash"], "linear")

        cb = QCheckBox("Color Over Life")
        cb.setChecked(False)
        cb.toggled.connect(lambda val: self._emit("color_over_life", val))
        layout.addWidget(cb)
        self._widgets["color_over_life"] = cb
        self._layout.addWidget(group)

    def _add_colors_section(self) -> None:
        group = QGroupBox("Colors")
        self._colors_layout = QVBoxLayout(group)

        self._color_inputs: list[QLineEdit] = []
        self._add_color_input("#00ff99")

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+")
        add_btn.setFixedWidth(30)
        add_btn.clicked.connect(lambda: self._add_color_input("#ffffff"))
        remove_btn = QPushButton("-")
        remove_btn.setFixedWidth(30)
        remove_btn.clicked.connect(self._remove_last_color)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch()
        self._colors_layout.addLayout(btn_row)

        self._layout.addWidget(group)

    def _add_export_section(self) -> None:
        group = QGroupBox("Export")
        layout = QVBoxLayout(group)
        self._add_float_spin(layout, "export_duration", "Duration (s)", 1.0, 300.0, 30.0)
        self._add_float_spin(layout, "export_crossfade", "Crossfade (s)", 0.0, 60.0, 10.0)
        self._add_combo(layout, "export_resolution", "Resolution",
                        ["1920x1080", "1280x720", "3840x2160", "640x360"], "1920x1080")
        self._add_int_spin(layout, "export_fps", "FPS", 24, 120, 60)
        self._add_int_spin(layout, "export_crf", "CRF", 0, 51, 18)

        # Output path
        path_row = QHBoxLayout()
        self._output_edit = QLineEdit("particles.mp4")
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(30)
        browse_btn.clicked.connect(self._browse_output)
        path_row.addWidget(QLabel("Output:"))
        path_row.addWidget(self._output_edit)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        self._generate_btn = QPushButton("Generate")
        layout.addWidget(self._generate_btn)

        self._layout.addWidget(group)

    # --- Widget helpers ---

    def _add_float_spin(
        self, layout: QVBoxLayout, key: str, label: str,
        min_val: float, max_val: float, default: float,
        step: float = 0.1, decimals: int = 3,
    ) -> QDoubleSpinBox:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setSingleStep(step)
        spin.setDecimals(decimals)
        spin.valueChanged.connect(lambda val: self._emit(key, val))
        row.addWidget(spin)
        layout.addLayout(row)
        self._widgets[key] = spin
        return spin

    def _add_int_spin(
        self, layout: QVBoxLayout, key: str, label: str,
        min_val: int, max_val: int, default: int,
    ) -> QSpinBox:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.valueChanged.connect(lambda val: self._emit(key, val))
        row.addWidget(spin)
        layout.addLayout(row)
        self._widgets[key] = spin
        return spin

    def _add_combo(
        self, layout: QVBoxLayout, key: str, label: str,
        items: list[str], default: str,
    ) -> QComboBox:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        combo = QComboBox()
        combo.addItems(items)
        combo.setCurrentText(default)
        combo.currentTextChanged.connect(lambda val: self._emit(key, val))
        row.addWidget(combo)
        layout.addLayout(row)
        self._widgets[key] = combo
        return combo

    def _add_color_input(self, color: str) -> None:
        edit = QLineEdit(color)
        edit.setMaxLength(7)
        edit.textChanged.connect(lambda: self._emit_colors())
        idx = len(self._color_inputs)
        self._colors_layout.insertWidget(idx, edit)
        self._color_inputs.append(edit)

    def _remove_last_color(self) -> None:
        if len(self._color_inputs) <= 1:
            return
        edit = self._color_inputs.pop()
        edit.deleteLater()
        self._emit_colors()

    def _emit_colors(self) -> None:
        colors = [e.text() for e in self._color_inputs if e.text().startswith("#")]
        if colors:
            self._emit("colors", colors)

    def _emit(self, key: str, value: object) -> None:
        if not self._block_signals:
            self.params_changed.emit(key, value)

    def _browse_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Output File", "particles.mp4", "MP4 Files (*.mp4)",
        )
        if path:
            self._output_edit.setText(path)

    # --- Public API ---

    @property
    def preset_combo(self) -> QComboBox:
        return self._preset_combo

    @property
    def load_btn(self) -> QPushButton:
        return self._load_btn

    @property
    def save_btn(self) -> QPushButton:
        return self._save_btn

    @property
    def generate_btn(self) -> QPushButton:
        return self._generate_btn

    def collect_export_params(self) -> dict:
        """Collect export-specific parameters."""
        res_str = self._widgets["export_resolution"]
        if isinstance(res_str, QComboBox):
            res_text = res_str.currentText()
        else:
            res_text = "1920x1080"
        w, h = res_text.split("x")
        return {
            "duration": self._widgets["export_duration"].value(),  # type: ignore[union-attr]
            "crossfade": self._widgets["export_crossfade"].value(),  # type: ignore[union-attr]
            "resolution": (int(w), int(h)),
            "fps": self._widgets["export_fps"].value(),  # type: ignore[union-attr]
            "crf": self._widgets["export_crf"].value(),  # type: ignore[union-attr]
            "output": self._output_edit.text(),
        }

    def set_from_preset(self, preset: ParticlePreset) -> None:
        """Update all controls from a preset. Blocks signals during update."""
        self._block_signals = True
        try:
            self._set_widget("max_particles", preset.max_particles)
            self._set_widget("particle_size", preset.particle_size)
            self._set_widget("spawn_rate", preset.spawn_rate)
            self._set_widget("lifetime", preset.lifetime)
            self._set_widget("spread", preset.spread)
            self._set_widget("spawn_mode", preset.spawn_mode)
            self._set_widget("spawn_x", preset.spawn_x)
            self._set_widget("spawn_y", preset.spawn_y)
            self._set_widget("spawn_radius", preset.spawn_radius)
            self._set_widget("gravity_x", preset.gravity_x)
            self._set_widget("gravity_y", preset.gravity_y)
            self._set_widget("speed_min", preset.speed_min)
            self._set_widget("speed_max", preset.speed_max)
            self._set_widget("drag", preset.drag)
            self._set_widget("turbulence", preset.turbulence)
            self._set_widget("radial_force", preset.radial_force)
            self._set_widget("vortex", preset.vortex)
            self._set_widget("size_over_life", preset.size_over_life)
            self._set_widget("fade_curve", preset.fade_curve)

            cb = self._widgets.get("color_over_life")
            if isinstance(cb, QCheckBox):
                cb.setChecked(preset.color_over_life)

            # Update color inputs
            for edit in self._color_inputs[:]:
                edit.deleteLater()
            self._color_inputs.clear()
            for color in preset.colors:
                self._add_color_input(color)
        finally:
            self._block_signals = False

    def _set_widget(self, key: str, value: object) -> None:
        widget = self._widgets.get(key)
        if widget is None:
            return
        if isinstance(widget, QDoubleSpinBox):
            widget.setValue(float(value))  # type: ignore[arg-type]
        elif isinstance(widget, QSpinBox):
            widget.setValue(int(value))  # type: ignore[arg-type]
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(str(value))

"""Parameter sidebar with wavern-style drag spinboxes, color editor, and help buttons."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from particle_gen.gui.color_section import ColorSection
from particle_gen.gui.drag_spinbox import DragSpinBox
from particle_gen.gui.help_button import make_help_button
from particle_gen.presets.schema import ParticlePreset

# Parameter metadata: (key, label, min, max, default, decimals, step, description)
_CORE_PARAMS = [
    ("max_particles", "Max Particles", 100, 10000, 2000, 0, 100,
     "Maximum number of particles alive at once."),
    ("particle_size", "Particle Size", 0.5, 100.0, 4.0, 1, 0.5,
     "Base size of particles in pixels."),
    ("size_min", "Size Min", 0.1, 3.0, 0.5, 1, 0.1,
     "Minimum size multiplier applied to base particle size."),
    ("size_max", "Size Max", 0.1, 3.0, 1.5, 1, 0.1,
     "Maximum size multiplier applied to base particle size."),
    ("spawn_rate", "Spawn Rate", 1.0, 5000.0, 100.0, 1, 10.0,
     "Number of new particles spawned per second."),
    ("lifetime", "Lifetime", 0.1, 30.0, 2.0, 2, 0.1,
     "Average lifetime of each particle in seconds."),
    ("lifetime_min", "Life Min", 0.1, 3.0, 0.5, 1, 0.1,
     "Minimum lifetime multiplier."),
    ("lifetime_max", "Life Max", 0.1, 3.0, 1.5, 1, 0.1,
     "Maximum lifetime multiplier."),
    ("spread", "Spread", 0.01, 5.0, 0.5, 2, 0.05,
     "Velocity spread multiplier at spawn."),
]

_SPAWN_PARAMS = [
    ("spawn_x", "Spawn X", -0.25, 1.25, 0.5, 3, 0.01,
     "Horizontal spawn position (0=left, 1=right). Values outside 0–1 spawn off-screen."),
    ("spawn_y", "Spawn Y", -0.25, 1.25, 0.5, 3, 0.01,
     "Vertical spawn position (0=bottom, 1=top). Values outside 0–1 spawn off-screen."),
    ("spawn_radius", "Radius", 0.01, 1.0, 0.3, 3, 0.01,
     "Spawn radius for circle mode."),
]

_PHYSICS_PARAMS = [
    ("gravity_x", "Gravity X", -1.0, 1.0, 0.0, 3, 0.01,
     "Horizontal gravity force."),
    ("gravity_y", "Gravity Y", -5.0, 5.0, -0.1, 3, 0.01,
     "Vertical gravity force. Negative = downward."),
    ("speed_min", "Speed Min", 0.01, 0.5, 0.05, 3, 0.01,
     "Minimum initial speed of spawned particles."),
    ("speed_max", "Speed Max", 0.1, 1.0, 0.3, 3, 0.01,
     "Maximum initial speed of spawned particles."),
    ("drag", "Drag", 0.0, 0.99, 0.0, 3, 0.01,
     "Velocity damping per frame. Higher = more slowdown."),
    ("turbulence", "Turbulence", 0.0, 1.0, 0.0, 3, 0.01,
     "Noise-driven random perturbation strength."),
    ("radial_force", "Radial Force", -1.0, 1.0, 0.0, 3, 0.01,
     "Positive = repel from spawn, negative = attract."),
    ("vortex", "Vortex", -1.0, 1.0, 0.0, 3, 0.01,
     "Rotational force around spawn point."),
]

_EXPORT_PARAMS = [
    ("export_duration", "Duration (s)", 1.0, 300.0, 30.0, 1, 1.0,
     "Total video length in seconds."),
    ("export_crossfade", "Crossfade (s)", 0.0, 60.0, 10.0, 1, 1.0,
     "Loop overlap duration. Must be < duration/2."),
]


class Sidebar(QScrollArea):
    """Scrollable sidebar with grouped particle parameter controls."""

    params_changed = Signal(str, object)

    def __init__(self) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.setMinimumWidth(340)
        self._block_signals = False

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setSpacing(6)
        self._layout.setContentsMargins(6, 6, 6, 6)

        self._widgets: dict[str, DragSpinBox | QComboBox | QCheckBox] = {}

        self._add_preset_section()
        self._add_reset_all_button()
        self._add_param_group("Core", _CORE_PARAMS)
        self._add_spawn_section()
        self._add_shapes_section()
        self._add_param_group("Physics", _PHYSICS_PARAMS)
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

    def _add_reset_all_button(self) -> None:
        btn = QPushButton("\u21BA Reset All to Defaults")
        btn.setObjectName("ResetAllButton")
        btn.clicked.connect(self._on_reset_all)
        self._layout.addWidget(btn)

    def _add_param_group(self, title: str, params: list[tuple]) -> None:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        for key, label, min_v, max_v, default, decimals, step, desc in params:
            lbl = QLabel(label)
            lbl.setObjectName("ParamLabel")
            layout.addWidget(lbl)
            dsb = DragSpinBox(
                minimum=float(min_v),
                maximum=float(max_v),
                step=float(step),
                decimals=decimals,
                description=desc,
                default_value=float(default),
            )
            dsb.setValue(float(default))
            dsb.valueChanged.connect(lambda val, k=key: self._emit(k, val))
            layout.addWidget(dsb)
            self._widgets[key] = dsb
        self._layout.addWidget(group)

    def _add_spawn_section(self) -> None:
        group = QGroupBox("Spawn")
        layout = QVBoxLayout(group)

        # Spawn mode combo
        mode_row = QHBoxLayout()
        mode_label = QLabel("Mode")
        mode_label.setObjectName("ParamLabel")
        mode_row.addWidget(mode_label)
        combo = QComboBox()
        combo.addItems(["point", "line", "circle", "edges", "random"])
        combo.setCurrentText("point")
        combo.currentTextChanged.connect(lambda val: self._emit("spawn_mode", val))
        mode_row.addWidget(combo)
        mode_row.addWidget(make_help_button("Particle spawn pattern: point, line, circle, edges, or random."))
        layout.addLayout(mode_row)
        self._widgets["spawn_mode"] = combo

        for key, label, min_v, max_v, default, decimals, step, desc in _SPAWN_PARAMS:
            lbl = QLabel(label)
            lbl.setObjectName("ParamLabel")
            layout.addWidget(lbl)
            dsb = DragSpinBox(
                minimum=float(min_v),
                maximum=float(max_v),
                step=float(step),
                decimals=decimals,
                description=desc,
                default_value=float(default),
            )
            dsb.setValue(float(default))
            dsb.valueChanged.connect(lambda val, k=key: self._emit(k, val))
            layout.addWidget(dsb)
            self._widgets[key] = dsb
        self._layout.addWidget(group)

    _SHAPE_BTN_STYLE_ON = (
        "QPushButton { background-color: #0078d4; color: #fff; border: 1px solid #0078d4; }"
    )
    _SHAPE_BTN_STYLE_OFF = (
        "QPushButton { background-color: #3c3c3c; color: #888; border: 1px solid #555; }"
    )

    def _add_shapes_section(self) -> None:
        group = QGroupBox("Shapes")
        layout = QVBoxLayout(group)

        self._shape_buttons: dict[str, QPushButton] = {}
        btn_layout = QHBoxLayout()
        for shape_name in ["circle", "square", "triangle", "diamond", "star", "ring"]:
            btn = QPushButton(shape_name.capitalize())
            btn.setCheckable(True)
            btn.setChecked(shape_name == "circle")
            btn.clicked.connect(
                lambda checked, s=shape_name: self._on_shape_toggled(s, checked)
            )
            btn_layout.addWidget(btn)
            self._shape_buttons[shape_name] = btn
        layout.addLayout(btn_layout)
        self._update_shape_styles()
        self._layout.addWidget(group)

    def _update_shape_styles(self) -> None:
        for btn in self._shape_buttons.values():
            btn.setStyleSheet(
                self._SHAPE_BTN_STYLE_ON if btn.isChecked() else self._SHAPE_BTN_STYLE_OFF
            )

    def _on_shape_toggled(self, shape: str, checked: bool) -> None:
        selected = [s for s, btn in self._shape_buttons.items() if btn.isChecked()]
        if not selected:
            self._shape_buttons[shape].setChecked(True)
            return
        self._update_shape_styles()
        self._emit("particle_shapes", selected)

    def _add_lifecycle_section(self) -> None:
        group = QGroupBox("Lifecycle")
        layout = QVBoxLayout(group)

        # size_over_life combo
        sol_row = QHBoxLayout()
        sol_label = QLabel("Size Over Life")
        sol_label.setObjectName("ParamLabel")
        sol_row.addWidget(sol_label)
        sol_combo = QComboBox()
        sol_combo.addItems(["constant", "grow", "shrink", "pulse"])
        sol_combo.setCurrentText("constant")
        sol_combo.currentTextChanged.connect(lambda val: self._emit("size_over_life", val))
        sol_row.addWidget(sol_combo)
        sol_row.addWidget(make_help_button("How particle size changes over its lifetime."))
        layout.addLayout(sol_row)
        self._widgets["size_over_life"] = sol_combo

        # fade_curve combo
        fc_row = QHBoxLayout()
        fc_label = QLabel("Fade Curve")
        fc_label.setObjectName("ParamLabel")
        fc_row.addWidget(fc_label)
        fc_combo = QComboBox()
        fc_combo.addItems(["linear", "ease_out", "flash"])
        fc_combo.setCurrentText("linear")
        fc_combo.currentTextChanged.connect(lambda val: self._emit("fade_curve", val))
        fc_row.addWidget(fc_combo)
        fc_row.addWidget(make_help_button("Alpha fade curve shape over particle lifetime."))
        layout.addLayout(fc_row)
        self._widgets["fade_curve"] = fc_combo

        # color_over_life checkbox
        cb_row = QHBoxLayout()
        cb = QCheckBox("Color Over Life")
        cb.setChecked(False)
        cb.toggled.connect(lambda val: self._emit("color_over_life", val))
        cb_row.addWidget(cb)
        cb_row.addWidget(make_help_button("Shift through color palette over particle lifetime."))
        layout.addLayout(cb_row)
        self._widgets["color_over_life"] = cb

        self._layout.addWidget(group)

    def _add_colors_section(self) -> None:
        group = QGroupBox("Colors")
        layout = QVBoxLayout(group)

        self._color_section = ColorSection()
        self._color_section.build(["#00ff99"])
        self._color_section.colors_changed.connect(
            lambda colors: self._emit("colors", colors)
        )
        layout.addWidget(self._color_section)

        self._layout.addWidget(group)

    def _add_export_section(self) -> None:
        group = QGroupBox("Export")
        layout = QVBoxLayout(group)

        for key, label, min_v, max_v, default, decimals, step, desc in _EXPORT_PARAMS:
            lbl = QLabel(label)
            lbl.setObjectName("ParamLabel")
            layout.addWidget(lbl)
            dsb = DragSpinBox(
                minimum=float(min_v),
                maximum=float(max_v),
                step=float(step),
                decimals=decimals,
                description=desc,
                default_value=float(default),
            )
            dsb.setValue(float(default))
            layout.addWidget(dsb)
            self._widgets[key] = dsb

        # Resolution combo
        res_row = QHBoxLayout()
        res_label = QLabel("Resolution")
        res_label.setObjectName("ParamLabel")
        res_row.addWidget(res_label)
        res_combo = QComboBox()
        res_combo.addItems(["1920x1080", "2560x1440", "1280x720", "3840x2160", "640x360"])
        res_combo.setCurrentText("1920x1080")
        res_row.addWidget(res_combo)
        layout.addLayout(res_row)
        self._widgets["export_resolution"] = res_combo

        # FPS
        fps_label = QLabel("FPS")
        fps_label.setObjectName("ParamLabel")
        layout.addWidget(fps_label)
        fps_dsb = DragSpinBox(minimum=24, maximum=120, step=1, decimals=0,
                              description="Frames per second.", default_value=60)
        fps_dsb.setValue(60)
        layout.addWidget(fps_dsb)
        self._widgets["export_fps"] = fps_dsb

        # CRF
        crf_label = QLabel("CRF")
        crf_label.setObjectName("ParamLabel")
        layout.addWidget(crf_label)
        crf_dsb = DragSpinBox(minimum=0, maximum=51, step=1, decimals=0,
                              description="H.264 quality (lower = better, 18 recommended).",
                              default_value=18)
        crf_dsb.setValue(18)
        layout.addWidget(crf_dsb)
        self._widgets["export_crf"] = crf_dsb

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

    # --- Helpers ---

    def _emit(self, key: str, value: object) -> None:
        if not self._block_signals:
            self.params_changed.emit(key, value)

    def _browse_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Output File", "particles.mp4", "MP4 Files (*.mp4)",
        )
        if path:
            self._output_edit.setText(path)

    def _on_reset_all(self) -> None:
        """Reset all parameters to their defaults."""
        default = ParticlePreset(name="default", description="Default preset")
        self.set_from_preset(default)
        # Emit changes for each param so the preview updates
        self._emit_all_params(default)

    def _emit_all_params(self, preset: ParticlePreset) -> None:
        """Emit params_changed for every parameter from a preset."""
        for key in (
            "max_particles", "particle_size", "size_min", "size_max",
            "spawn_rate", "lifetime", "lifetime_min", "lifetime_max", "spread",
            "spawn_mode", "spawn_x", "spawn_y", "spawn_radius",
            "particle_shapes",
            "gravity_x", "gravity_y", "speed_min", "speed_max",
            "drag", "turbulence", "radial_force", "vortex",
            "size_over_life", "fade_curve", "color_over_life", "colors",
        ):
            self.params_changed.emit(key, getattr(preset, key))

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
        res_widget = self._widgets["export_resolution"]
        if isinstance(res_widget, QComboBox):
            res_text = res_widget.currentText()
        else:
            res_text = "1920x1080"
        w, h = res_text.split("x")

        dur_widget = self._widgets["export_duration"]
        cf_widget = self._widgets["export_crossfade"]
        fps_widget = self._widgets["export_fps"]
        crf_widget = self._widgets["export_crf"]

        return {
            "duration": dur_widget.value() if isinstance(dur_widget, DragSpinBox) else 30.0,
            "crossfade": cf_widget.value() if isinstance(cf_widget, DragSpinBox) else 10.0,
            "resolution": (int(w), int(h)),
            "fps": int(fps_widget.value()) if isinstance(fps_widget, DragSpinBox) else 60,
            "crf": int(crf_widget.value()) if isinstance(crf_widget, DragSpinBox) else 18,
            "output": self._output_edit.text(),
        }

    def set_from_preset(self, preset: ParticlePreset) -> None:
        """Update all controls from a preset. Blocks signals during update."""
        self._block_signals = True
        try:
            self._set_dsb("max_particles", preset.max_particles)
            self._set_dsb("particle_size", preset.particle_size)
            self._set_dsb("spawn_rate", preset.spawn_rate)
            self._set_dsb("lifetime", preset.lifetime)
            self._set_dsb("spread", preset.spread)
            self._set_combo("spawn_mode", preset.spawn_mode)
            self._set_dsb("spawn_x", preset.spawn_x)
            self._set_dsb("spawn_y", preset.spawn_y)
            self._set_dsb("spawn_radius", preset.spawn_radius)
            self._set_dsb("gravity_x", preset.gravity_x)
            self._set_dsb("gravity_y", preset.gravity_y)
            self._set_dsb("speed_min", preset.speed_min)
            self._set_dsb("speed_max", preset.speed_max)
            self._set_dsb("drag", preset.drag)
            self._set_dsb("turbulence", preset.turbulence)
            self._set_dsb("radial_force", preset.radial_force)
            self._set_dsb("vortex", preset.vortex)
            self._set_dsb("size_min", preset.size_min)
            self._set_dsb("size_max", preset.size_max)
            self._set_dsb("lifetime_min", preset.lifetime_min)
            self._set_dsb("lifetime_max", preset.lifetime_max)
            self._set_combo("size_over_life", preset.size_over_life)
            self._set_combo("fade_curve", preset.fade_curve)

            for shape_name, btn in self._shape_buttons.items():
                btn.setChecked(shape_name in preset.particle_shapes)
            self._update_shape_styles()

            cb = self._widgets.get("color_over_life")
            if isinstance(cb, QCheckBox):
                cb.setChecked(preset.color_over_life)

            self._color_section.build(preset.colors)
        finally:
            self._block_signals = False

    def _set_dsb(self, key: str, value: float | int) -> None:
        widget = self._widgets.get(key)
        if isinstance(widget, DragSpinBox):
            widget.setValue(float(value))

    def _set_combo(self, key: str, value: str) -> None:
        widget = self._widgets.get(key)
        if isinstance(widget, QComboBox):
            widget.setCurrentText(value)

"""Color palette editor section with swatches, color picker, and reorder controls."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ColorSection(QWidget):
    """Editable color palette widget with add/remove/reorder controls."""

    colors_changed = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._color_buttons: list[QPushButton] = []
        self._colors: list[str] = []
        self._rebuilding = False

    def build(self, colors: list[str]) -> None:
        """Clear and rebuild the color palette rows."""
        self._rebuilding = True
        self._colors = list(colors)
        self._color_buttons.clear()

        # Remove all existing child widgets
        while self._layout.count():
            item = self._layout.takeAt(0)
            assert item is not None
            w = item.widget()
            if w is not None:
                w.deleteLater()
            else:
                sub = item.layout()
                if sub is not None and isinstance(sub, (QVBoxLayout, QHBoxLayout)):
                    _clear_layout(sub)

        for i, color_hex in enumerate(self._colors):
            row = QHBoxLayout()

            up_btn = QPushButton("\u25B2")
            up_btn.setObjectName("ColorControlBtn")
            up_btn.setFixedSize(24, 24)
            up_btn.setEnabled(i > 0)
            up_btn.clicked.connect(lambda _, idx=i: self._on_move_up(idx))
            row.addWidget(up_btn)

            down_btn = QPushButton("\u25BC")
            down_btn.setObjectName("ColorControlBtn")
            down_btn.setFixedSize(24, 24)
            down_btn.setEnabled(i < len(self._colors) - 1)
            down_btn.clicked.connect(lambda _, idx=i: self._on_move_down(idx))
            row.addWidget(down_btn)

            btn = QPushButton()
            btn.setFixedSize(30, 30)
            btn.setStyleSheet(
                f"background-color: {color_hex}; border: 1px solid #555;"
            )
            btn.clicked.connect(lambda _, idx=i: self._on_color_clicked(idx))
            row.addWidget(btn)

            label = QLabel(color_hex)
            row.addWidget(label)

            remove_btn = QPushButton("x")
            remove_btn.setObjectName("ColorControlBtn")
            remove_btn.setFixedSize(24, 24)
            remove_btn.clicked.connect(lambda _, idx=i: self._on_remove(idx))
            row.addWidget(remove_btn)

            row_widget = QWidget()
            row_widget.setLayout(row)
            self._layout.addWidget(row_widget)
            self._color_buttons.append(btn)

        add_btn = QPushButton("+ Add Color")
        add_btn.clicked.connect(self._on_add)
        self._layout.addWidget(add_btn)

        self._rebuilding = False

    def get_colors(self) -> list[str]:
        """Return current color list."""
        return list(self._colors)

    def _emit(self) -> None:
        if not self._rebuilding:
            self.colors_changed.emit(list(self._colors))

    def _on_color_clicked(self, index: int) -> None:
        from PySide6.QtGui import QColor

        current = QColor(self._colors[index])
        color = QColorDialog.getColor(current, self, "Pick Color")
        if color.isValid():
            hex_color = color.name().upper()
            self._colors[index] = hex_color
            self._color_buttons[index].setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid #555;"
            )
            self._emit()

    def _on_add(self) -> None:
        color = QColorDialog.getColor(parent=self, title="Add Color")
        if color.isValid():
            self._colors.append(color.name().upper())
            self.build(self._colors)
            self._emit()

    def _on_remove(self, index: int) -> None:
        if len(self._colors) <= 1:
            return
        self._colors.pop(index)
        self.build(self._colors)
        self._emit()

    def _on_move_up(self, index: int) -> None:
        if index <= 0:
            return
        self._colors[index], self._colors[index - 1] = (
            self._colors[index - 1], self._colors[index],
        )
        self.build(self._colors)
        self._emit()

    def _on_move_down(self, index: int) -> None:
        if index >= len(self._colors) - 1:
            return
        self._colors[index], self._colors[index + 1] = (
            self._colors[index + 1], self._colors[index],
        )
        self.build(self._colors)
        self._emit()


def _clear_layout(layout: QVBoxLayout | QHBoxLayout) -> None:
    """Recursively remove all items from a layout and delete their widgets."""
    while layout.count():
        item = layout.takeAt(0)
        assert item is not None
        w = item.widget()
        if w is not None:
            w.deleteLater()
        else:
            sub = item.layout()
            if sub is not None and isinstance(sub, (QVBoxLayout, QHBoxLayout)):
                _clear_layout(sub)

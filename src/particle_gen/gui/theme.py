"""Dark theme stylesheet for Particlops GUI."""

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #ddd;
}

QGroupBox {
    border: 1px solid #444;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 16px;
    font-weight: bold;
    color: #ccc;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}

QScrollArea {
    background-color: #2a2a2a;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: #2a2a2a;
}

QComboBox {
    background-color: #3c3c3c;
    color: #ddd;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 4px 8px;
    min-height: 22px;
}

QComboBox:hover {
    border-color: #0078d4;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #2a2a2a;
    color: #ddd;
    selection-background-color: #0078d4;
    border: 1px solid #555;
}

QPushButton {
    background-color: #3c3c3c;
    color: #ddd;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 5px 12px;
    min-height: 22px;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #0078d4;
}

QPushButton:pressed {
    background-color: #0078d4;
}

QPushButton#HelpButton {
    border-radius: 10px;
    border: 1px solid #555;
    background: #333;
    color: #aaa;
    font-weight: bold;
    font-size: 11px;
    padding: 0;
}

QPushButton#HelpButton:hover {
    background: #555;
    color: #fff;
}

QPushButton#ResetButton {
    border-radius: 10px;
    border: 1px solid #555;
    background: #333;
    color: #aaa;
    font-size: 13px;
    padding: 0;
}

QPushButton#ResetButton:hover {
    background: #555;
    color: #fff;
}

QPushButton#ColorControlBtn {
    border-radius: 3px;
    border: 1px solid #555;
    background: #333;
    color: #aaa;
    font-size: 12px;
    padding: 0;
}

QPushButton#ColorControlBtn:hover {
    background: #555;
    color: #fff;
}

QPushButton#ColorControlBtn:disabled {
    color: #444;
    background: #2a2a2a;
}

QPushButton#ResetAllButton {
    background-color: #333;
    color: #aaa;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 4px 10px;
}

QPushButton#ResetAllButton:hover {
    background: #555;
    color: #fff;
}

QLabel {
    color: #ddd;
    background: transparent;
}

QLabel#ParamLabel {
    color: #bbb;
    font-size: 12px;
}

QLineEdit {
    background-color: #2a2a2a;
    color: #ddd;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 3px 6px;
    selection-background-color: #0078d4;
}

QLineEdit:focus {
    border-color: #0078d4;
}

QCheckBox {
    color: #ddd;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555;
    border-radius: 3px;
    background-color: #3c3c3c;
}

QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}

QProgressDialog {
    background-color: #2a2a2a;
}

QSplitter::handle {
    background-color: #333;
    width: 3px;
}

QScrollBar:vertical {
    background: #2a2a2a;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #555;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #777;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""

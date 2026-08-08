LIGHT_STYLE = """
* { font-family: "Segoe UI", "Inter", sans-serif; font-size: 13px; color: #243247; }
QMainWindow, QWidget#content { background: #f5f7fb; }
QFrame#sidebar { background: #17243b; border: 0; }
QLabel#brand { color: #ffffff; font-size: 22px; font-weight: 800; letter-spacing: 2px; }
QLabel#tagline { color: #93a4bd; font-size: 12px; }
QLabel#versionLabel { color: #71839d; font-size: 11px; padding: 4px; }
QLabel#navTitle { color: #71839d; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
QLabel#navItem, QLabel#navActive { padding: 11px 12px; border-radius: 7px; }
QLabel#navItem { color: #aab7ca; }
QLabel#navActive { color: #ffffff; background: #243754; font-weight: 600;
                   border-left: 3px solid #57c6ff; }
QLabel#pageTitle { color: #17243b; font-size: 26px; font-weight: 750; }
QLabel#pageSubtitle { color: #708096; }
QGroupBox { font-weight: 650; border: 1px solid #e1e7ef; border-radius: 10px;
            margin-top: 9px; padding-top: 10px; background: #ffffff; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 5px; color: #31425a; }
QLineEdit, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTableWidget {
    border: 1px solid #d8e0ea; border-radius: 6px; padding: 7px; background: #ffffff;
}
QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 1px solid #2684ff; }
QPushButton { border: 0; border-radius: 6px; padding: 8px 15px;
              background: #e8edf4; font-weight: 550; }
QPushButton:hover { background: #dce4ee; }
QPushButton#primary { color: white; background: #1677ff; font-weight: 650; padding: 9px 20px; }
QPushButton#primary:hover { background: #0868e4; }
QPushButton#secondary { color: #1769d2; background: #e7f1ff; padding: 9px 20px; }
QPushButton#sidebarButton { color: #cbd6e5; background: #243754;
                            text-align: left; padding: 10px 12px; }
QPushButton#sidebarButton:hover { color: #ffffff; background: #304765; }
QPushButton:disabled { color: #8993a3; background: #edf0f4; }
QFrame#statCard, QFrame#panel { background: #ffffff; border: 1px solid #e1e7ef;
                               border-radius: 10px; }
QLabel#statValue { color: #17243b; font-size: 17px; font-weight: 700; }
QLabel#panelTitle { color: #26364d; font-size: 14px; font-weight: 700; }
QLabel#engineStatus { font-size: 12px; }
QLabel#engineStatus[state="ready"] { color: #16845b; }
QLabel#engineStatus[state="fallback"] { color: #b26a00; }
QTableWidget#fileTable { border-radius: 10px; gridline-color: #edf1f6;
                         alternate-background-color: #f8fafd; }
QHeaderView::section { color: #526279; background: #eef3f8; border: 0;
                       border-bottom: 1px solid #dce4ed; padding: 8px; font-weight: 650; }
QProgressBar { min-height: 10px; max-height: 10px; border: 0; border-radius: 5px;
               text-align: center; color: transparent; background: #e7edf5; }
QProgressBar::chunk { background: #20b486; border-radius: 5px; }
QPlainTextEdit { color: #536176; background: #f8fafd; }
"""

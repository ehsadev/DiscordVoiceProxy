import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.utils.logging import configure_logging

STYLE = """
QMainWindow,QWidget{background:#0f1115;color:#e7e9ee;font-family:'Segoe UI';font-size:10pt}
#Title{font-size:24pt;font-weight:700} #Subtitle{color:#9299a8;font-size:11pt;margin-bottom:8px}
QGroupBox{border:1px solid #292e39;border-radius:12px;margin-top:8px;padding:16px;color:#aeb5c3} QGroupBox::title{subcontrol-origin:margin;left:14px;padding:0 6px}
#Card{background:#171a21;border:1px solid #292e39;border-radius:12px} #CardTitle{font-size:9pt;color:#858d9d;font-weight:700} #CardStatus{font-size:13pt;font-weight:700} #CardDetail{color:#7e8797;font-size:9pt}
#CardStatus[kind='good']{color:#55d187} #CardStatus[kind='bad']{color:#ff6b78} #CardStatus[kind='warn']{color:#f2bd58} #CardStatus[kind='neutral']{color:#b9c0cd}
QLineEdit,QSpinBox{background:#14171d;border:1px solid #303642;border-radius:8px;padding:9px;color:#fff} QPushButton{background:#5865f2;border:0;border-radius:8px;padding:10px 16px;color:white;font-weight:600} QPushButton:hover{background:#6975ff} QPushButton:disabled{background:#292e39;color:#666d7b} QPushButton#Secondary{background:#252a34} QProgressBar{height:8px;border:0;border-radius:4px;background:#252a34} QProgressBar::chunk{background:#5865f2;border-radius:4px} #StatusBar{background:#171a21;border:1px solid #292e39;border-radius:8px;padding:10px;color:#aeb5c3} #copywrite{background:#171a21;border:1px solid #292e39;border-radius:8px;padding:6px;color:#aeb5c3}
"""

def resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative_path

    return Path(__file__).resolve().parent.parent / relative_path



def main():
    
    logger = configure_logging()
    logger.info("startup")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(resource_path("assets/icon.ico"))))
    app.setStyleSheet(STYLE)
    win = MainWindow(logger)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

from PySide6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from app.models.proxy import ProxyConfiguration


class ProxyConfigWidget(QWidget):
    def __init__(self):
        super().__init__()
        f = QFormLayout(self)
        f.setContentsMargins(0, 0, 0, 0)
        self.host = QLineEdit("127.0.0.1")
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(10808)
        self.user = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.detect = QPushButton("Detect Proxy")
        f.addRow("SOCKS5 Address", self.host)
        f.addRow("Port", self.port)
        f.addRow("Username", self.user)
        f.addRow("Password", self.password)
        f.addRow("", self.detect)

    def configuration(self):
        return ProxyConfiguration(
            self.host.text().strip(),
            self.port.value(),
            self.user.text().strip() or None,
            self.password.text() or None,
        )

    def set_configuration(self, cfg):
        self.host.setText(cfg.host)
        self.port.setValue(cfg.port)
        self.user.setText(cfg.username or "")
        self.password.setText(cfg.password or "")

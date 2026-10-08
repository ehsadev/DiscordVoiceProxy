from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatusCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("Card")
        l = QVBoxLayout(self)
        l.setContentsMargins(18, 14, 18, 14)
        l.setSpacing(4)
        self.title = QLabel(title)
        self.title.setObjectName("CardTitle")
        self.status = QLabel("Checking…")
        self.status.setObjectName("CardStatus")
        self.detail = QLabel("")
        self.detail.setObjectName("CardDetail")
        l.addWidget(self.title)
        l.addWidget(self.status)
        l.addWidget(self.detail)

    def set_status(self, text, kind="neutral", detail=""):
        self.status.setText(text)
        self.status.setProperty("kind", kind)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.detail.setText(detail)

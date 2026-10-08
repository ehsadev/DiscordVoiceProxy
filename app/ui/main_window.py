import time
import logging
from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.proxy import ProxyState
from app.proxy_detection import ProxyDetectionService
from app.services.discord_service import DiscordService
from app.services.dotnet_service import DotNetService
from app.services.launcher_service import LauncherService
from app.services.proxy_service import ProxyService

from .proxy_config import ProxyConfigWidget
from .status_card import StatusCard
from .workers import Worker


class MainWindow(QMainWindow):
    def __init__(self, logger: logging.Logger):
        super().__init__()
        self.logger = logger
        self.pool = QThreadPool.globalInstance()
        self.discord = DiscordService()
        self.dotnet_service = DotNetService()
        self.proxy = ProxyService()
        self.launcher = LauncherService()
        self.detector = ProxyDetectionService()
        self.setWindowTitle("Discord Voice Proxy Manager")
        self.resize(820, 760)
        self._build()
        self.refresh()

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        title = QLabel("Discord Voice Proxy Manager")
        title.setObjectName("Title")
        sub = QLabel("Route Discord voice traffic through a SOCKS5 proxy")
        sub.setObjectName("Subtitle")
        layout.addWidget(title)
        layout.addWidget(sub)
        cards = QHBoxLayout()
        self.discord_card = StatusCard("DISCORD")
        self.runtime_card = StatusCard(".NET 8 RUNTIME")
        self.proxy_card = StatusCard("PROXY")
        cards.addWidget(self.discord_card)
        cards.addWidget(self.runtime_card)
        cards.addWidget(self.proxy_card)
        layout.addLayout(cards)
        group = QGroupBox("Proxy Configuration")
        gl = QVBoxLayout(group)
        self.config = ProxyConfigWidget()
        gl.addWidget(self.config)
        layout.addWidget(group)
        actions = QHBoxLayout()
        self.install = QPushButton("Install Proxy")
        self.remove = QPushButton("Remove Proxy")
        self.recheck = QPushButton("Recheck Status")
        self.normal = QPushButton("Launch Discord Normally")
        self.with_proxy = QPushButton("Launch Discord With Proxy")
        self.install.setStyleSheet("""
            QPushButton {
                background-color: #5865F2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
            QPushButton:pressed {
                background-color: #3C45A5;
            }
        """)
        self.remove.setStyleSheet("""
            QPushButton {
                background-color: #ED4245;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #C73537;
            }
            QPushButton:pressed {
                background-color: #A82B2D;
            }
        """)

        self.recheck.setStyleSheet("""
            QPushButton {
                background-color: #4F545C;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5D626A;
            }
            QPushButton:pressed {
                background-color: #40444B;
            }
        """)

        # self.normal.setStyleSheet("""
        #     QPushButton {
        #         background-color: #2F3136;
        #         color: #FFFFFF;
        #         border: 1px solid #4F545C;
        #         border-radius: 8px;
        #         padding: 10px 16px;
        #         font-weight: 600;
        #     }
        #     QPushButton:hover {
        #         background-color: #40444B;
        #     }
        #     QPushButton:pressed {
        #         background-color: #292B2F;
        #     }
        # """)

        # self.with_proxy.setStyleSheet("""
        #     QPushButton {
        #         background-color: #3BA55D;
        #         color: white;
        #         border: none;
        #         border-radius: 8px;
        #         padding: 10px 16px;
        #         font-weight: 600;
        #     }
        #     QPushButton:hover {
        #         background-color: #2D8548;
        #     }
        #     QPushButton:pressed {
        #         background-color: #246B3A;
        #     }
        # """)
        actions.addWidget(self.install)
        actions.addWidget(self.remove)
        actions.addWidget(self.recheck)
        layout.addLayout(actions)
        launch = QHBoxLayout()

        launch.addWidget(self.normal)
        launch.addWidget(self.with_proxy)
        layout.addLayout(launch)
        self.dotnet_button = QPushButton("Install .NET 8 Runtime")
        self.dotnet_button.setObjectName("Secondary")
        layout.addWidget(self.dotnet_button)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)
        self.status = QLabel("Status: Ready")
        self.status.setObjectName("StatusBar")
        layout.addWidget(self.status)
        self.copywrite = QLabel("DevByEhsan 2026 - Licensed under MIT")
        self.copywrite.setObjectName("copywrite")
        layout.addWidget(self.copywrite)
        self.install.clicked.connect(self.install_proxy)
        self.remove.clicked.connect(self.remove_proxy)
        self.recheck.clicked.connect(self.refresh)
        self.normal.clicked.connect(lambda: self.launch(False))
        self.with_proxy.clicked.connect(lambda: self.launch(True))
        self.config.detect.clicked.connect(self.detect_proxy)
        self.dotnet_button.clicked.connect(self.install_dotnet)

    def set_busy(self, busy, msg):
        for w in [
            self.install,
            self.remove,
            self.recheck,
            self.normal,
            self.with_proxy,
            self.dotnet_button,
            self.config.detect,
        ]:
            w.setEnabled(not busy)
        self.progress.setVisible(busy)
        self.status.setText("Status: " + msg)

    def refresh(self):
        inst = self.discord.get_installation()
        running = self.discord.is_discord_running()
        rt = self.dotnet_service.status()
        ps = self.proxy.status(inst.app_directory if inst else None)
        self.discord_card.set_status(
            "● Detected" if inst else "● Not Detected",
            "good" if inst else "bad",
            f"Version: {inst.version}" if inst else "Discord installation not found",
        )
        self.runtime_card.set_status(
            "● Installed" if rt.installed else "● Not Installed",
            "good" if rt.installed else "bad",
            rt.version or "Microsoft.NETCore.App 8.x required",
        )
        labels = {
            ProxyState.INSTALLED: ("● Enabled", "good"),
            ProxyState.NOT_INSTALLED: ("● Not Installed", "neutral"),
            ProxyState.PARTIAL: ("⚠ Needs Repair", "warn"),
            ProxyState.INVALID_CONFIGURATION: ("⚠ Invalid Configuration", "warn"),
        }
        txt, kind = labels.get(ps.state, ("⚠ Needs Repair", "warn"))
        self.proxy_card.set_status(txt, kind, ps.message or (ps.directory or ""))
        self.install.setEnabled(bool(inst and not running))
        self.remove.setEnabled(
            bool(
                inst
                and not running
                and ps.state
                in (
                    ProxyState.INSTALLED,
                    ProxyState.PARTIAL,
                    ProxyState.INVALID_CONFIGURATION,
                )
            )
        )
        self.normal.setEnabled(bool(inst and not running))
        self.with_proxy.setEnabled(
            bool(
                inst
                and not running
                and rt.installed
                and ps.state == ProxyState.INSTALLED
            )
        )
        self.dotnet_button.setEnabled(not rt.installed)

    def run_worker(self, fn, done=None, msg="Working…"):
        self.set_busy(True, msg)
        w = Worker(fn)
        w.signals.result.connect(done or (lambda _: None))
        w.signals.error.connect(self.on_error)
        w.signals.finished.connect(
            lambda: self.set_busy(False, "Ready") or self.refresh()
        )
        w.signals.progress.connect(self.progress.setValue)
        self.pool.start(w)

    def on_error(self, e):
        self.logger.exception(e)
        QMessageBox.critical(self, "Operation failed", e)
        self.status.setText("Status: Operation failed")

    def install_proxy(self):
        inst = self.discord.get_installation()
        if not inst:
            return
        if not self.config.host.text().strip():
            QMessageBox.warning(self, "Proxy configuration", "Enter a SOCKS5 address.")
            return
        cfg = self.config.configuration()
        self.run_worker(
            lambda progress=None: self.proxy.install(inst.app_directory, cfg, progress),
            msg="Installing proxy…",
        )

    def remove_proxy(self):
        inst = self.discord.get_installation()
        if not inst:
            return
        if (
            QMessageBox.question(
                self,
                "Remove Proxy",
                "Remove the proxy installation and restore backed-up files?",
            )
            == QMessageBox.Yes
        ):
            self.run_worker(
                lambda progress=None: self.proxy.remove(inst.app_directory),
                msg="Removing proxy…",
            )

    def detect_proxy(self):

        self.set_busy(True, "Detecting proxy…")

        w = Worker(self.detector.detect)

        w.signals.result.connect(self._proxy_detected)

        w.signals.error.connect(self.on_error)

        w.signals.finished.connect(lambda: self.set_busy(False, "Ready"))

        self.pool.start(w)

    def _proxy_detected(self, result):
        name, cfg = result
        if cfg:
            self.config.set_configuration(cfg)
            self.status.setText(
                f"Status: Detected {name} proxy at {cfg.host}:{cfg.port}"
            )
        else:
            self.status.setText("Status: No supported local SOCKS5 proxy detected")

    def install_dotnet(self):
        import tempfile

        path = Path(tempfile.gettempdir()) / "dotnet-runtime-8-x64.exe"

        def work(progress=None):
            self.dotnet_service.download_installer(path, progress)
            return self.dotnet_service.install_and_verify(path)

        self.run_worker(work, self._dotnet_installed, "Installing .NET 8 Runtime…")

    def _dotnet_installed(self, status):
        QMessageBox.information(
            self,
            ".NET 8 Runtime",
            f".NET 8 Runtime installed successfully.\n\nDetected: Microsoft.NETCore.App {status.version}",
        )

    def launch(self, with_proxy):
        inst = self.discord.get_installation()
        if not inst:
            return
        if (
            with_proxy
            and self.proxy.status(inst.app_directory).state != ProxyState.INSTALLED
        ):
            return
        try:
            self.launcher.launch(inst.executable)
            self.status.setText("Status: Discord launched")
        except Exception as e:
            self.on_error(str(e))

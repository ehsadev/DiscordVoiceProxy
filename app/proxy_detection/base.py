from abc import ABC, abstractmethod

from app.models.proxy import ProxyConfiguration


class ProxyDetector(ABC):
    name = "Unknown"

    @abstractmethod
    def detect(self) -> ProxyConfiguration | None: ...

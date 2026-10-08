from .invisible_man import InvisibleManDetector
from .nekoray import NekoRayDetector
from .v2rayn import V2RayNDetector


class ProxyDetectionService:
    def __init__(self):
        self.detectors = [V2RayNDetector(), NekoRayDetector(), InvisibleManDetector()]

    def detect(self):

        for detector in self.detectors:
            try:
                cfg = detector.detect()
                if cfg:
                    return detector.name, cfg
            except Exception:
                continue
        return None, None

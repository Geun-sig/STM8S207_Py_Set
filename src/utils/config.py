from PyQt6.QtCore import QSettings
from typing import Optional
import json


class AppConfig:
    """애플리케이션 설정 관리 클래스"""

    def __init__(self):
        self.settings = QSettings("SolarMonitor", "SolarBatteryMonitor")

    def save_last_port(self, port: str):
        """
        마지막 사용 COM 포트 저장

        Args:
            port: COM 포트 이름
        """
        self.settings.setValue("serial/last_port", port)

    def load_last_port(self) -> str:
        """
        마지막 사용 COM 포트 로드

        Returns:
            포트 이름 (없으면 빈 문자열)
        """
        return self.settings.value("serial/last_port", "")

    def save_window_geometry(self, geometry):
        """
        윈도우 위치/크기 저장

        Args:
            geometry: QMainWindow.saveGeometry() 결과
        """
        self.settings.setValue("window/geometry", geometry)

    def load_window_geometry(self):
        """
        윈도우 위치/크기 로드

        Returns:
            저장된 geometry 또는 None
        """
        return self.settings.value("window/geometry")

    def save_window_state(self, state):
        """
        윈도우 상태 저장 (스플리터 위치 등)

        Args:
            state: QMainWindow.saveState() 결과
        """
        self.settings.setValue("window/state", state)

    def load_window_state(self):
        """
        윈도우 상태 로드

        Returns:
            저장된 state 또는 None
        """
        return self.settings.value("window/state")

    def save_graph_buffer_size(self, size: int):
        """
        그래프 버퍼 크기 저장

        Args:
            size: 버퍼 크기
        """
        self.settings.setValue("graph/buffer_size", size)

    def load_graph_buffer_size(self) -> int:
        """
        그래프 버퍼 크기 로드

        Returns:
            버퍼 크기 (기본값: 1000)
        """
        return self.settings.value("graph/buffer_size", 1000, type=int)

    def save_device_settings(self, settings: 'DeviceSettings'):
        """
        장비 설정 저장

        Args:
            settings: DeviceSettings 객체
        """
        # 설정을 JSON 문자열로 변환하여 저장
        settings_dict = settings.to_dict()
        settings_json = json.dumps(settings_dict)
        self.settings.setValue("device/settings", settings_json)

    def load_device_settings(self) -> Optional['DeviceSettings']:
        """
        장비 설정 로드

        Returns:
            DeviceSettings 객체, 저장된 설정이 없으면 None
        """
        from ..models.device_settings import DeviceSettings

        settings_json = self.settings.value("device/settings", None)
        if settings_json is None:
            return None

        try:
            settings_dict = json.loads(settings_json)
            return DeviceSettings.from_dict(settings_dict)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None

    def clear_device_settings(self):
        """저장된 장비 설정 삭제"""
        self.settings.remove("device/settings")

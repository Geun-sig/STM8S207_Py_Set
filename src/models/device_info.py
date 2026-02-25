from dataclasses import dataclass


@dataclass
class DeviceInfo:
    """장치 펌웨어 버전 정보"""
    version: tuple[str, str, str, str]  # (A, B, C, D) = ASCII 문자

    def __str__(self) -> str:
        return f"v{'.'.join(self.version)}"

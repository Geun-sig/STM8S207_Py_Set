from dataclasses import dataclass
from datetime import datetime


@dataclass
class SensorData:
    """태양광/배터리 모니터링 데이터"""
    timestamp: datetime
    solar_voltage: float      # 태양광 전압 (V)
    battery_voltage: float    # 배터리 전압 (V)
    current: float            # 충방전 전류 (A, + 충전, - 방전)
    output_voltage: float     # 출력 전압 (V)

    def __str__(self) -> str:
        return (f"Solar: {self.solar_voltage:.1f}V, "
                f"Battery: {self.battery_voltage:.1f}V, "
                f"Current: {self.current:+.2f}A, "
                f"Output: {self.output_voltage:.1f}V")

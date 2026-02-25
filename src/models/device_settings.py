from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class BatteryTypeSettings:
    """배터리 타입별 충방전 설정"""
    float_charge_voltage: float = 13.8  # 부동 충전 전압 (V)
    max_charge_voltage: float = 14.4  # 최대 충전 전압 (V)
    max_charge_current: float = 30.0  # 최대 충전 전류 (A)
    max_discharge_current: float = 50.0  # 최대 방전 전류 (A)
    over_discharge_cutoff_voltage: float = 11.0  # 과방전 차단 전압 (V)
    discharge_reconnect_voltage: float = 12.0  # 방전 재개 전압 (V)
    charge_current_setting: float = 20.0  # 충전 전류 설정 (A)

    def to_dict(self) -> Dict[str, float]:
        """설정을 딕셔너리로 변환"""
        return {
            'float_charge_voltage': self.float_charge_voltage,
            'max_charge_voltage': self.max_charge_voltage,
            'max_charge_current': self.max_charge_current,
            'max_discharge_current': self.max_discharge_current,
            'over_discharge_cutoff_voltage': self.over_discharge_cutoff_voltage,
            'discharge_reconnect_voltage': self.discharge_reconnect_voltage,
            'charge_current_setting': self.charge_current_setting,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'BatteryTypeSettings':
        """딕셔너리로부터 설정 객체 생성"""
        return cls(**data)


@dataclass
class DeviceSettings:
    """
    장비 동작 파라미터 설정

    이 클래스는 장비의 동작을 제어하는 모든 설정값을 담습니다.
    각 필드는 NMEA 프로토콜을 통해 장비로부터 읽거나 장비로 쓸 수 있습니다.
    """

    # 배터리 타입 선택 (0: 납축전지, 1: LiFePO4, 2: Li-ion, 3: LiPo)
    battery_type: int = 0

    # 배터리 타입별 충방전 설정 (4가지 타입)
    battery_settings: List[BatteryTypeSettings] = field(default_factory=lambda: [
        # 0: 납축전지 (Lead-acid)
        BatteryTypeSettings(
            float_charge_voltage=13.8,
            max_charge_voltage=14.4,
            max_charge_current=30.0,
            max_discharge_current=50.0,
            over_discharge_cutoff_voltage=11.0,
            discharge_reconnect_voltage=12.0,
            charge_current_setting=20.0,
        ),
        # 1: LiFePO4
        BatteryTypeSettings(
            float_charge_voltage=13.6,
            max_charge_voltage=14.6,
            max_charge_current=30.0,
            max_discharge_current=50.0,
            over_discharge_cutoff_voltage=10.0,
            discharge_reconnect_voltage=11.0,
            charge_current_setting=20.0,
        ),
        # 2: Li-ion
        BatteryTypeSettings(
            float_charge_voltage=12.6,
            max_charge_voltage=12.6,
            max_charge_current=30.0,
            max_discharge_current=50.0,
            over_discharge_cutoff_voltage=9.0,
            discharge_reconnect_voltage=10.0,
            charge_current_setting=20.0,
        ),
        # 3: LiPo
        BatteryTypeSettings(
            float_charge_voltage=12.6,
            max_charge_voltage=12.6,
            max_charge_current=30.0,
            max_discharge_current=50.0,
            over_discharge_cutoff_voltage=9.0,
            discharge_reconnect_voltage=10.0,
            charge_current_setting=20.0,
        ),
    ])

    # 기타 설정
    battery_capacity: float = 100.0  # 배터리 용량 (Ah)
    solar_voltage_max: float = 50.0  # 태양광 패널 최대 전압 (V)
    solar_power_max: float = 500.0  # 태양광 패널 최대 전력 (W)
    mppt_enable: bool = True  # MPPT 기능 활성화

    temperature_compensation: bool = True  # 온도 보상 활성화
    temp_coeff: float = -0.003  # 온도 계수 (V/°C)
    temp_sensor_enable: bool = True  # 온도 센서 활성화

    over_voltage_protection: bool = True  # 과전압 보호
    over_current_protection: bool = True  # 과전류 보호
    over_temperature_protection: bool = True  # 과온도 보호
    short_circuit_protection: bool = True  # 단락 보호
    reverse_polarity_protection: bool = True  # 역극성 보호

    lcd_backlight_timeout: int = 60  # LCD 백라이트 타임아웃 (초, 0=항상 켜짐)
    data_log_interval: int = 10  # 데이터 로깅 간격 (초)
    serial_baud_rate: int = 9600  # 시리얼 통신 속도
    device_id: int = 1  # 장비 ID
    load_output_enable: bool = True  # 부하 출력 활성화
    auto_power_off: int = 0  # 자동 전원 차단 시간 (분, 0=비활성화)
    alarm_enable: bool = True  # 알람 활성화

    # 예약 필드 (향후 확장용)
    reserved_1: float = 0.0
    reserved_2: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        설정을 딕셔너리로 변환

        Returns:
            설정 딕셔너리
        """
        return {
            'battery_type': self.battery_type,
            'battery_settings': [bs.to_dict() for bs in self.battery_settings],
            'battery_capacity': self.battery_capacity,
            'solar_voltage_max': self.solar_voltage_max,
            'solar_power_max': self.solar_power_max,
            'mppt_enable': self.mppt_enable,
            'temperature_compensation': self.temperature_compensation,
            'temp_coeff': self.temp_coeff,
            'temp_sensor_enable': self.temp_sensor_enable,
            'over_voltage_protection': self.over_voltage_protection,
            'over_current_protection': self.over_current_protection,
            'over_temperature_protection': self.over_temperature_protection,
            'short_circuit_protection': self.short_circuit_protection,
            'reverse_polarity_protection': self.reverse_polarity_protection,
            'lcd_backlight_timeout': self.lcd_backlight_timeout,
            'data_log_interval': self.data_log_interval,
            'serial_baud_rate': self.serial_baud_rate,
            'device_id': self.device_id,
            'load_output_enable': self.load_output_enable,
            'auto_power_off': self.auto_power_off,
            'alarm_enable': self.alarm_enable,
            'reserved_1': self.reserved_1,
            'reserved_2': self.reserved_2,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceSettings':
        """
        딕셔너리로부터 설정 객체 생성

        Args:
            data: 설정 딕셔너리

        Returns:
            DeviceSettings 객체
        """
        # battery_settings를 BatteryTypeSettings 객체로 변환
        if 'battery_settings' in data:
            battery_settings = [BatteryTypeSettings.from_dict(bs) for bs in data['battery_settings']]
            data['battery_settings'] = battery_settings

        return cls(**data)

    def get_current_battery_settings(self) -> BatteryTypeSettings:
        """
        현재 선택된 배터리 타입의 설정 반환

        Returns:
            현재 배터리 타입의 설정
        """
        return self.battery_settings[self.battery_type]

    def get_battery_type_name(self, type_index: int = None) -> str:
        """
        배터리 타입 이름 반환

        Args:
            type_index: 배터리 타입 인덱스 (None이면 현재 선택된 타입)

        Returns:
            배터리 타입 이름
        """
        if type_index is None:
            type_index = self.battery_type

        names = ['납축전지', 'LiFePO4', 'Li-ion', 'LiPo']
        return names[type_index] if 0 <= type_index < len(names) else '알 수 없음'

    def get_field_info(self, field_name: str) -> Dict[str, Any]:
        """
        필드의 메타 정보 반환 (UI 생성용)

        Args:
            field_name: 필드 이름

        Returns:
            필드 정보 딕셔너리 (label, type, min, max, unit 등)
        """
        # 필드별 메타 정보
        field_info = {
            'battery_type': {'label': '배터리 타입', 'options': ['납축전지', 'LiFePO4', 'Li-ion', 'LiPo']},
            'battery_capacity': {'label': '배터리 용량', 'min': 10.0, 'max': 500.0, 'unit': 'Ah', 'decimals': 1},
            'solar_voltage_max': {'label': '태양광 최대 전압', 'min': 18.0, 'max': 100.0, 'unit': 'V', 'decimals': 1},
            'solar_power_max': {'label': '태양광 최대 전력', 'min': 100.0, 'max': 5000.0, 'unit': 'W', 'decimals': 0},
            'mppt_enable': {'label': 'MPPT 기능'},
            'temperature_compensation': {'label': '온도 보상'},
            'temp_coeff': {'label': '온도 계수', 'min': -0.01, 'max': 0.0, 'unit': 'V/°C', 'decimals': 4},
            'temp_sensor_enable': {'label': '온도 센서'},
            'over_voltage_protection': {'label': '과전압 보호'},
            'over_current_protection': {'label': '과전류 보호'},
            'over_temperature_protection': {'label': '과온도 보호'},
            'short_circuit_protection': {'label': '단락 보호'},
            'reverse_polarity_protection': {'label': '역극성 보호'},
            'lcd_backlight_timeout': {'label': 'LCD 백라이트 타임아웃', 'min': 0, 'max': 300, 'unit': '초'},
            'data_log_interval': {'label': '데이터 로깅 간격', 'min': 1, 'max': 3600, 'unit': '초'},
            'serial_baud_rate': {'label': '시리얼 통신 속도', 'options': [4800, 9600, 19200, 38400, 57600, 115200]},
            'device_id': {'label': '장비 ID', 'min': 1, 'max': 255},
            'load_output_enable': {'label': '부하 출력'},
            'auto_power_off': {'label': '자동 전원 차단', 'min': 0, 'max': 1440, 'unit': '분'},
            'alarm_enable': {'label': '알람'},
            'reserved_1': {'label': '예약 1', 'min': 0.0, 'max': 100.0, 'unit': '', 'decimals': 2},
            'reserved_2': {'label': '예약 2', 'min': 0, 'max': 100},
        }

        return field_info.get(field_name, {'label': field_name})

    def get_battery_setting_field_info(self, field_name: str) -> Dict[str, Any]:
        """
        배터리 타입별 설정 필드의 메타 정보 반환

        Args:
            field_name: 필드 이름

        Returns:
            필드 정보 딕셔너리
        """
        field_info = {
            'float_charge_voltage': {'label': '부동 충전 전압', 'min': 0.0, 'max': 30.0, 'unit': 'V', 'decimals': 1},
            'max_charge_voltage': {'label': '최대 충전 전압', 'min': 0.0, 'max': 30.0, 'unit': 'V', 'decimals': 1},
            'max_charge_current': {'label': '최대 충전 전류', 'min': 0.0, 'max': 100.0, 'unit': 'A', 'decimals': 1},
            'max_discharge_current': {'label': '최대 방전 전류', 'min': 0.0, 'max': 200.0, 'unit': 'A', 'decimals': 1},
            'over_discharge_cutoff_voltage': {'label': '과방전 차단 전압', 'min': 0.0, 'max': 30.0, 'unit': 'V', 'decimals': 1},
            'discharge_reconnect_voltage': {'label': '방전 재개 전압', 'min': 0.0, 'max': 30.0, 'unit': 'V', 'decimals': 1},
            'charge_current_setting': {'label': '충전 전류 설정', 'min': 0.0, 'max': 100.0, 'unit': 'A', 'decimals': 1},
        }

        return field_info.get(field_name, {'label': field_name})

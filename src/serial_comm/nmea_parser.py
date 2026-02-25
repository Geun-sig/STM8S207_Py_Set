import re
from datetime import datetime
from typing import Optional, Tuple
from ..models.sensor_data import SensorData
from ..models.device_info import DeviceInfo
from ..models.device_settings import DeviceSettings


def calculate_nmea_checksum(sentence: str) -> str:
    """
    NMEA0183 체크섬 계산

    Args:
        sentence: '$'와 '*' 사이의 문자열 (예: "SC,12.3,13.8,0.50,12.0")

    Returns:
        2자리 16진수 체크섬 (예: "4A")
    """
    checksum = 0
    for char in sentence:
        checksum ^= ord(char)
    return f"{checksum:02X}"


def validate_nmea_sentence(full_sentence: str) -> bool:
    """
    NMEA 문장의 체크섬 검증

    Args:
        full_sentence: 완전한 NMEA 문장 (예: "$SC,12.3,13.8,0.50,12.0*4A\\r\\n")

    Returns:
        체크섬이 유효하면 True
    """
    sentence = full_sentence.strip()

    if not sentence.startswith('$'):
        return False

    if '*' not in sentence:
        return False

    try:
        data_part, checksum_part = sentence.split('*')
        data_part = data_part[1:]  # '$' 제거

        calculated = calculate_nmea_checksum(data_part)
        return calculated == checksum_part.upper()
    except (ValueError, IndexError):
        return False


def parse_sc_data(sentence: str) -> Optional[SensorData]:
    """
    $SC 데이터 문장 파싱

    Args:
        sentence: NMEA 문장 (예: "$SC,18.5,13.2,1.25,12.0*3F\\r\\n")

    Returns:
        파싱 성공 시 SensorData 객체, 실패 시 None
    """
    if not validate_nmea_sentence(sentence):
        return None

    # 정규식으로 데이터 추출
    # $SC,XX.X,YY.Y,ZZ.ZZ,AA.A*CC
    pattern = r'\$SC,([+-]?\d+\.?\d*),([+-]?\d+\.?\d*),([+-]?\d+\.?\d*),([+-]?\d+\.?\d*)\*[0-9A-F]{2}'

    match = re.match(pattern, sentence.strip())
    if not match:
        return None

    try:
        solar_voltage = float(match.group(1))
        battery_voltage = float(match.group(2))
        current = float(match.group(3))
        output_voltage = float(match.group(4))

        return SensorData(
            timestamp=datetime.now(),
            solar_voltage=solar_voltage,
            battery_voltage=battery_voltage,
            current=current,
            output_voltage=output_voltage
        )
    except (ValueError, IndexError):
        return None


def parse_version(sentence: str) -> Optional[DeviceInfo]:
    """
    $LISTV 버전 응답 파싱

    Args:
        sentence: NMEA 문장 (예: "$LISTV,A,B,C,D*CC\\r\\n")

    Returns:
        파싱 성공 시 DeviceInfo 객체, 실패 시 None
    """
    # 체크섬 검증 생략하고 직접 파싱
    # 정규식으로 버전 정보 추출
    # $LISTV,A,B,C,D*CC (A,B,C,D는 ASCII 문자)
    pattern = r'\$LISTV,(.+?),(.+?),(.+?),(.+?)\*'

    match = re.match(pattern, sentence.strip())
    if not match:
        return None

    try:
        # ASCII 문자 그대로 저장
        version = (
            match.group(1),
            match.group(2),
            match.group(3),
            match.group(4)
        )

        return DeviceInfo(version=version)
    except (ValueError, IndexError):
        return None


def create_command(command: str) -> str:
    """
    NMEA 명령 문자열 생성 (체크섬 포함)

    Args:
        command: 명령 문자열 (예: "LICMD,A")

    Returns:
        체크섬이 포함된 완전한 NMEA 명령 (예: "$LICMD,A*22\\r\\n")
    """
    checksum = calculate_nmea_checksum(command)
    return f"${command}*{checksum}\r\n"


def create_read_eeprom1_command() -> str:
    """
    EEPROM 1 영역 읽기 명령 생성 (납축전지, LiFePO4)

    Returns:
        EEPROM 1 읽기 명령 문자열
    """
    return create_command("LICMD,6")


def create_read_eeprom2_command() -> str:
    """
    EEPROM 2 영역 읽기 명령 생성 (Li-ion, Li-pol)

    Returns:
        EEPROM 2 읽기 명령 문자열
    """
    return create_command("LICMD,8")


def parse_liste_response(sentence: str, settings: DeviceSettings) -> Optional[DeviceSettings]:
    """
    $LISTE 응답 파싱 (EEPROM 1 또는 EEPROM 2)

    Args:
        sentence: NMEA 문장
        settings: 기존 DeviceSettings 객체 (업데이트됨)

    Returns:
        업데이트된 DeviceSettings 객체, 실패 시 None
    """
    if not validate_nmea_sentence(sentence):
        return None

    sentence = sentence.strip()

    try:
        # '$LISTE,' 제거하고 '*' 이전까지 추출
        data_part = sentence.split('*')[0][1:]  # '$' 제거
        if not data_part.startswith('LISTE,'):
            return None

        # 'LISTE,' 제거
        values_str = data_part[6:]

        from ..models.device_settings import BatteryTypeSettings

        # EEPROM 1인지 2인지 확인 (A: 또는 B:가 있으면 EEPROM 1)
        if 'A:' in values_str or 'B:' in values_str:
            # EEPROM 1: 납축전지(A), LiFePO4(B)
            # 형식: {battery_type},A:1501601701801902002110,B:1511621731841952062217
            # battery_type 추출 (첫 번째 쉼표 앞의 숫자)
            if ',' in values_str:
                battery_type_str, rest = values_str.split(',', 1)
                try:
                    settings.battery_type = int(battery_type_str)
                except ValueError:
                    pass
                values_str = rest

            parts = values_str.split(',')
            for part in parts:
                if ':' not in part:
                    continue

                battery_type_char, data = part.split(':', 1)

                # 3자리씩 끊어서 7개 값 추출
                if len(data) != 21:  # 3자리 x 7개 = 21자리
                    continue

                values = []
                for i in range(7):
                    raw_value = int(data[i*3:(i+1)*3])
                    actual_value = raw_value / 10.0  # 0.1 곱하기
                    values.append(actual_value)

                # 배터리 타입에 따라 저장
                if battery_type_char == 'A':
                    # 납축전지 (인덱스 0)
                    settings.battery_settings[0] = BatteryTypeSettings(
                        float_charge_voltage=values[0],
                        max_charge_voltage=values[1],
                        max_charge_current=values[2],
                        max_discharge_current=values[3],
                        over_discharge_cutoff_voltage=values[4],
                        discharge_reconnect_voltage=values[5],
                        charge_current_setting=values[6],
                    )
                elif battery_type_char == 'B':
                    # LiFePO4 (인덱스 1)
                    settings.battery_settings[1] = BatteryTypeSettings(
                        float_charge_voltage=values[0],
                        max_charge_voltage=values[1],
                        max_charge_current=values[2],
                        max_discharge_current=values[3],
                        over_discharge_cutoff_voltage=values[4],
                        discharge_reconnect_voltage=values[5],
                        charge_current_setting=values[6],
                    )

        else:
            # EEPROM 2: Li-ion(C), Li-pol(D)
            # 형식: C:101102103104105106107,D:111112123124135136147
            parts = values_str.split(',')
            for part in parts:
                if ':' not in part:
                    continue

                battery_type_char, data = part.split(':', 1)

                # 3자리씩 끊어서 7개 값 추출
                if len(data) != 21:  # 3자리 x 7개 = 21자리
                    continue

                values = []
                for i in range(7):
                    raw_value = int(data[i*3:(i+1)*3])
                    actual_value = raw_value / 10.0  # 0.1 곱하기
                    values.append(actual_value)

                # 배터리 타입에 따라 저장
                if battery_type_char == 'C':
                    # Li-ion (인덱스 2)
                    settings.battery_settings[2] = BatteryTypeSettings(
                        float_charge_voltage=values[0],
                        max_charge_voltage=values[1],
                        max_charge_current=values[2],
                        max_discharge_current=values[3],
                        over_discharge_cutoff_voltage=values[4],
                        discharge_reconnect_voltage=values[5],
                        charge_current_setting=values[6],
                    )
                elif battery_type_char == 'D':
                    # Li-pol (인덱스 3)
                    settings.battery_settings[3] = BatteryTypeSettings(
                        float_charge_voltage=values[0],
                        max_charge_voltage=values[1],
                        max_charge_current=values[2],
                        max_discharge_current=values[3],
                        over_discharge_cutoff_voltage=values[4],
                        discharge_reconnect_voltage=values[5],
                        charge_current_setting=values[6],
                    )

        return settings

    except (ValueError, IndexError) as e:
        return None


def create_write_eeprom1_command(settings: DeviceSettings) -> str:
    """
    EEPROM 1 영역 쓰기 명령 생성 (납축전지, LiFePO4)

    Args:
        settings: DeviceSettings 객체

    Returns:
        EEPROM 1 쓰기 명령 문자열
    """
    # 배터리 타입
    battery_type = settings.battery_type

    # 납축전지 (A)
    bs_a = settings.battery_settings[0]
    data_a = ''.join([
        f"{int(bs_a.float_charge_voltage * 10):03d}",
        f"{int(bs_a.max_charge_voltage * 10):03d}",
        f"{int(bs_a.max_charge_current * 10):03d}",
        f"{int(bs_a.max_discharge_current * 10):03d}",
        f"{int(bs_a.over_discharge_cutoff_voltage * 10):03d}",
        f"{int(bs_a.discharge_reconnect_voltage * 10):03d}",
        f"{int(bs_a.charge_current_setting * 10):03d}",
    ])

    # LiFePO4 (B)
    bs_b = settings.battery_settings[1]
    data_b = ''.join([
        f"{int(bs_b.float_charge_voltage * 10):03d}",
        f"{int(bs_b.max_charge_voltage * 10):03d}",
        f"{int(bs_b.max_charge_current * 10):03d}",
        f"{int(bs_b.max_discharge_current * 10):03d}",
        f"{int(bs_b.over_discharge_cutoff_voltage * 10):03d}",
        f"{int(bs_b.discharge_reconnect_voltage * 10):03d}",
        f"{int(bs_b.charge_current_setting * 10):03d}",
    ])

    command = f"LICMD,7,{battery_type},A:{data_a},B:{data_b}"
    return create_command(command)


def create_write_eeprom2_command(settings: DeviceSettings) -> str:
    """
    EEPROM 2 영역 쓰기 명령 생성 (Li-ion, Li-pol)

    Args:
        settings: DeviceSettings 객체

    Returns:
        EEPROM 2 쓰기 명령 문자열
    """
    # Li-ion (C)
    bs_c = settings.battery_settings[2]
    data_c = ''.join([
        f"{int(bs_c.float_charge_voltage * 10):03d}",
        f"{int(bs_c.max_charge_voltage * 10):03d}",
        f"{int(bs_c.max_charge_current * 10):03d}",
        f"{int(bs_c.max_discharge_current * 10):03d}",
        f"{int(bs_c.over_discharge_cutoff_voltage * 10):03d}",
        f"{int(bs_c.discharge_reconnect_voltage * 10):03d}",
        f"{int(bs_c.charge_current_setting * 10):03d}",
    ])

    # Li-pol (D)
    bs_d = settings.battery_settings[3]
    data_d = ''.join([
        f"{int(bs_d.float_charge_voltage * 10):03d}",
        f"{int(bs_d.max_charge_voltage * 10):03d}",
        f"{int(bs_d.max_charge_current * 10):03d}",
        f"{int(bs_d.max_discharge_current * 10):03d}",
        f"{int(bs_d.over_discharge_cutoff_voltage * 10):03d}",
        f"{int(bs_d.discharge_reconnect_voltage * 10):03d}",
        f"{int(bs_d.charge_current_setting * 10):03d}",
    ])

    command = f"LICMD,9,C:{data_c},D:{data_d}"
    return create_command(command)


def parse_settings_response(sentence: str) -> Optional[DeviceSettings]:
    """
    설정 응답 파싱

    Args:
        sentence: NMEA 문장 (예: "$LICFG,0,13.8,14.4,...*CC\\r\\n")

    Returns:
        파싱 성공 시 DeviceSettings 객체, 실패 시 None
    """
    if not validate_nmea_sentence(sentence):
        return None

    sentence = sentence.strip()

    try:
        # '$LICFG,' 제거하고 '*' 이전까지 추출
        data_part = sentence.split('*')[0][1:]  # '$' 제거
        if not data_part.startswith('LICFG,'):
            return None

        # 'LICFG,' 제거
        values_str = data_part[6:]
        values = values_str.split(',')

        # 50개 값이 있어야 함 (1 + 28 + 21)
        if len(values) != 50:
            return None

        idx = 0

        # 배터리 타입
        battery_type = int(values[idx])
        idx += 1

        # 4개 배터리 타입별 설정
        from ..models.device_settings import BatteryTypeSettings
        battery_settings = []
        for i in range(4):
            bs = BatteryTypeSettings(
                float_charge_voltage=float(values[idx]),
                max_charge_voltage=float(values[idx + 1]),
                max_charge_current=float(values[idx + 2]),
                max_discharge_current=float(values[idx + 3]),
                over_discharge_cutoff_voltage=float(values[idx + 4]),
                discharge_reconnect_voltage=float(values[idx + 5]),
                charge_current_setting=float(values[idx + 6]),
            )
            battery_settings.append(bs)
            idx += 7

        # 기타 설정
        settings = DeviceSettings(
            battery_type=battery_type,
            battery_settings=battery_settings,
            battery_capacity=float(values[idx]),
            solar_voltage_max=float(values[idx + 1]),
            solar_power_max=float(values[idx + 2]),
            mppt_enable=bool(int(values[idx + 3])),
            temperature_compensation=bool(int(values[idx + 4])),
            temp_coeff=float(values[idx + 5]),
            temp_sensor_enable=bool(int(values[idx + 6])),
            over_voltage_protection=bool(int(values[idx + 7])),
            over_current_protection=bool(int(values[idx + 8])),
            over_temperature_protection=bool(int(values[idx + 9])),
            short_circuit_protection=bool(int(values[idx + 10])),
            reverse_polarity_protection=bool(int(values[idx + 11])),
            lcd_backlight_timeout=int(values[idx + 12]),
            data_log_interval=int(values[idx + 13]),
            serial_baud_rate=int(values[idx + 14]),
            device_id=int(values[idx + 15]),
            load_output_enable=bool(int(values[idx + 16])),
            auto_power_off=int(values[idx + 17]),
            alarm_enable=bool(int(values[idx + 18])),
            reserved_1=float(values[idx + 19]),
            reserved_2=int(values[idx + 20]),
        )

        return settings

    except (ValueError, IndexError) as e:
        return None


def parse_acknowledge(sentence: str) -> Tuple[bool, Optional[str]]:
    """
    ACK/NAK 응답 파싱

    Args:
        sentence: NMEA 문장 (예: "$LIACK,OK*CC\\r\\n" 또는 "$LIACK,ERR*CC\\r\\n")

    Returns:
        (성공 여부, 메시지) 튜플
    """
    if not validate_nmea_sentence(sentence):
        return False, "Invalid checksum"

    sentence = sentence.strip()

    # 정규식으로 응답 추출
    pattern = r'\$LIACK,(\w+)\*[0-9A-F]{2}'

    match = re.match(pattern, sentence)
    if not match:
        return False, "Invalid format"

    response = match.group(1).upper()
    if response == "OK":
        return True, "Success"
    else:
        return False, response


def parse_listok(sentence: str) -> bool:
    """
    $LISTOK 응답 파싱 (EEPROM 쓰기 성공)

    Args:
        sentence: NMEA 문장 (예: "$LISTOK*CC\\r\\n")

    Returns:
        성공 여부
    """
    if not validate_nmea_sentence(sentence):
        return False

    sentence = sentence.strip()
    return sentence.startswith('$LISTOK')

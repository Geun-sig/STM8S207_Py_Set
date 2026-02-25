import serial
import serial.tools.list_ports
from typing import List, Optional


class SerialHandler:
    """시리얼 포트 관리 클래스"""

    def __init__(self):
        self.serial_port: Optional[serial.Serial] = None
        self.port_name: str = ""

    @staticmethod
    def list_available_ports() -> List[str]:
        """
        사용 가능한 COM 포트 목록 반환

        Returns:
            COM 포트 이름 리스트
        """
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def open_port(self, port: str, baudrate: int = 9600) -> bool:
        """
        시리얼 포트 열기

        Args:
            port: COM 포트 이름 (예: "COM3")
            baudrate: 통신 속도 (기본: 9600)

        Returns:
            성공 시 True, 실패 시 False
        """
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,  # 8 데이터 비트
                parity=serial.PARITY_NONE,  # 패리티 없음
                stopbits=serial.STOPBITS_ONE,  # 1 스톱 비트
                timeout=1.0  # 1초 타임아웃
            )
            self.port_name = port
            return True
        except (serial.SerialException, OSError) as e:
            print(f"포트 열기 실패: {e}")
            return False

    def close_port(self) -> None:
        """시리얼 포트 닫기"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None
            self.port_name = ""

    def is_open(self) -> bool:
        """
        포트 열림 상태 확인

        Returns:
            포트가 열려 있으면 True
        """
        return self.serial_port is not None and self.serial_port.is_open

    def send_command(self, command: str) -> bool:
        """
        명령 전송

        Args:
            command: 전송할 명령 문자열 (체크섬 포함)

        Returns:
            성공 시 True, 실패 시 False
        """
        if not self.is_open():
            return False

        try:
            self.serial_port.write(command.encode('ascii'))
            return True
        except (serial.SerialException, OSError) as e:
            print(f"명령 전송 실패: {e}")
            return False

    def read_line(self) -> Optional[str]:
        """
        한 줄 읽기 (\\r\\n까지)

        Returns:
            읽은 문자열, 실패 시 None
        """
        if not self.is_open():
            return None

        try:
            line = self.serial_port.readline()
            if line:
                return line.decode('ascii', errors='ignore')
            return None
        except (serial.SerialException, OSError, UnicodeDecodeError) as e:
            print(f"데이터 읽기 실패: {e}")
            return None

    def flush(self) -> None:
        """입출력 버퍼 비우기"""
        if self.is_open():
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()

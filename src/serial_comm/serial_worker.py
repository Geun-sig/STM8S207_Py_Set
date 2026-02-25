from PyQt6.QtCore import QThread, pyqtSignal, QObject, QMutex, QMutexLocker
import time
from .serial_handler import SerialHandler
from . import nmea_parser
from ..models.sensor_data import SensorData
from ..models.device_info import DeviceInfo
from ..models.device_settings import DeviceSettings


class SerialWorker(QThread):
    """시리얼 통신 워커 스레드"""

    # 시그널 정의
    data_received = pyqtSignal(object)  # SensorData 객체
    version_received = pyqtSignal(object)  # DeviceInfo 객체
    settings_received = pyqtSignal(object)  # DeviceSettings 객체
    settings_write_ack = pyqtSignal(bool, str)  # 쓰기 확인 (성공 여부, 메시지)
    connected = pyqtSignal(str)  # COM 포트 이름
    disconnected = pyqtSignal()  # 연결 해제
    error_occurred = pyqtSignal(str)  # 에러 메시지
    packet_count_updated = pyqtSignal(int)  # 패킷 수
    error_count_updated = pyqtSignal(int)  # 에러 수

    # 타임아웃 설정 (초)
    TIMEOUT_SECONDS = 5.0

    def __init__(self, port: str, baudrate: int = 9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial_handler = SerialHandler()
        self.running = False
        self.packet_count = 0
        self.error_count = 0
        self.command_queue = []
        self.mutex = QMutex()
        self.reading_settings = False  # 설정 읽기 진행 중
        self.settings_buffer = None  # 설정 임시 저장소
        self.eeprom1_received = False  # EEPROM 1 수신 여부
        self.writing_settings = False  # 설정 쓰기 진행 중
        self.eeprom1_written = False  # EEPROM 1 쓰기 완료 여부
        self.last_command_time = None  # 마지막 명령 전송 시각

    def run(self):
        """스레드 실행 (메인 루프)"""
        self.running = True

        # 시리얼 포트 열기
        if not self.serial_handler.open_port(self.port, self.baudrate):
            self.error_occurred.emit(f"포트 열기 실패: {self.port}")
            return

        self.connected.emit(self.port)

        # 메인 루프: 데이터 수신
        while self.running:
            try:
                # 큐에 명령이 있으면 전송
                with QMutexLocker(self.mutex):
                    if self.command_queue:
                        command = self.command_queue.pop(0)
                        nmea_command = nmea_parser.create_command(command)
                        self.serial_handler.send_command(nmea_command)
                        # 명령 전송 시각 기록
                        self.last_command_time = time.time()

                # 타임아웃 체크
                self._check_timeout()

                line = self.serial_handler.read_line()

                if line is None:
                    # 타임아웃 또는 읽기 실패
                    continue

                line = line.strip()
                if not line:
                    continue

                # NMEA 문장 파싱
                self._parse_sentence(line)

            except Exception as e:
                self.error_count += 1
                self.error_count_updated.emit(self.error_count)
                self.error_occurred.emit(f"데이터 수신 중 에러: {str(e)}")
                time.sleep(0.1)  # 에러 발생 시 짧은 대기

        # 종료 시 포트 닫기
        self.serial_handler.close_port()
        self.disconnected.emit()

    def _parse_sentence(self, sentence: str):
        """
        NMEA 문장 파싱 및 적절한 시그널 발생

        Args:
            sentence: NMEA 문장
        """
        # $SC 데이터 파싱
        if sentence.startswith('$SC,'):
            data = nmea_parser.parse_sc_data(sentence)
            if data:
                self.packet_count += 1
                self.packet_count_updated.emit(self.packet_count)
                self.data_received.emit(data)
            else:
                self.error_count += 1
                self.error_count_updated.emit(self.error_count)
                self.error_occurred.emit(f"$SC 파싱 실패: {sentence}")

        # $LISTV 버전 파싱
        elif sentence.startswith('$LISTV'):
            version_info = nmea_parser.parse_version(sentence)
            if version_info:
                self.version_received.emit(version_info)
            else:
                self.error_count += 1
                self.error_count_updated.emit(self.error_count)
                self.error_occurred.emit(f"$LISTV 파싱 실패: {sentence}")

        # $LICFG 설정 파싱
        elif sentence.startswith('$LICFG'):
            settings = nmea_parser.parse_settings_response(sentence)
            if settings:
                self.settings_received.emit(settings)
            else:
                self.error_count += 1
                self.error_count_updated.emit(self.error_count)
                self.error_occurred.emit(f"$LICFG 파싱 실패: {sentence}")

        # $LIACK 확인 응답 파싱
        elif sentence.startswith('$LIACK'):
            success, message = nmea_parser.parse_acknowledge(sentence)
            self.settings_write_ack.emit(success, message)

        # $LISTOK EEPROM 쓰기 확인 응답 파싱
        elif sentence.startswith('$LISTOK'):
            if self.writing_settings:
                success = nmea_parser.parse_listok(sentence)
                if success:
                    if not self.eeprom1_written:
                        # EEPROM 1 쓰기 완료 - EEPROM 2 쓰기는 이미 큐에 있음
                        self.eeprom1_written = True
                        # 다음 명령 전송을 위해 타임아웃 타이머 리셋
                        self.last_command_time = None
                    else:
                        # EEPROM 2 쓰기 완료 - 모든 쓰기 완료
                        self.writing_settings = False
                        self.eeprom1_written = False
                        self.last_command_time = None
                        self.settings_write_ack.emit(True, "설정이 장비에 저장되었습니다.")
                else:
                    self.writing_settings = False
                    self.eeprom1_written = False
                    self.last_command_time = None
                    self.error_count += 1
                    self.error_count_updated.emit(self.error_count)
                    self.settings_write_ack.emit(False, "설정 쓰기 실패: $LISTOK 파싱 오류")

        # $LISTE 설정 응답 파싱 (EEPROM 1 또는 2)
        elif sentence.startswith('$LISTE'):
            if self.reading_settings and self.settings_buffer:
                settings = nmea_parser.parse_liste_response(sentence, self.settings_buffer)
                if settings:
                    self.settings_buffer = settings

                    # EEPROM 1인지 2인지 확인 (A: 또는 B:가 있으면 EEPROM 1)
                    if 'A:' in sentence or 'B:' in sentence:
                        # EEPROM 1 수신됨
                        self.eeprom1_received = True
                        # 다음 명령 전송을 위해 타임아웃 타이머 리셋
                        self.last_command_time = None
                        # EEPROM 2 읽기 명령 전송
                        with QMutexLocker(self.mutex):
                            self.command_queue.append("LICMD,8")
                    else:
                        # EEPROM 2 수신됨 - 모든 설정 읽기 완료
                        self.reading_settings = False
                        self.eeprom1_received = False
                        self.last_command_time = None
                        self.settings_received.emit(self.settings_buffer)
                        self.settings_buffer = None
                else:
                    self.reading_settings = False
                    self.eeprom1_received = False
                    self.last_command_time = None
                    self.settings_buffer = None
                    self.error_count += 1
                    self.error_count_updated.emit(self.error_count)
                    self.error_occurred.emit(f"$LISTE 파싱 실패: {sentence}")

    def send_command(self, command: str) -> bool:
        """
        명령 전송 (큐에 추가)

        Args:
            command: 전송할 명령 (예: "LICMD,A")

        Returns:
            성공 시 True
        """
        with QMutexLocker(self.mutex):
            self.command_queue.append(command)
        return True

    def request_read_settings(self) -> bool:
        """
        장비로부터 설정 읽기 요청 (EEPROM 1과 2를 순차적으로 읽음)

        Returns:
            성공 시 True
        """
        # 설정 읽기 상태 초기화
        self.reading_settings = True
        self.eeprom1_received = False
        self.settings_buffer = DeviceSettings()  # 빈 설정 객체 생성

        # EEPROM 1 읽기 명령 전송
        with QMutexLocker(self.mutex):
            self.command_queue.append("LICMD,6")
        return True

    def request_write_settings(self, settings: DeviceSettings) -> bool:
        """
        장비로 설정 쓰기 요청 (EEPROM 1과 2를 순차적으로 씀)

        Args:
            settings: DeviceSettings 객체

        Returns:
            성공 시 True
        """
        # 설정 쓰기 상태 초기화
        self.writing_settings = True
        self.eeprom1_written = False

        # EEPROM 1 쓰기 명령 생성
        command1 = nmea_parser.create_write_eeprom1_command(settings)
        command1_body = command1.strip()[1:].split('*')[0]

        # EEPROM 2 쓰기 명령 생성
        command2 = nmea_parser.create_write_eeprom2_command(settings)
        command2_body = command2.strip()[1:].split('*')[0]

        # 명령 큐에 순차적으로 추가
        with QMutexLocker(self.mutex):
            self.command_queue.append(command1_body)
            self.command_queue.append(command2_body)
        return True

    def _check_timeout(self):
        """
        설정 읽기/쓰기 타임아웃 체크
        """
        if self.last_command_time is None:
            return

        elapsed = time.time() - self.last_command_time

        # 설정 읽기 중 타임아웃
        if self.reading_settings and elapsed > self.TIMEOUT_SECONDS:
            self.reading_settings = False
            self.eeprom1_received = False
            self.settings_buffer = None
            self.last_command_time = None
            self.error_count += 1
            self.error_count_updated.emit(self.error_count)
            self.error_occurred.emit(f"장비 응답 타임아웃 ({self.TIMEOUT_SECONDS}초 초과)\n장비가 연결되어 있는지 확인하세요.")
            # 설정 읽기 실패 시그널 발생
            self.settings_received.emit(None)

        # 설정 쓰기 중 타임아웃
        elif self.writing_settings and elapsed > self.TIMEOUT_SECONDS:
            self.writing_settings = False
            self.eeprom1_written = False
            self.last_command_time = None
            self.error_count += 1
            self.error_count_updated.emit(self.error_count)
            self.error_occurred.emit(f"장비 응답 타임아웃 ({self.TIMEOUT_SECONDS}초 초과)\n장비가 연결되어 있는지 확인하세요.")
            # 설정 쓰기 실패 시그널 발생
            self.settings_write_ack.emit(False, f"타임아웃: 장비 응답 없음 ({self.TIMEOUT_SECONDS}초)")

    def stop(self):
        """스레드 정지"""
        self.running = False
        self.wait(2000)  # 최대 2초 대기

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QStatusBar, QMessageBox, QMenuBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from .widgets.serial_config_widget import SerialConfigWidget
from .widgets.data_display_widget import DataDisplayWidget
from .widgets.status_widget import StatusWidget
from .widgets.graph_widget import GraphWidget
from .widgets.logging_widget import LoggingWidget
from .widgets.device_settings_dialog import DeviceSettingsDialog
from ..serial_comm.serial_worker import SerialWorker
from ..utils.data_logger import DataLogger


class MainWindow(QMainWindow):
    """메인 애플리케이션 윈도우"""

    def __init__(self):
        super().__init__()
        self.serial_worker = None
        self.data_logger = DataLogger()
        self.settings_dialog = None
        self._init_ui()
        self.setWindowTitle("태양광/배터리 모니터링 시스템")
        self.resize(1200, 800)

    def _init_ui(self):
        """UI 초기화"""
        # 메뉴바 생성
        self._create_menu_bar()

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QHBoxLayout()

        # 스플리터 (좌우 분할)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 좌측 패널 (제어 및 데이터 표시)
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        # 위젯 생성
        self.serial_config_widget = SerialConfigWidget()
        self.data_display_widget = DataDisplayWidget()
        self.status_widget = StatusWidget()
        self.logging_widget = LoggingWidget()

        # 좌측 패널에 위젯 추가
        left_layout.addWidget(self.serial_config_widget)
        left_layout.addWidget(self.data_display_widget)
        left_layout.addWidget(self.status_widget)
        left_layout.addWidget(self.logging_widget)
        left_layout.addStretch()

        left_panel.setLayout(left_layout)

        # 우측 패널 (그래프)
        self.graph_widget = GraphWidget()

        # 스플리터에 패널 추가
        splitter.addWidget(left_panel)
        splitter.addWidget(self.graph_widget)
        splitter.setStretchFactor(0, 1)  # 좌측 패널
        splitter.setStretchFactor(1, 3)  # 우측 패널 (그래프가 더 넓게)

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

        # 상태 바
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비")

        # 시그널 연결
        self._connect_signals()

    def _create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()

        # 장비 메뉴
        device_menu = menubar.addMenu("장비(&D)")

        # 설정 액션
        settings_action = QAction("장비 설정(&S)...", self)
        settings_action.setShortcut("Ctrl+S")
        settings_action.setStatusTip("장비 동작 파라미터 설정")
        settings_action.triggered.connect(self._on_device_settings_requested)
        device_menu.addAction(settings_action)

        device_menu.addSeparator()

        # 종료 액션
        exit_action = QAction("종료(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("애플리케이션 종료")
        exit_action.triggered.connect(self.close)
        device_menu.addAction(exit_action)

        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말(&H)")

        # 정보 액션
        about_action = QAction("정보(&A)", self)
        about_action.setStatusTip("애플리케이션 정보")
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _connect_signals(self):
        """시그널 연결"""
        # 시리얼 설정 위젯
        self.serial_config_widget.connect_requested.connect(self._on_connect_requested)
        self.serial_config_widget.disconnect_requested.connect(self._on_disconnect_requested)

        # 상태 위젯
        self.status_widget.version_request.connect(self._on_version_request)
        self.status_widget.reset_request.connect(self._on_reset_request)

        # 로깅 위젯
        self.logging_widget.start_logging_requested.connect(self._on_start_logging)
        self.logging_widget.stop_logging_requested.connect(self._on_stop_logging)

    def _on_connect_requested(self, port: str):
        """
        연결 요청 핸들러

        Args:
            port: COM 포트 이름
        """
        # 기존 연결이 있으면 먼저 해제
        if self.serial_worker:
            self._on_disconnect_requested()

        # 워커 스레드 생성
        self.serial_worker = SerialWorker(port)

        # 워커 시그널 연결
        self.serial_worker.connected.connect(self._on_connected)
        self.serial_worker.disconnected.connect(self._on_disconnected)
        self.serial_worker.error_occurred.connect(self._on_error)
        self.serial_worker.data_received.connect(self._on_data_received)
        self.serial_worker.version_received.connect(self._on_version_received)
        self.serial_worker.settings_received.connect(self._on_settings_received)
        self.serial_worker.settings_write_ack.connect(self._on_settings_write_ack)
        self.serial_worker.packet_count_updated.connect(self._on_packet_count_updated)
        self.serial_worker.error_count_updated.connect(self._on_error_count_updated)

        # 스레드 시작
        self.serial_worker.start()
        self.status_bar.showMessage(f"연결 중: {port}...")

    def _on_disconnect_requested(self):
        """연결 해제 요청 핸들러"""
        if self.serial_worker:
            self.serial_worker.stop()
            self.serial_worker = None
            self.status_bar.showMessage("연결 해제됨")

    def _on_connected(self, port: str):
        """
        연결 성공 핸들러

        Args:
            port: COM 포트 이름
        """
        self.serial_config_widget.set_connected(True, port)
        self.status_widget.set_connected(True)
        self.data_display_widget.clear()
        self.graph_widget.clear()
        self.status_bar.showMessage(f"연결됨: {port}")

    def _on_disconnected(self):
        """연결 해제 핸들러"""
        self.serial_config_widget.set_connected(False)
        self.status_widget.set_connected(False)
        self.status_bar.showMessage("연결 안 됨")

    def _on_error(self, error_msg: str):
        """
        에러 핸들러

        Args:
            error_msg: 에러 메시지
        """
        self.status_bar.showMessage(f"에러: {error_msg}", 5000)
        # 중요한 에러는 메시지 박스로 표시
        if "포트 열기 실패" in error_msg:
            QMessageBox.critical(self, "연결 에러", error_msg)
            self._on_disconnected()

    def _on_data_received(self, data):
        """
        데이터 수신 핸들러

        Args:
            data: SensorData 객체
        """
        self.data_display_widget.update_data(data)
        self.graph_widget.update_data(data)

        # 로깅 중이면 데이터 저장
        if self.data_logger.is_logging:
            self.data_logger.log_data(data)
            self.logging_widget.update_record_count(self.data_logger.get_record_count())

        self.status_bar.showMessage(f"데이터 수신: {data}", 2000)

    def _on_version_received(self, version_info):
        """
        버전 정보 수신 핸들러

        Args:
            version_info: DeviceInfo 객체
        """
        self.status_widget.update_version(version_info)
        self.status_bar.showMessage(f"펌웨어 버전: {version_info}", 3000)

    def _on_packet_count_updated(self, count: int):
        """
        패킷 수 업데이트 핸들러

        Args:
            count: 패킷 수
        """
        self.status_widget.update_packet_count(count)

    def _on_error_count_updated(self, count: int):
        """
        에러 수 업데이트 핸들러

        Args:
            count: 에러 수
        """
        self.status_widget.update_error_count(count)

    def _on_version_request(self):
        """버전 조회 요청 핸들러"""
        if self.serial_worker:
            success = self.serial_worker.send_command("LICMD,A")
            if success:
                self.status_bar.showMessage("버전 조회 명령 전송됨", 2000)
            else:
                self.status_bar.showMessage("버전 조회 명령 전송 실패", 3000)

    def _on_reset_request(self):
        """MCU 리셋 요청 핸들러"""
        if self.serial_worker:
            success = self.serial_worker.send_command("LICMD,B")
            if success:
                self.status_bar.showMessage("MCU 리셋 명령 전송됨", 2000)
            else:
                self.status_bar.showMessage("MCU 리셋 명령 전송 실패", 3000)

    def _on_start_logging(self, file_path: str):
        """
        로깅 시작 핸들러

        Args:
            file_path: 저장할 파일 경로
        """
        if self.data_logger.start_logging(file_path):
            self.logging_widget.set_logging_state(True, file_path)
            self.status_bar.showMessage(f"로깅 시작: {file_path}", 3000)
        else:
            QMessageBox.warning(self, "로깅 에러", "로깅 시작에 실패했습니다.")

    def _on_stop_logging(self):
        """로깅 중지 핸들러"""
        if self.data_logger.stop_logging():
            record_count = self.data_logger.get_record_count()
            file_path = self.data_logger.get_file_path()
            self.logging_widget.set_logging_state(False)
            self.status_bar.showMessage(f"로깅 중지: {record_count}개 레코드 저장됨", 3000)
            QMessageBox.information(
                self,
                "로깅 완료",
                f"{record_count}개의 레코드가 저장되었습니다.\n\n파일: {file_path}"
            )

    def _on_device_settings_requested(self):
        """장비 설정 메뉴 클릭 핸들러"""
        # 설정 다이얼로그가 없으면 생성
        if self.settings_dialog is None:
            self.settings_dialog = DeviceSettingsDialog(self)

            # 설정 다이얼로그 시그널 연결
            self.settings_dialog.read_settings_requested.connect(self._on_settings_read_requested)
            self.settings_dialog.write_settings_requested.connect(self._on_settings_write_requested)

        # 연결 상태에 따라 버튼 활성화/비활성화
        is_connected = self.serial_worker is not None and self.serial_worker.isRunning()
        self.settings_dialog.set_connected(is_connected)

        # 다이얼로그 표시
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def _on_settings_read_requested(self):
        """설정 읽기 요청 핸들러"""
        if self.serial_worker:
            success = self.serial_worker.request_read_settings()
            if success:
                self.status_bar.showMessage("설정 읽기 명령 전송됨", 2000)
            else:
                self.status_bar.showMessage("설정 읽기 명령 전송 실패", 3000)
        else:
            QMessageBox.warning(self, "연결 안 됨", "장비에 연결되어 있지 않습니다.")

    def _on_settings_write_requested(self, settings):
        """설정 쓰기 요청 핸들러"""
        if self.serial_worker:
            success = self.serial_worker.request_write_settings(settings)
            if success:
                self.status_bar.showMessage("설정 쓰기 명령 전송됨", 2000)
            else:
                self.status_bar.showMessage("설정 쓰기 명령 전송 실패", 3000)
        else:
            QMessageBox.warning(self, "연결 안 됨", "장비에 연결되어 있지 않습니다.")

    def _on_settings_received(self, settings):
        """설정 수신 핸들러"""
        # 타임아웃으로 None을 받은 경우
        if settings is None:
            # 에러 메시지는 error_occurred 시그널에서 이미 표시됨
            return

        if self.settings_dialog:
            self.settings_dialog.load_settings(settings)
        self.status_bar.showMessage("설정을 장비로부터 읽었습니다", 3000)
        QMessageBox.information(self, "설정 읽기 완료", "장비로부터 설정을 성공적으로 읽었습니다.")

    def _on_settings_write_ack(self, success, message):
        """설정 쓰기 확인 응답 핸들러"""
        if success:
            self.status_bar.showMessage("설정이 장비에 저장되었습니다", 3000)
            QMessageBox.information(self, "설정 쓰기 완료", "설정이 장비에 성공적으로 저장되었습니다.")
        else:
            self.status_bar.showMessage(f"설정 쓰기 실패: {message}", 5000)
            QMessageBox.warning(self, "설정 쓰기 실패", f"설정 저장에 실패했습니다.\n\n에러: {message}")

    def _on_about(self):
        """정보 메뉴 클릭 핸들러"""
        QMessageBox.about(
            self,
            "태양광/배터리 모니터링 시스템",
            "<h3>태양광/배터리 모니터링 시스템</h3>"
            "<p>버전 1.0.0</p>"
            ""
            "<p>© 2026 (주)마린테크</p>"
        )

    def closeEvent(self, event):
        """
        윈도우 닫기 이벤트 핸들러

        Args:
            event: 닫기 이벤트
        """
        # 로깅 중이면 중지
        if self.data_logger.is_logging:
            self.data_logger.stop_logging()

        # 시리얼 워커 정리
        if self.serial_worker:
            self.serial_worker.stop()
            self.serial_worker = None

        event.accept()

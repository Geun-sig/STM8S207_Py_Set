from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QGroupBox)
from PyQt6.QtCore import pyqtSignal
from ...models.device_info import DeviceInfo


class StatusWidget(QWidget):
    """상태 및 버전 정보 위젯"""

    # 시그널 정의
    version_request = pyqtSignal()  # 버전 조회 요청
    reset_request = pyqtSignal()  # MCU 리셋 요청

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()

        # 그룹 박스
        group_box = QGroupBox("상태 정보")
        group_layout = QVBoxLayout()

        # 펌웨어 버전
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("펌웨어 버전:"))
        self.version_label = QLabel("--")
        self.version_label.setStyleSheet("font-weight: bold;")
        version_layout.addWidget(self.version_label)
        version_layout.addStretch()

        self.version_btn = QPushButton("버전 조회")
        self.version_btn.clicked.connect(self._on_version_request)
        self.version_btn.setEnabled(False)
        version_layout.addWidget(self.version_btn)
        group_layout.addLayout(version_layout)

        # MCU 리셋
        reset_layout = QHBoxLayout()
        reset_layout.addWidget(QLabel("MCU 제어:"))
        self.reset_btn = QPushButton("MCU 리셋")
        self.reset_btn.clicked.connect(self._on_reset_request)
        self.reset_btn.setEnabled(False)
        reset_layout.addWidget(self.reset_btn)
        reset_layout.addStretch()
        group_layout.addLayout(reset_layout)

        # 수신 패킷 수
        packet_layout = QHBoxLayout()
        packet_layout.addWidget(QLabel("수신 패킷:"))
        self.packet_count_label = QLabel("0")
        self.packet_count_label.setStyleSheet("font-weight: bold; color: green;")
        packet_layout.addWidget(self.packet_count_label)
        packet_layout.addStretch()
        group_layout.addLayout(packet_layout)

        # 에러 수
        error_layout = QHBoxLayout()
        error_layout.addWidget(QLabel("에러 수:"))
        self.error_count_label = QLabel("0")
        self.error_count_label.setStyleSheet("font-weight: bold; color: red;")
        error_layout.addWidget(self.error_count_label)
        error_layout.addStretch()
        group_layout.addLayout(error_layout)

        group_box.setLayout(group_layout)
        layout.addWidget(group_box)
        layout.addStretch()

        self.setLayout(layout)

    def _on_version_request(self):
        """버전 조회 버튼 클릭 핸들러"""
        self.version_request.emit()

    def _on_reset_request(self):
        """MCU 리셋 버튼 클릭 핸들러"""
        self.reset_request.emit()

    def update_version(self, version_info: DeviceInfo):
        """
        펌웨어 버전 업데이트

        Args:
            version_info: DeviceInfo 객체
        """
        self.version_label.setText(str(version_info))

    def update_packet_count(self, count: int):
        """
        패킷 수 업데이트

        Args:
            count: 패킷 수
        """
        self.packet_count_label.setText(str(count))

    def update_error_count(self, count: int):
        """
        에러 수 업데이트

        Args:
            count: 에러 수
        """
        self.error_count_label.setText(str(count))

    def set_connected(self, connected: bool):
        """
        연결 상태에 따라 버튼 활성화/비활성화

        Args:
            connected: 연결 여부
        """
        self.version_btn.setEnabled(connected)
        self.reset_btn.setEnabled(connected)
        if not connected:
            self.version_label.setText("--")
            self.packet_count_label.setText("0")
            self.error_count_label.setText("0")

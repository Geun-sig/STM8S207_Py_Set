from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QGroupBox, QFileDialog)
from PyQt6.QtCore import pyqtSignal


class LoggingWidget(QWidget):
    """데이터 로깅 컨트롤 위젯"""

    # 시그널 정의
    start_logging_requested = pyqtSignal(str)  # 로깅 시작 (파일 경로)
    stop_logging_requested = pyqtSignal()  # 로깅 중지

    def __init__(self):
        super().__init__()
        self.is_logging = False
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()

        # 그룹 박스
        group_box = QGroupBox("데이터 로깅")
        group_layout = QVBoxLayout()

        # 파일 경로 표시
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("파일:"))
        self.file_label = QLabel("로깅 중지됨")
        self.file_label.setStyleSheet("color: gray;")
        file_layout.addWidget(self.file_label)
        file_layout.addStretch()
        group_layout.addLayout(file_layout)

        # 레코드 수 표시
        record_layout = QHBoxLayout()
        record_layout.addWidget(QLabel("저장된 레코드:"))
        self.record_label = QLabel("0")
        self.record_label.setStyleSheet("font-weight: bold;")
        record_layout.addWidget(self.record_label)
        record_layout.addStretch()
        group_layout.addLayout(record_layout)

        # 버튼들
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("로깅 시작")
        self.start_btn.clicked.connect(self._on_start_clicked)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("로깅 중지")
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        group_layout.addLayout(btn_layout)

        group_box.setLayout(group_layout)
        layout.addWidget(group_box)
        layout.addStretch()

        self.setLayout(layout)

    def _on_start_clicked(self):
        """로깅 시작 버튼 클릭 핸들러"""
        # 파일 저장 다이얼로그
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "데이터 저장 위치 선택",
            f"solar_data.csv",
            "CSV 파일 (*.csv)"
        )

        if file_path:
            self.start_logging_requested.emit(file_path)

    def _on_stop_clicked(self):
        """로깅 중지 버튼 클릭 핸들러"""
        self.stop_logging_requested.emit()

    def set_logging_state(self, is_logging: bool, file_path: str = ""):
        """
        로깅 상태 설정

        Args:
            is_logging: 로깅 중 여부
            file_path: 파일 경로
        """
        self.is_logging = is_logging

        if is_logging:
            self.file_label.setText(file_path)
            self.file_label.setStyleSheet("color: green; font-weight: bold;")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        else:
            self.file_label.setText("로깅 중지됨")
            self.file_label.setStyleSheet("color: gray;")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.record_label.setText("0")

    def update_record_count(self, count: int):
        """
        레코드 수 업데이트

        Args:
            count: 레코드 수
        """
        self.record_label.setText(str(count))

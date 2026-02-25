from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                             QPushButton, QLabel, QGroupBox)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from ...serial_comm.serial_handler import SerialHandler


class SerialConfigWidget(QWidget):
    """시리얼 포트 설정 위젯"""

    # 시그널 정의
    connect_requested = pyqtSignal(str)  # 연결 요청 (포트 이름)
    disconnect_requested = pyqtSignal()  # 연결 해제 요청

    def __init__(self):
        super().__init__()
        self.is_connected = False
        self._init_ui()
        self.refresh_ports()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()

        # --- 로고와 회사명 ---
        header_layout = QHBoxLayout()
        
        # 로고
        logo_label = QLabel()
        try:
            pixmap = QPixmap("marine_logo.ico")
            if not pixmap.isNull():
                logo_label.setPixmap(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            print(f"로고 로드 실패: {e}") # 임시 디버깅
        
        # 회사명
        company_label = QLabel("(주) 마린테크")
        company_label.setStyleSheet("font-size: 20pt; font-weight: bold;")
        
        header_layout.addStretch()
        header_layout.addWidget(logo_label)
        header_layout.addWidget(company_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 제품명 라벨 추가
        product_label = QLabel("해상용 충방전기")
        product_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        product_label.setStyleSheet("font-size: 14pt; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(product_label)

        # 그룹 박스
        group_box = QGroupBox("시리얼 포트 설정")
        group_layout = QVBoxLayout()

        # COM 포트 선택
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("COM 포트:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        port_layout.addWidget(self.port_combo)

        # 새로고침 버튼
        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.refresh_btn)
        group_layout.addLayout(port_layout)

        # 연결/연결 해제 버튼
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("연결")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        btn_layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("연결 해제")
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        self.disconnect_btn.setEnabled(False)
        btn_layout.addWidget(self.disconnect_btn)
        group_layout.addLayout(btn_layout)

        # 상태 표시
        self.status_label = QLabel("연결 안 됨")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        group_layout.addWidget(self.status_label)

        group_box.setLayout(group_layout)
        layout.addWidget(group_box)
        layout.addStretch()

        self.setLayout(layout)

    def refresh_ports(self):
        """사용 가능한 포트 목록 새로고침"""
        self.port_combo.clear()
        ports = SerialHandler.list_available_ports()
        if ports:
            self.port_combo.addItems(ports)
        else:
            self.port_combo.addItem("포트 없음")

    def _on_connect_clicked(self):
        """연결 버튼 클릭 핸들러"""
        port = self.port_combo.currentText()
        if port and port != "포트 없음":
            self.connect_requested.emit(port)

    def _on_disconnect_clicked(self):
        """연결 해제 버튼 클릭 핸들러"""
        self.disconnect_requested.emit()

    def set_connected(self, connected: bool, port: str = ""):
        """
        연결 상태 설정

        Args:
            connected: 연결 여부
            port: 포트 이름
        """
        self.is_connected = connected

        if connected:
            self.status_label.setText(f"연결됨: {port}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.port_combo.setEnabled(False)
            self.refresh_btn.setEnabled(False)
        else:
            self.status_label.setText("연결 안 됨")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.port_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)

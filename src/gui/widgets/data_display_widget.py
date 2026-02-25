from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout,
                             QLabel, QGroupBox)
from PyQt6.QtCore import Qt
from ...models.sensor_data import SensorData


class DataDisplayWidget(QWidget):
    """실시간 데이터 표시 위젯"""

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()

        # 그룹 박스
        group_box = QGroupBox("실시간 데이터")
        grid_layout = QGridLayout()

        # 라벨 스타일
        label_style = "font-size: 14px; font-weight: bold;"
        value_style = "font-size: 18px; color: blue; font-weight: bold;"

        # 태양광 전압
        grid_layout.addWidget(QLabel("태양광 전압:"), 0, 0)
        self.solar_voltage_label = QLabel("-- V")
        self.solar_voltage_label.setStyleSheet(value_style)
        self.solar_voltage_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.solar_voltage_label, 0, 1)

        # 배터리 전압
        grid_layout.addWidget(QLabel("배터리 전압:"), 1, 0)
        self.battery_voltage_label = QLabel("-- V")
        self.battery_voltage_label.setStyleSheet(value_style)
        self.battery_voltage_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.battery_voltage_label, 1, 1)

        # 충방전 전류
        grid_layout.addWidget(QLabel("충방전 전류:"), 2, 0)
        self.current_label = QLabel("-- A")
        self.current_label.setStyleSheet(value_style)
        self.current_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.current_label, 2, 1)

        # 출력 전압
        grid_layout.addWidget(QLabel("출력 전압:"), 3, 0)
        self.output_voltage_label = QLabel("-- V")
        self.output_voltage_label.setStyleSheet(value_style)
        self.output_voltage_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.output_voltage_label, 3, 1)

        # 마지막 업데이트 시간
        grid_layout.addWidget(QLabel("마지막 업데이트:"), 4, 0)
        self.last_update_label = QLabel("--")
        self.last_update_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.last_update_label, 4, 1)

        group_box.setLayout(grid_layout)
        layout.addWidget(group_box)
        layout.addStretch()

        self.setLayout(layout)

    def update_data(self, data: SensorData):
        """
        데이터 업데이트

        Args:
            data: SensorData 객체
        """
        self.solar_voltage_label.setText(f"{data.solar_voltage:.1f} V")
        self.battery_voltage_label.setText(f"{data.battery_voltage:.1f} V")

        # 전류는 부호 표시 (+ 충전, - 방전)
        current_color = "green" if data.current >= 0 else "orange"
        self.current_label.setText(f"{data.current:+.2f} A")
        self.current_label.setStyleSheet(f"font-size: 18px; color: {current_color}; font-weight: bold;")

        self.output_voltage_label.setText(f"{data.output_voltage:.1f} V")

        # 시간 표시
        time_str = data.timestamp.strftime("%H:%M:%S")
        self.last_update_label.setText(time_str)

    def clear(self):
        """데이터 초기화"""
        self.solar_voltage_label.setText("-- V")
        self.battery_voltage_label.setText("-- V")
        self.current_label.setText("-- A")
        self.current_label.setStyleSheet("font-size: 18px; color: blue; font-weight: bold;")
        self.output_voltage_label.setText("-- V")
        self.last_update_label.setText("--")

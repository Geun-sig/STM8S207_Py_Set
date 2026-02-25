from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QFormLayout, QDoubleSpinBox, QSpinBox,
                             QCheckBox, QComboBox, QPushButton, QGroupBox,
                             QScrollArea, QMessageBox, QLabel, QGridLayout, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont # QFont import 추가
from ...models.device_settings import DeviceSettings, BatteryTypeSettings
import json
import os


class DeviceSettingsDialog(QDialog):
    """장비 설정 다이얼로그"""

    # 시그널 정의
    read_settings_requested = pyqtSignal()  # 장비로부터 설정 읽기 요청
    write_settings_requested = pyqtSignal(DeviceSettings)  # 장비로 설정 쓰기 요청

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = DeviceSettings()
        self.widgets = {}  # 필드명 -> 위젯 매핑
        self.battery_widgets = {}  # 배터리 설정 필드명 -> 위젯 매핑 (4개 타입별)
        self.settings_loaded = False  # 설정 로드 여부
        self._init_ui()
        self.setWindowTitle("장비 설정")
        self.resize(800, 480)

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()

        # 탭 위젯 생성
        tabs = QTabWidget()

        # 각 카테고리별 탭 추가
        tabs.addTab(self._create_battery_tab(), "충방전 설정")
        tabs.addTab(self._create_misc_tab(), "기타")

        layout.addWidget(tabs)

        # 버튼 패널
        button_layout = QHBoxLayout()

        self.read_button = QPushButton("장비에서 읽기")
        self.read_button.setAutoDefault(False)
        self.read_button.setMinimumHeight(40)
        self.read_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #1976D2;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border: 1px solid #0D47A1;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
                border: 1px solid #01579B;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
                border: 1px solid #9E9E9E;
            }
        """)
        self.read_button.clicked.connect(self._on_read_clicked)

        self.write_button = QPushButton("장비로 쓰기")
        self.write_button.setAutoDefault(False)
        self.write_button.setMinimumHeight(40)
        self.write_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #F57C00;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #F57C00;
                border: 1px solid #E65100;
            }
            QPushButton:pressed {
                background-color: #E65100;
                border: 1px solid #BF360C;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
                border: 1px solid #9E9E9E;
            }
        """)
        self.write_button.clicked.connect(self._on_write_clicked)

        self.save_button = QPushButton("파일로 저장")
        self.save_button.setAutoDefault(False)
        self.save_button.clicked.connect(self._on_save_clicked)

        self.load_button = QPushButton("파일에서 불러오기")
        self.load_button.setAutoDefault(False)
        self.load_button.clicked.connect(self._on_load_clicked)

        self.close_button = QPushButton("닫기")
        self.close_button.setAutoDefault(False)
        self.close_button.clicked.connect(self.reject)

        button_layout.addWidget(self.read_button)
        button_layout.addWidget(self.write_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # 초기 상태: 모든 입력 필드 비활성화
        self._set_widgets_enabled(False)
        # 파일에서 불러오기 버튼은 항상 활성화
        self.load_button.setEnabled(True)

    def _create_battery_tab(self) -> QWidget:
        """충방전 설정 탭 생성"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        main_layout = QVBoxLayout()

        # 배터리 타입 선택
        type_group = QGroupBox("배터리 타입 선택")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        type_group.setFont(font)
        type_group.setStyleSheet("""
            QGroupBox::title {
                color: #0000A0; /* 더 진한 파란색 */
            }
        """)
        type_layout = QFormLayout()

        self.battery_type_combo = QComboBox()
        self.battery_type_combo.addItems(['납축전지', 'LiFePO4', 'Li-ion', 'LiPo'])
        type_layout.addRow("설정 배터리 타입:", self.battery_type_combo)

        type_group.setLayout(type_layout)
        type_group.setFixedWidth(480) # 800px의 60%

        # 그룹 박스를 가운데 정렬하기 위한 레이아웃
        type_group_h_layout = QHBoxLayout()
        type_group_h_layout.addStretch()
        type_group_h_layout.addWidget(type_group)
        type_group_h_layout.addStretch()
        
        main_layout.addLayout(type_group_h_layout)

        # 충방전 설정 테이블
        settings_group = QGroupBox("충방전 설정")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        settings_group.setFont(font)
        settings_group.setStyleSheet("""
            QGroupBox::title {
                color: #0000A0; /* 더 진한 파란색 */
            }
        """)
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(30)  # 가로 간격 30px (기본값 약 6px의 5배)
        grid_layout.setVerticalSpacing(10)    # 세로 간격

        # 각 설정 필드 정보
        battery_fields = [
            'float_charge_voltage',
            'max_charge_voltage',
            'max_charge_current',
            'max_discharge_current',
            'over_discharge_cutoff_voltage',
            'discharge_reconnect_voltage',
            'charge_current_setting',
        ]

        battery_type_names = ['납축전지', 'LiFePO4', 'Li-ion', 'LiPo']

        # 헤더 행 (0행: 배터리 타입 이름)
        grid_layout.addWidget(QLabel("설정 항목"), 0, 0)
        for i, type_name in enumerate(battery_type_names):
            header_label = QLabel(type_name)
            header_label.setStyleSheet("font-weight: bold;")
            header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid_layout.addWidget(header_label, 0, i + 1)

        # 단위 열 추가
        grid_layout.addWidget(QLabel("단위"), 0, 5)

        # 각 설정 행 추가
        for row, field_name in enumerate(battery_fields, start=1):
            info = self.settings.get_battery_setting_field_info(field_name)
            label = info.get('label', field_name)
            unit = info.get('unit', '')

            # 설정 항목 이름 (첫 번째 열)
            label_widget = QLabel(label + ":")
            grid_layout.addWidget(label_widget, row, 0)

            # 4개 배터리 타입별 위젯 생성 (2~5열)
            for i in range(4):
                if i not in self.battery_widgets:
                    self.battery_widgets[i] = {}

                widget = QDoubleSpinBox()
                widget.setMinimum(info.get('min', 0.0))
                widget.setMaximum(info.get('max', 999999.0))
                widget.setDecimals(1)  # 소수점 1자리까지 표시
                widget.setSingleStep(0.1)  # 0.1 단위로 증감
                widget.setMinimumWidth(100)
                self.battery_widgets[i][field_name] = widget

                grid_layout.addWidget(widget, row, i + 1)

            # 단위 (6번째 열)
            unit_label = QLabel(unit)
            unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid_layout.addWidget(unit_label, row, 5)

        # 열 너비 조정
        grid_layout.setColumnStretch(0, 2)  # 설정 항목 이름 열
        for i in range(1, 5):
            grid_layout.setColumnStretch(i, 1)  # 배터리 타입별 값 열
        grid_layout.setColumnStretch(5, 1)  # 단위 열

        settings_group.setLayout(grid_layout)
        main_layout.addWidget(settings_group)

        main_layout.addStretch()
        container.setLayout(main_layout)
        scroll.setWidget(container)
        return scroll

    def _create_misc_tab(self) -> QWidget:
        """기타 설정 탭 생성"""
        fields = [
            'reserved_1',
        ]
        return self._create_scrollable_form(fields)

    def _create_scrollable_form(self, fields: list) -> QWidget:
        """
        스크롤 가능한 폼 위젯 생성

        Args:
            fields: 필드명 리스트

        Returns:
            스크롤 영역 위젯
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        for field_name in fields:
            info = self.settings.get_field_info(field_name)
            label = info.get('label', field_name)
            widget = self._create_widget_for_field(field_name, info)

            if widget:
                self.widgets[field_name] = widget
                unit = info.get('unit', '')
                if unit:
                    h_layout = QHBoxLayout()
                    h_layout.addWidget(widget)
                    h_layout.addWidget(QLabel(unit))
                    h_layout.addStretch()
                    form.addRow(f"{label}:", h_layout)
                else:
                    form.addRow(f"{label}:", widget)

        container.setLayout(form)
        scroll.setWidget(container)
        return scroll

    def _create_widget_for_field(self, field_name: str, info: dict) -> QWidget:
        """
        필드 타입에 맞는 위젯 생성

        Args:
            field_name: 필드명
            info: 필드 정보

        Returns:
            생성된 위젯
        """
        field_value = getattr(self.settings, field_name)

        if isinstance(field_value, bool):
            # 체크박스
            widget = QCheckBox()
            widget.setChecked(field_value)
            return widget

        elif isinstance(field_value, int):
            # 정수 입력
            if 'options' in info:
                # 콤보박스 (선택 옵션)
                widget = QComboBox()
                options = info['options']
                if isinstance(options[0], int):
                    widget.addItems([str(opt) for opt in options])
                    widget.setCurrentText(str(field_value))
                else:
                    widget.addItems(options)
                    widget.setCurrentIndex(field_value)
                return widget
            else:
                # 스핀박스
                widget = QSpinBox()
                widget.setMinimum(info.get('min', 0))
                widget.setMaximum(info.get('max', 999999))
                widget.setValue(field_value)
                return widget

        elif isinstance(field_value, float):
            # 실수 입력
            widget = QDoubleSpinBox()
            widget.setMinimum(info.get('min', 0.0))
            widget.setMaximum(info.get('max', 999999.0))
            widget.setDecimals(info.get('decimals', 2))
            widget.setValue(field_value)
            return widget

        return None


    def _set_widgets_enabled(self, enabled: bool):
        """
        모든 입력 위젯 활성화/비활성화

        Args:
            enabled: True면 활성화, False면 비활성화
        """
        # 배터리 타입 콤보박스
        self.battery_type_combo.setEnabled(enabled)

        # 배터리 설정 위젯들
        for i in range(4):
            if i in self.battery_widgets:
                for widget in self.battery_widgets[i].values():
                    widget.setEnabled(enabled)

        # 기타 설정 위젯들
        for widget in self.widgets.values():
            widget.setEnabled(enabled)

        # 장비로 쓰기 버튼
        # 연결 상태와 설정 로드 상태 모두 확인
        if hasattr(self, 'write_button'):
            write_enabled = enabled and self.settings_loaded
            self.write_button.setEnabled(write_enabled)

        # 파일로 저장 버튼
        # 설정 로드 상태만 확인 (연결 불필요)
        if hasattr(self, 'save_button'):
            self.save_button.setEnabled(self.settings_loaded)

    def _on_read_clicked(self):
        """장비에서 읽기 버튼 클릭"""
        self.read_settings_requested.emit()

    def _on_write_clicked(self):
        """장비로 쓰기 버튼 클릭"""
        # 현재 UI의 값을 설정 객체로 수집
        settings = self.get_settings()

        reply = QMessageBox.question(
            self,
            "설정 쓰기 확인",
            "현재 설정을 장비로 전송하시겠습니까?\n장비의 설정이 변경됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.write_settings_requested.emit(settings)

    def _on_save_clicked(self):
        """파일로 저장 버튼 클릭"""
        # 설정이 로드되지 않았으면 저장 불가
        if not self.settings_loaded:
            QMessageBox.warning(
                self,
                "저장 불가",
                "저장할 설정이 없습니다.\n먼저 '장비에서 읽기'를 실행하거나 '파일에서 불러오기'를 하세요."
            )
            return

        # 현재 UI의 설정값 수집
        settings = self.get_settings()

        # 파일 저장 다이얼로그
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "설정 파일 저장",
            os.path.join(os.getcwd(), "device_settings.json"),
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return  # 사용자가 취소

        try:
            # 설정을 딕셔너리로 변환
            settings_dict = settings.to_dict()

            # JSON 파일로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=2, ensure_ascii=False)

            QMessageBox.information(
                self,
                "저장 완료",
                f"설정이 성공적으로 저장되었습니다.\n\n파일: {file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "저장 실패",
                f"설정 저장 중 오류가 발생했습니다.\n\n에러: {str(e)}"
            )

    def _on_load_clicked(self):
        """파일에서 불러오기 버튼 클릭"""
        # 파일 열기 다이얼로그
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "설정 파일 불러오기",
            os.getcwd(),
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return  # 사용자가 취소

        try:
            # JSON 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                settings_dict = json.load(f)

            # 딕셔너리를 DeviceSettings 객체로 변환
            settings = DeviceSettings.from_dict(settings_dict)

            # UI에 로드 (이 메서드가 위젯 활성화도 처리)
            self.load_settings(settings)

            QMessageBox.information(
                self,
                "불러오기 완료",
                f"설정이 성공적으로 불러와졌습니다.\n\n파일: {file_path}"
            )

        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self,
                "불러오기 실패",
                f"JSON 파일 형식이 올바르지 않습니다.\n\n에러: {str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "불러오기 실패",
                f"설정 불러오기 중 오류가 발생했습니다.\n\n에러: {str(e)}"
            )

    def load_settings(self, settings: DeviceSettings):
        """
        설정을 UI에 로드

        Args:
            settings: DeviceSettings 객체
        """
        self.settings = settings

        # 배터리 타입 설정
        self.battery_type_combo.blockSignals(True)
        self.battery_type_combo.setCurrentIndex(settings.battery_type)
        self.battery_type_combo.blockSignals(False)

        # 배터리 타입별 설정 로드
        for i in range(4):
            battery_setting = settings.battery_settings[i]
            for field_name, widget in self.battery_widgets[i].items():
                value = getattr(battery_setting, field_name)
                widget.blockSignals(True)
                widget.setValue(value)
                widget.blockSignals(False)

        # 기타 설정 로드
        for field_name, widget in self.widgets.items():
            value = getattr(settings, field_name)

            widget.blockSignals(True)
            if isinstance(widget, QCheckBox):
                widget.setChecked(value)
            elif isinstance(widget, QSpinBox):
                widget.setValue(value)
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(value)
            elif isinstance(widget, QComboBox):
                info = settings.get_field_info(field_name)
                if 'options' in info:
                    options = info['options']
                    if isinstance(options[0], int):
                        widget.setCurrentText(str(value))
                    else:
                        widget.setCurrentIndex(value)
            widget.blockSignals(False)

        # 설정 로드 완료 - 위젯 활성화
        self.settings_loaded = True
        self._set_widgets_enabled(True)

    def get_settings(self) -> DeviceSettings:
        """
        UI의 현재 값으로 설정 객체 생성

        Returns:
            DeviceSettings 객체
        """
        # 4개 배터리 타입 모두의 설정 저장
        for i in range(4):
            for field_name, widget in self.battery_widgets[i].items():
                setattr(self.settings.battery_settings[i], field_name, widget.value())

        # 배터리 타입 저장
        self.settings.battery_type = self.battery_type_combo.currentIndex()

        # 기타 설정 저장
        for field_name, widget in self.widgets.items():
            if isinstance(widget, QCheckBox):
                setattr(self.settings, field_name, widget.isChecked())
            elif isinstance(widget, QSpinBox):
                setattr(self.settings, field_name, widget.value())
            elif isinstance(widget, QDoubleSpinBox):
                setattr(self.settings, field_name, widget.value())
            elif isinstance(widget, QComboBox):
                info = self.settings.get_field_info(field_name)
                if 'options' in info:
                    options = info['options']
                    if isinstance(options[0], int):
                        setattr(self.settings, field_name, int(widget.currentText()))
                    else:
                        setattr(self.settings, field_name, widget.currentIndex())

        return self.settings

    def set_connected(self, connected: bool):
        """
        연결 상태에 따라 버튼 활성화/비활성화

        Args:
            connected: 연결 상태
        """
        self.read_button.setEnabled(connected)
        # 장비로 쓰기는 연결 상태와 설정 로드 상태 모두 확인
        self.write_button.setEnabled(connected and self.settings_loaded)

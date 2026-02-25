from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from collections import deque
from datetime import datetime
from ...models.sensor_data import SensorData


class GraphWidget(QWidget):
    """실시간 그래프 위젯"""

    def __init__(self, max_samples: int = 1000, window_size: float = 100.0):
        super().__init__()
        self.max_samples = max_samples
        self.window_size = window_size  # X축 표시 범위 (초)
        self._init_data_buffers()
        self._init_ui()
        self.start_time = datetime.now()

    def _init_data_buffers(self):
        """데이터 버퍼 초기화"""
        self.time_buffer = deque(maxlen=self.max_samples)
        self.solar_voltage_buffer = deque(maxlen=self.max_samples)
        self.battery_voltage_buffer = deque(maxlen=self.max_samples)
        self.current_buffer = deque(maxlen=self.max_samples)
        self.output_voltage_buffer = deque(maxlen=self.max_samples)

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()

        # pyqtgraph 설정
        pg.setConfigOptions(antialias=True)

        # 전체 그래프 위젯 생성
        self._create_all_params_tab()

        layout.addWidget(self.graph_widget)
        self.setLayout(layout)

    def _create_all_params_tab(self):
        """모든 파라미터 그래프 생성"""
        self.graph_widget = pg.GraphicsLayoutWidget()

        # 태양광 전압
        self.solar_plot = self.graph_widget.addPlot(row=0, col=0, title="태양광 전압")
        self.solar_plot.setLabel('left', '전압', units='V')
        self.solar_plot.setLabel('bottom', '시간', units='s')
        self.solar_plot.showGrid(x=True, y=True)
        self.solar_curve = self.solar_plot.plot(pen='y', name='태양광')

        # 배터리 전압
        self.battery_plot = self.graph_widget.addPlot(row=1, col=0, title="배터리 전압")
        self.battery_plot.setLabel('left', '전압', units='V')
        self.battery_plot.setLabel('bottom', '시간', units='s')
        self.battery_plot.showGrid(x=True, y=True)
        self.battery_curve = self.battery_plot.plot(pen='g', name='배터리')

        # 충방전 전류
        self.current_plot = self.graph_widget.addPlot(row=2, col=0, title="충방전 전류")
        self.current_plot.setLabel('left', '전류', units='A')
        self.current_plot.setLabel('bottom', '시간', units='s')
        self.current_plot.showGrid(x=True, y=True)
        self.current_plot.addLine(y=0, pen='r')  # 0선 표시
        self.current_curve = self.current_plot.plot(pen='c', name='전류')

        # 출력 전압
        self.output_plot = self.graph_widget.addPlot(row=3, col=0, title="출력 전압")
        self.output_plot.setLabel('left', '전압', units='V')
        self.output_plot.setLabel('bottom', '시간', units='s')
        self.output_plot.showGrid(x=True, y=True)
        self.output_curve = self.output_plot.plot(pen='m', name='출력')

    def update_data(self, data: SensorData):
        """
        데이터 업데이트

        Args:
            data: SensorData 객체
        """
        # 경과 시간 계산 (초)
        elapsed_time = (data.timestamp - self.start_time).total_seconds()

        # 버퍼에 데이터 추가
        self.time_buffer.append(elapsed_time)
        self.solar_voltage_buffer.append(data.solar_voltage)
        self.battery_voltage_buffer.append(data.battery_voltage)
        self.current_buffer.append(data.current)
        self.output_voltage_buffer.append(data.output_voltage)

        # 리스트로 변환
        time_list = list(self.time_buffer)
        solar_list = list(self.solar_voltage_buffer)
        battery_list = list(self.battery_voltage_buffer)
        current_list = list(self.current_buffer)
        output_list = list(self.output_voltage_buffer)

        # 그래프 업데이트
        self.solar_curve.setData(time_list, solar_list)
        self.battery_curve.setData(time_list, battery_list)
        self.current_curve.setData(time_list, current_list)
        self.output_curve.setData(time_list, output_list)

        # X축 범위를 100초 윈도우로 설정 (슬라이딩 윈도우)
        if elapsed_time < self.window_size:
            # 초기에는 0부터 window_size까지 표시
            x_min = 0
            x_max = self.window_size
        else:
            # window_size 초과 시 최근 window_size 초만 표시
            x_min = elapsed_time - self.window_size
            x_max = elapsed_time

        # 모든 플롯에 X축 범위 적용
        self.solar_plot.setXRange(x_min, x_max, padding=0)
        self.battery_plot.setXRange(x_min, x_max, padding=0)
        self.current_plot.setXRange(x_min, x_max, padding=0)
        self.output_plot.setXRange(x_min, x_max, padding=0)

    def clear(self):
        """데이터 초기화"""
        self._init_data_buffers()
        self.start_time = datetime.now()

        # 모든 그래프 클리어
        self.solar_curve.setData([], [])
        self.battery_curve.setData([], [])
        self.current_curve.setData([], [])
        self.output_curve.setData([], [])

        # X축 범위를 초기 상태로 리셋
        self.solar_plot.setXRange(0, self.window_size, padding=0)
        self.battery_plot.setXRange(0, self.window_size, padding=0)
        self.current_plot.setXRange(0, self.window_size, padding=0)
        self.output_plot.setXRange(0, self.window_size, padding=0)

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional
from ..models.sensor_data import SensorData


class DataLogger:
    """실시간 데이터 CSV 로거"""

    def __init__(self):
        self.file_path: Optional[Path] = None
        self.file_handle = None
        self.csv_writer = None
        self.is_logging = False
        self.record_count = 0

    def start_logging(self, file_path: Optional[str] = None) -> bool:
        """
        로깅 시작

        Args:
            file_path: 저장할 파일 경로 (None이면 자동 생성)

        Returns:
            성공 시 True
        """
        if self.is_logging:
            return False

        # 파일 경로 설정
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"solar_data_{timestamp}.csv"

        self.file_path = Path(file_path)

        try:
            # 파일 열기 (UTF-8 BOM 포함 - Excel 호환성)
            self.file_handle = open(self.file_path, 'w', newline='', encoding='utf-8-sig')
            self.csv_writer = csv.writer(self.file_handle)

            # 헤더 작성
            self.csv_writer.writerow([
                '타임스탬프',
                '태양광 전압(V)',
                '배터리 전압(V)',
                '충방전 전류(A)',
                '출력 전압(V)'
            ])

            self.is_logging = True
            self.record_count = 0
            return True

        except Exception as e:
            print(f"로깅 시작 실패: {e}")
            if self.file_handle:
                self.file_handle.close()
            return False

    def log_data(self, data: SensorData) -> bool:
        """
        데이터 로깅

        Args:
            data: SensorData 객체

        Returns:
            성공 시 True
        """
        if not self.is_logging or not self.csv_writer:
            return False

        try:
            # 데이터 작성
            self.csv_writer.writerow([
                data.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],  # 밀리초까지
                f"{data.solar_voltage:.1f}",
                f"{data.battery_voltage:.1f}",
                f"{data.current:.2f}",
                f"{data.output_voltage:.1f}"
            ])

            self.file_handle.flush()  # 즉시 파일에 쓰기
            self.record_count += 1
            return True

        except Exception as e:
            print(f"데이터 로깅 실패: {e}")
            return False

    def stop_logging(self) -> bool:
        """
        로깅 중지

        Returns:
            성공 시 True
        """
        if not self.is_logging:
            return False

        try:
            if self.file_handle:
                self.file_handle.close()

            self.is_logging = False
            self.file_handle = None
            self.csv_writer = None
            return True

        except Exception as e:
            print(f"로깅 중지 실패: {e}")
            return False

    def get_file_path(self) -> Optional[str]:
        """
        현재 로깅 중인 파일 경로

        Returns:
            파일 경로 또는 None
        """
        if self.file_path:
            return str(self.file_path)
        return None

    def get_record_count(self) -> int:
        """
        저장된 레코드 수

        Returns:
            레코드 수
        """
        return self.record_count

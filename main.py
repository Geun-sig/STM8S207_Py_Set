import sys
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow


def main():
    """애플리케이션 메인 함수"""
    app = QApplication(sys.argv)
    app.setApplicationName("태양광/배터리 모니터링 시스템")
    app.setOrganizationName("Solar Monitor")

    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()

    # 이벤트 루프 실행
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

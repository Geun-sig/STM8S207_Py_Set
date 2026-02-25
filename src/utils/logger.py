import logging
import sys
from datetime import datetime


def setup_logger(name: str = "SolarMonitor", level=logging.INFO):
    """
    로거 설정

    Args:
        name: 로거 이름
        level: 로그 레벨

    Returns:
        설정된 Logger 객체
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 이미 핸들러가 있으면 추가하지 않음
    if logger.handlers:
        return logger

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


def setup_file_logger(name: str = "SolarMonitor",
                      filename: str = None,
                      level=logging.INFO):
    """
    파일 로거 설정

    Args:
        name: 로거 이름
        filename: 로그 파일 이름 (None이면 자동 생성)
        level: 로그 레벨

    Returns:
        설정된 Logger 객체
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"solar_monitor_{timestamp}.log"

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 파일 핸들러
    file_handler = logging.FileHandler(filename, encoding='utf-8')
    file_handler.setLevel(level)

    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger

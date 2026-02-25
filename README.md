# 태양광/배터리 모니터링 시스템

Python + PyQt6 기반 실시간 태양광/배터리 모니터링 GUI 애플리케이션

---

## 주요 기능

### 실시간 모니터링
- 태양광 전압, 배터리 전압, 충방전 전류, 출력 전압 실시간 표시
- pyqtgraph 기반 실시간 그래프

### 시리얼 통신
- COM 포트 자동 감지 및 수동 선택
- NMEA0183 형식 데이터 파싱 및 체크섬 검증 (XOR 방식)
- 9600 baud, 8N1 설정

### 장비 설정 (EEPROM 읽기/쓰기)
- 배터리 타입별 충방전 파라미터 설정
  - 납축전지 / LiFePO4 / Li-ion / LiPo 4가지 타입 지원
- EEPROM 1/2 순차 읽기·쓰기
- 설정값을 JSON 파일로 저장/불러오기
- 장비 무응답 시 5초 자동 타임아웃

---

## 시스템 요구사항

- Python 3.10 이상
- Windows / Linux / macOS

---

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/your-repo/solar-battery-monitor.git
cd solar-battery-monitor
```

### 2. 가상환경 생성 및 활성화

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

---

## 실행

```bash
python main.py
```

---

## 사용법

### 1. 시리얼 포트 연결

1. "시리얼 포트 설정" 패널에서 COM 포트 선택
2. 필요시 "새로고침" 버튼으로 포트 목록 갱신
3. "연결" 버튼 클릭

### 2. 데이터 모니터링

- 연결 후 자동으로 데이터 수신 시작
- "실시간 데이터" 패널에서 현재 값 확인
- 그래프에서 시간에 따른 변화 확인

### 3. 장비 설정

메뉴바 **장비(D) → 장비 설정(S)** 또는 `Ctrl+S`

| 버튼 | 설명 |
|---|---|
| 장비에서 읽기 | EEPROM 1/2를 순차 읽어 UI에 표시 |
| 장비로 쓰기 | 현재 UI 값을 EEPROM 1/2에 순차 저장 |
| 파일로 저장 | 현재 설정을 JSON 파일로 저장 |
| 파일에서 불러오기 | JSON 파일에서 설정을 불러와 UI에 표시 |

> **참고:** 장비에서 읽거나 파일에서 불러오기 전까지 입력 필드는 비활성화됩니다.

### 4. 펌웨어 버전 조회

"상태 정보" 패널에서 "버전 조회" 버튼 클릭

### 5. 연결 해제

"연결 해제" 버튼 클릭

---

## 데이터 프로토콜

### 실시간 센서 데이터 수신 (`$SC`)

**형식:** `$SC,XX.X,YY.Y,ZZ.ZZ,AA.A*CC\r\n`

| 필드 | 설명 |
|---|---|
| `XX.X` | 태양광 전압 (V) |
| `YY.Y` | 배터리 전압 (V) |
| `ZZ.ZZ` | 충방전 전류 (A, + 충전 / - 방전) |
| `AA.A` | 출력 전압 (V) |
| `CC` | NMEA 체크섬 (16진수 XOR) |

**예시:** `$SC,18.5,13.2,1.25,12.0*3F\r\n`

### 펌웨어 버전 조회

| 방향 | 메시지 |
|---|---|
| 송신 | `$LICMD,A*22\r\n` |
| 수신 | `$LISTV,A,B,C,D*CC\r\n` (버전 A.B.C.D) |

### 장비 설정 읽기

| 명령 | 설명 |
|---|---|
| `$LICMD,6*55` | EEPROM 1 읽기 (납축전지 A, LiFePO4 B) |
| `$LICMD,8*5B` | EEPROM 2 읽기 (Li-ion C, LiPo D) |

**응답 예시:**
```
$LISTE,0,A:170160170180190200170,B:170162173184195206170*5E
$LISTE,C:187102103104105106187,D:187112123124135136187*CC
```

> 3자리 숫자 × 7개 / 실제값 = 원시값 ÷ 10 (예: `170` → `17.0 V`)

**필드 순서:** 부동충전전압, 최대충전전압, 최대충전전류, 최대방전전류, 과방전차단전압, 방전재개전압, 충전전류설정

### 장비 설정 쓰기

| 명령 | 설명 |
|---|---|
| `$LICMD,7,{type},A:...,B:...*CC` | EEPROM 1 쓰기 (type: 배터리 타입 0~3) |
| `$LICMD,9,C:...,D:...*CC` | EEPROM 2 쓰기 |

**확인 응답:** `$LISTOK*CC`

**쓰기 순서:** EEPROM 1 전송 → `$LISTOK` 수신 → EEPROM 2 전송 → `$LISTOK` 수신 → 완료

---

## 프로젝트 구조

```
python_set/
├── main.py                              # 애플리케이션 진입점
├── requirements.txt                     # 의존성 목록
├── README.md
│
├── src/
│   ├── gui/
│   │   ├── main_window.py              # 메인 윈도우 (메뉴바, 시그널 연결)
│   │   └── widgets/
│   │       ├── data_display_widget.py  # 실시간 데이터 표시
│   │       ├── device_settings_dialog.py # 장비 설정 다이얼로그
│   │       ├── graph_widget.py         # 실시간 그래프
│   │       ├── logging_widget.py       # 로그 출력
│   │       ├── serial_config_widget.py # 시리얼 포트 설정
│   │       └── status_widget.py        # 상태 정보
│   │
│   ├── serial_comm/
│   │   ├── serial_handler.py           # 시리얼 포트 관리
│   │   ├── serial_worker.py            # QThread 비동기 I/O 워커
│   │   └── nmea_parser.py              # NMEA 파싱 / 명령 생성
│   │
│   ├── models/
│   │   ├── sensor_data.py              # 센서 데이터 모델
│   │   ├── device_info.py              # 장치 정보 모델
│   │   └── device_settings.py          # 배터리 설정 모델 (to_dict / from_dict)
│   │
│   └── utils/
│       ├── config.py                   # 설정 저장/로드 (JSON)
│       └── logger.py                   # 로깅
│
└── tests/
    └── test_nmea_parser.py             # NMEA 파서 단위 테스트
```

---

## 테스트

```bash
python -m unittest tests.test_nmea_parser
```

---

## 문제 해결

| 증상 | 확인 사항 |
|---|---|
| COM 포트가 목록에 없음 | 장치 연결 확인, 드라이버 설치 확인, "새로고침" 클릭 |
| 연결 실패 | 다른 프로그램의 포트 점유 여부 확인, 장치 전원 및 케이블 확인 |
| 데이터 수신 안 됨 | 에러 카운트 증가 여부 확인, 체크섬 에러 로그 확인 |
| 장비 설정 읽기 실패 | 연결 상태 확인, 5초 내 응답 없으면 타임아웃 메시지 표시됨 |

---

## 기술 스택

| 패키지 | 버전 |
|---|---|
| Python | 3.10+ |
| PyQt6 | 6.6.1 |
| pyqtgraph | 0.13.3 |
| pyserial | 3.5 |
| numpy | 1.26.3 |

---

## 라이선스

이 프로젝트는 교육 및 개인 사용 목적으로 제공됩니다.

# 태양광/배터리 모니터링 시스템 개발 진행 상황

## 프로젝트 개요
Python + PyQt6 기반 태양광/배터리 모니터링 GUI 애플리케이션

---

## 최근 작업 내역 (2026-01-09)

### 0. 타임아웃 기능 추가 (2026-01-09)

#### 문제
- 장비가 시리얼 데이터를 전송하지 않을 때 무한 대기
- 사용자에게 아무런 피드백이 없어 응답 여부를 알 수 없음
- `reading_settings`, `writing_settings` 플래그가 True로 계속 유지됨

#### 해결 방안
**serial_worker.py 수정:**
- `TIMEOUT_SECONDS = 5.0` 상수 추가 (타임아웃 시간: 5초)
- `last_command_time` 변수 추가 (마지막 명령 전송 시각 추적)
- `_check_timeout()` 메서드 추가:
  - 설정 읽기/쓰기 중일 때 경과 시간 체크
  - 5초 초과 시 타임아웃 처리
  - 상태 플래그 초기화 (`reading_settings`, `writing_settings`, `last_command_time`)
  - 에러 카운트 증가
  - `error_occurred` 시그널 발생 ("장비 응답 타임아웃")
  - `settings_received(None)` 또는 `settings_write_ack(False, "타임아웃")` 시그널 발생

- 메인 루프에서 타임아웃 체크:
  - 명령 전송 시 `last_command_time = time.time()` 기록
  - 매 루프마다 `_check_timeout()` 호출

- 응답 수신 시 타이머 리셋:
  - $LISTE (EEPROM 1) 수신 → `last_command_time = None` (다음 명령 전송 대기)
  - $LISTE (EEPROM 2) 수신 → `last_command_time = None` (완료)
  - $LISTOK (EEPROM 1) 수신 → `last_command_time = None` (다음 명령 전송 대기)
  - $LISTOK (EEPROM 2) 수신 → `last_command_time = None` (완료)
  - 파싱 실패 시에도 `last_command_time = None` (상태 초기화)

**main_window.py 수정:**
- `_on_settings_received(settings)` 핸들러:
  - `settings is None` 체크 추가
  - None일 경우 조기 반환 (에러 메시지는 `error_occurred`에서 표시됨)

#### 동작 흐름
1. **정상 응답 시:**
   ```
   명령 전송 → last_command_time 기록
   → 응답 수신 (5초 이내)
   → 파싱 성공 → last_command_time = None
   → 다음 명령 또는 완료
   ```

2. **타임아웃 시:**
   ```
   명령 전송 → last_command_time 기록
   → 5초 경과
   → _check_timeout() 감지
   → 상태 초기화 + 에러 시그널 발생
   → 사용자에게 타임아웃 메시지 표시
   ```

#### 장점
- 장비 무반응 시 5초 후 자동 타임아웃
- 사용자에게 명확한 에러 메시지 제공
- 상태 플래그가 정리되어 다음 명령 실행 가능
- 에러 카운트 자동 증가

#### 코드 위치
- `src/serial_comm/serial_worker.py:25` - TIMEOUT_SECONDS 상수
- `src/serial_comm/serial_worker.py:42` - last_command_time 변수
- `src/serial_comm/serial_worker.py:68` - 명령 전송 시 시각 기록
- `src/serial_comm/serial_worker.py:71` - 타임아웃 체크 호출
- `src/serial_comm/serial_worker.py:257-289` - _check_timeout() 메서드
- `src/serial_comm/serial_worker.py:150,155,160,181,190,198` - 타이머 리셋
- `src/gui/main_window.py:335-339` - None 체크

#### 디버그 메시지 제거 (2026-01-09)
정상 동작 확인 후 모든 디버그 print 문 제거:
- `serial_worker.py` - 명령 전송, 수신, 파싱 관련 디버그 메시지 (17개)
- `device_settings_dialog.py` - 버튼 클릭 디버그 메시지 (2개)
- `main_window.py` - 설정 읽기/쓰기 핸들러 디버그 메시지 (10개)

---

### 0.1 초기 설정값 숨김 처리 (2026-01-09)

#### 문제
- 장비 설정 다이얼로그를 처음 열면 하드코딩된 기본값이 표시됨
- 사용자가 실제 장비 설정이 아닌 기본값을 보고 혼란
- 장비에서 읽기 전에도 "장비로 쓰기"가 가능하여 의미 없는 데이터 전송 가능

#### 해결 방안
**device_settings_dialog.py 수정:**
- `settings_loaded` 플래그 추가 (초기값: False)
- `_set_widgets_enabled(enabled)` 메서드 추가:
  - 모든 입력 위젯 (배터리 설정, 기타 설정) 활성화/비활성화
  - 배터리 타입 콤보박스 활성화/비활성화
  - 장비로 쓰기 버튼은 연결 상태 AND settings_loaded 확인

- 초기화 수정:
  - `__init__()`: 초기 `load_settings()` 호출 제거
  - `_init_ui()` 끝: `_set_widgets_enabled(False)` 호출

- `load_settings()` 수정:
  - 설정 로드 완료 후 `settings_loaded = True`
  - `_set_widgets_enabled(True)` 호출하여 위젯 활성화

- `set_connected()` 수정:
  - 장비로 쓰기 버튼: `connected AND settings_loaded` 확인

#### 동작 흐름
1. **다이얼로그 초기 상태:**
   - 모든 입력 필드 비활성화 (회색 처리)
   - 장비로 쓰기 버튼 비활성화
   - 장비에서 읽기 버튼만 활성화 (연결된 경우)

2. **장비에서 읽기 성공:**
   - `load_settings()` 호출
   - 모든 입력 필드 활성화
   - 실제 장비 설정값 표시
   - 장비로 쓰기 버튼 활성화

3. **파일에서 불러오기 성공:** (향후 구현)
   - `load_settings()` 호출
   - 동일하게 활성화 및 값 표시

#### 장점
- 사용자가 실제 데이터인지 기본값인지 명확히 구분 가능
- 의미 없는 기본값 전송 방지
- 더 직관적인 사용자 경험

#### 코드 위치
- `src/gui/widgets/device_settings_dialog.py:21` - settings_loaded 플래그
- `src/gui/widgets/device_settings_dialog.py:126` - 초기 비활성화
- `src/gui/widgets/device_settings_dialog.py:128` - 파일에서 불러오기 버튼 활성화
- `src/gui/widgets/device_settings_dialog.py:345-368` - _set_widgets_enabled() 메서드
- `src/gui/widgets/device_settings_dialog.py:527-528` - load_settings()에서 활성화
- `src/gui/widgets/device_settings_dialog.py:571` - set_connected() 수정

---

### 0.2 파일 저장/불러오기 기능 구현 (2026-01-09)

#### 구현 내용

**파일 형식:**
- JSON 형식으로 저장/로드
- UTF-8 인코딩, indent=2로 가독성 향상
- DeviceSettings.to_dict() / from_dict() 활용

**파일 저장 (_on_save_clicked):**
- 설정이 로드되지 않은 경우 경고 메시지
- QFileDialog로 저장 경로 선택 (기본: ~/device_settings.json)
- 현재 UI의 설정값을 수집하여 JSON 저장
- 성공/실패 메시지 표시

**파일 불러오기 (_on_load_clicked):**
- QFileDialog로 파일 선택
- JSON 파일 읽기 및 파싱
- DeviceSettings.from_dict()로 객체 생성
- load_settings() 호출하여 UI 업데이트 및 활성화
- JSON 형식 오류 별도 처리

**버튼 활성화 로직:**
- **장비에서 읽기**: 연결 상태에 따름
- **장비로 쓰기**: 연결 상태 AND settings_loaded
- **파일로 저장**: settings_loaded만 확인 (연결 불필요)
- **파일에서 불러오기**: 항상 활성화

#### 사용 시나리오

1. **장비 설정 백업:**
   ```
   장비에서 읽기 → 파일로 저장 → device_settings.json 생성
   ```

2. **설정 복원:**
   ```
   파일에서 불러오기 → device_settings.json 선택 → 장비로 쓰기
   ```

3. **설정 편집:**
   ```
   파일에서 불러오기 → 값 수정 → 파일로 저장 (or 장비로 쓰기)
   ```

#### 장점
- 장비 설정을 파일로 백업 가능
- 여러 설정 프로파일 관리 가능
- 오프라인 상태에서도 설정 편집 가능
- 설정 공유 및 버전 관리 용이

#### 에러 처리
- 저장 실패: 파일 쓰기 권한, 디스크 공간 등
- 불러오기 실패: 파일 없음, JSON 형식 오류, 필드 누락 등
- 모든 예외 상황에 대한 사용자 친화적 메시지 제공

#### 코드 위치
- `src/gui/widgets/device_settings_dialog.py:7-8` - json, os import
- `src/gui/widgets/device_settings_dialog.py:384-428` - _on_save_clicked() 구현
- `src/gui/widgets/device_settings_dialog.py:430-471` - _on_load_clicked() 구현
- `src/gui/widgets/device_settings_dialog.py:368` - save_button 활성화 로직
- `src/models/device_settings.py:118-167` - to_dict(), from_dict() 메서드

---

### 1. 장비 설정 기능 구현

#### 1.1 데이터 모델 (`src/models/device_settings.py`)
- **BatteryTypeSettings 클래스**: 배터리 타입별 충방전 설정
  - 부동 충전 전압 (float_charge_voltage)
  - 최대 충전 전압 (max_charge_voltage)
  - 최대 충전 전류 (max_charge_current)
  - 최대 방전 전류 (max_discharge_current)
  - 과방전 차단 전압 (over_discharge_cutoff_voltage)
  - 방전 재개 전압 (discharge_reconnect_voltage)
  - 충전 전류 설정 (charge_current_setting)

- **DeviceSettings 클래스**: 전체 장비 설정
  - 배터리 타입 선택 (0: 납축전지, 1: LiFePO4, 2: Li-ion, 3: LiPo)
  - 4개 배터리 타입별 설정 (battery_settings 배열)
  - 기타 설정 (배터리 용량, 태양광 설정, 보호 기능 등)

#### 1.2 UI 구현 (`src/gui/widgets/device_settings_dialog.py`)
- **DeviceSettingsDialog**: 별도 다이얼로그 창으로 구현
- **2개 탭 구조**:
  - **충방전 설정 탭**:
    - 배터리 타입 선택 콤보박스 (최상단)
    - 테이블 형태로 4개 배터리 타입의 설정값을 가로로 나란히 표시
    - 7개 설정 항목 × 4개 타입 = 28개 입력 필드
    - 가로 간격: 30px (가독성 향상)
    - 값 조정: 0.1 단위, 소수점 1자리 표시
  - **기타 탭**:
    - 배터리 용량, 태양광 설정, 온도 보상, 보호 기능, 시스템 설정 등

- **주요 기능**:
  - 장비에서 읽기
  - 장비로 쓰기
  - 파일로 저장 (향후 구현)
  - 파일에서 불러오기 (향후 구현)
  - 적용
  - 닫기

#### 1.3 NMEA 프로토콜 구현 (`src/serial_comm/nmea_parser.py`)

**읽기 명령:**
- `$LICMD,6*55` - EEPROM 1 읽기 (납축전지, LiFePO4)
- `$LICMD,8*5B` - EEPROM 2 읽기 (Li-ion, LiPo)

**응답 형식:**
- EEPROM 1: `$LISTE,0,A:170160170180190200170,B:170162173184195206170*5E`
- EEPROM 2: `$LISTE,C:187102103104105106187,D:187112123124135136187*CC`
- 각 값: 3자리 숫자 (170 → 17.0, 즉 0.1 곱하기)
- 순서: 부동충전전압, 최대충전전압, 최대충전전류, 최대방전전류, 과방전차단전압, 방전재개전압, 충전전류설정

**쓰기 명령:**
- `$LICMD,7,{battery_type},A:170160...,B:170162...*CC` - EEPROM 1 쓰기
- `$LICMD,9,C:187102...,D:187112...*CC` - EEPROM 2 쓰기
- battery_type: 현재 선택된 배터리 타입 (0-3)
- 값을 10배하여 3자리 정수로 변환 (17.0 → 170)

**쓰기 확인 응답:**
- `$LISTOK*CC` - 쓰기 성공
- EEPROM 1 쓰기 → $LISTOK 수신 → EEPROM 2 쓰기 → $LISTOK 수신 → 완료

**구현된 함수:**
- `create_read_eeprom1_command()` - EEPROM 1 읽기 명령 생성
- `create_read_eeprom2_command()` - EEPROM 2 읽기 명령 생성
- `create_write_eeprom1_command(settings)` - EEPROM 1 쓰기 명령 생성 (battery_type 포함)
- `create_write_eeprom2_command(settings)` - EEPROM 2 쓰기 명령 생성
- `parse_liste_response(sentence, settings)` - $LISTE 응답 파싱
- `parse_acknowledge(sentence)` - ACK/NAK 응답 파싱
- `parse_listok(sentence)` - $LISTOK 응답 파싱

#### 1.4 시리얼 워커 업데이트 (`src/serial_comm/serial_worker.py`)

**시그널 추가:**
- `settings_received` - 설정 수신 시그널
- `settings_write_ack` - 쓰기 확인 시그널

**메서드 추가:**
- `request_read_settings()` - 설정 읽기 요청 (EEPROM 1, 2 순차 읽기)
- `request_write_settings(settings)` - 설정 쓰기 요청 (EEPROM 1, 2 순차 쓰기)

**상태 추적 변수:**
- `reading_settings` - 설정 읽기 진행 중 플래그
- `eeprom1_received` - EEPROM 1 읽기 완료 플래그
- `writing_settings` - 설정 쓰기 진행 중 플래그
- `eeprom1_written` - EEPROM 1 쓰기 완료 플래그

**동작 흐름:**
1. 읽기: EEPROM 1 읽기 → $LISTE 수신 → 자동으로 EEPROM 2 읽기 → $LISTE 수신 → 전체 설정 UI 업데이트
2. 쓰기: EEPROM 1 쓰기 → $LISTOK 수신 → EEPROM 2 쓰기 → $LISTOK 수신 → 완료 시그널 발생

#### 1.5 메인 윈도우 업데이트 (`src/gui/main_window.py`)

**메뉴바 추가:**
- 장비(D) 메뉴
  - 장비 설정(S) - Ctrl+S
  - 종료(X) - Ctrl+Q
- 도움말(H) 메뉴
  - 정보(A)

**핸들러 추가:**
- `_on_device_settings_requested()` - 설정 다이얼로그 열기
- `_on_settings_read_requested()` - 설정 읽기 요청
- `_on_settings_write_requested(settings)` - 설정 쓰기 요청
- `_on_settings_received(settings)` - 설정 수신 처리
- `_on_settings_write_ack(success, message)` - 쓰기 확인 처리

#### 1.6 설정 저장/로드 (`src/utils/config.py`)

**메서드 추가:**
- `save_device_settings(settings)` - JSON으로 설정 저장
- `load_device_settings()` - 저장된 설정 불러오기
- `clear_device_settings()` - 저장된 설정 삭제

---

### 2. 해결된 주요 문제

#### 2.0 배터리 타입 파싱 문제 (2026-01-09)
**문제:**
- 납축전지(타입 0)일 때는 정상 동작
- 다른 배터리 타입(1, 2, 3)으로 설정 후 쓰기/읽기 시 값이 맞지 않음
- 납축전지(A)와 LiFePO4(B) 설정 항목에서만 문제 발생
- 배터리 타입 값도 설정한 것과 달라짐

**원인:**
- EEPROM 1 응답 형식: `$LISTE,{battery_type},A:...,B:...*5E`
- 기존 코드는 `values_str.startswith('0,')`만 체크하여 battery_type이 0일 때만 정상 파싱
- battery_type이 1, 2, 3일 때는 조건 실패로 EEPROM 2로 잘못 파싱됨

**해결:**
- EEPROM 1/2 구분 방법 변경: 'A:' 또는 'B:' 존재 여부로 판단
- 첫 번째 쉼표 앞의 숫자를 battery_type으로 파싱하여 settings.battery_type에 저장
- `nmea_parser.py:186` - 조건문 수정 및 battery_type 파싱 로직 추가

#### 2.1 위젯 범위 제한 문제
**문제:**
- 장비에서 읽은 값(17.0V, 20.0V)이 UI에 제대로 표시되지 않음
- 위젯의 min/max 범위가 너무 작아서 값이 잘림 (예: max=15.0V → 17.0V 입력 시 15.0V로 제한)

**해결:**
- 모든 전압 범위를 0.0 ~ 30.0V로 확장
- 전류 범위를 0.0 ~ 100.0A (방전 200.0A)로 확장
- `device_settings.py`의 `get_battery_setting_field_info()` 메서드 수정

#### 2.2 UI 업데이트 신호 충돌
**문제:**
- `setValue()` 호출 시 valueChanged 신호가 발생하여 의도치 않은 업데이트 발생

**해결:**
- `blockSignals(True)` 사용하여 신호 차단
- 값 설정 후 `blockSignals(False)`로 복원

#### 2.3 Enter 키로 버튼 자동 실행 문제 (2026-01-09)
**문제:**
- 설정값 입력 후 Enter 키를 누르면 포커스가 있는 "장비에서 읽기" 버튼이 자동 실행됨
- 입력 확정 목적의 Enter가 버튼 클릭으로 오인됨

**해결:**
- 모든 버튼에 `setAutoDefault(False)` 설정
- Enter 키는 다음 필드로 포커스 이동만 하고 버튼은 마우스 클릭 또는 스페이스바로만 실행

#### 2.4 UI 개선 사항 (2026-01-09)
- "적용" 버튼 제거 - 실질적 기능 없어 혼란 방지
- 배터리 타입 명칭 변경: "Li-pol" → "LiPo"

---

### 3. 현재 구현 상태

#### ✅ 완료된 기능
- [x] 배터리 타입별 설정 데이터 모델
- [x] 장비 설정 UI 다이얼로그 (테이블 형태)
- [x] EEPROM 1/2 읽기 NMEA 프로토콜 및 연동
- [x] EEPROM 1/2 쓰기 NMEA 프로토콜 및 연동
- [x] $LISTOK 응답 처리 및 순차 쓰기 로직
- [x] 시리얼 통신 연동
- [x] 메인 윈도우 메뉴 통합
- [x] 설정 파일 저장/로드 (로컬)
- [x] 값 범위 제한 문제 해결
- [x] UI 업데이트 안정화
- [x] 설정 파일 저장/불러오기 (JSON)
- [x] 타임아웃 처리
- [x] 초기 설정값 숨김 처리

#### 🚧 향후 구현 예정
- [ ] 설정 프로파일 관리 (여러 설정 세트)
- [ ] 설정값 검증 로직 강화
- [ ] 기타 탭 설정의 장비 연동 (현재는 충방전 설정만 EEPROM 연동)

---

### 4. 파일 구조

```
python_set/
├── main.py
├── claude.md (이 파일)
├── src/
│   ├── models/
│   │   ├── device_settings.py (신규 - 배터리 설정 모델)
│   │   ├── battery_type_settings.py (BatteryTypeSettings 클래스)
│   │   └── __init__.py (업데이트)
│   ├── gui/
│   │   ├── main_window.py (업데이트 - 메뉴바, 설정 연동)
│   │   └── widgets/
│   │       └── device_settings_dialog.py (신규 - 설정 다이얼로그)
│   ├── serial_comm/
│   │   ├── nmea_parser.py (업데이트 - EEPROM 1/2 프로토콜)
│   │   └── serial_worker.py (업데이트 - 설정 읽기/쓰기)
│   └── utils/
│       └── config.py (업데이트 - 설정 저장/로드)
```

---

### 5. 통신 프로토콜 명세

#### 5.1 설정 읽기

| 명령 | 설명 | 형식 |
|------|------|------|
| `$LICMD,6*55` | EEPROM 1 읽기 | 납축전지(A), LiFePO4(B) |
| `$LICMD,8*5B` | EEPROM 2 읽기 | Li-ion(C), LiPo(D) |

**응답 예시:**
```
$LISTE,0,A:170160170180190200170,B:170162173184195206170*5E
$LISTE,C:187102103104105106187,D:187112123124135136187*CC
```

**값 해석:**
- 3자리씩 7개 값
- 실제값 = 원시값 / 10.0
- 예: 170 → 17.0V

#### 5.2 설정 쓰기

| 명령 | 설명 | 형식 |
|------|------|------|
| `$LICMD,7,{type},A:...,B:...*CC` | EEPROM 1 쓰기 | 납축전지(A), LiFePO4(B), type=배터리타입(0-3) |
| `$LICMD,9,C:...,D:...*CC` | EEPROM 2 쓰기 | Li-ion(C), LiPo(D) |

**명령 예시:**
```
$LICMD,7,0,A:131141150170180200211,B:150160170180190200210*42
$LICMD,9,C:100200113114115116117,D:211212223224235236247*5B
```

**값 인코딩:**
- 실제값 × 10 → 3자리 정수
- 예: 17.0V → 170

**확인 응답:**
```
$LISTOK*CC  (성공)
```

**쓰기 순서:**
1. EEPROM 1 쓰기 명령 전송
2. $LISTOK 수신 대기
3. EEPROM 2 쓰기 명령 전송
4. $LISTOK 수신 대기
5. settings_write_ack 시그널 발생

---

### 6. 테스트 결과

#### ✅ 정상 동작 확인
- 장비에서 설정 읽기: EEPROM 1, 2 모두 정상 파싱
- UI 표시: 4개 배터리 타입의 28개 값 모두 정확히 표시
- 장비로 설정 쓰기: EEPROM 1, 2 순차 전송
- 값 범위: 0.1 단위 조정, 소수점 1자리 표시

#### 검증된 데이터
**납축전지(A):** 17.0, 16.0, 17.0, 18.0, 19.0, 20.0, 17.0
**LiFePO4(B):** 17.0, 16.2, 17.3, 18.4, 19.5, 20.6, 17.0
**Li-ion(C):** 18.7, 10.2, 10.3, 10.4, 10.5, 10.6, 18.7
**LiPo(D):** 18.7, 11.2, 12.3, 12.4, 13.5, 13.6, 18.7

---

## 최근 업데이트 (2026-01-09)

### UI 개선 및 배터리 타입 파싱 버그 수정

#### 1. 배터리 타입 파싱 버그 수정
**문제 발견:**
- 납축전지(타입 0) 이외의 배터리 타입으로 설정 후 쓰기/읽기 시 값이 맞지 않음
- 배터리 타입 값이 설정한 것과 달라짐

**근본 원인:**
- EEPROM 1 응답이 `$LISTE,{battery_type},A:...,B:...*5E` 형식
- 기존 코드는 `values_str.startswith('0,')`만 체크
- battery_type이 1, 2, 3일 때 파싱 실패

**수정 내용:**
- **nmea_parser.py:186** - EEPROM 1/2 구분: 'A:' 또는 'B:' 존재 여부로 판단
- 첫 번째 쉼표 앞의 숫자를 battery_type으로 추출
- settings.battery_type에 올바른 값 저장
- **serial_worker.py:159** - EEPROM 1/2 구분 로직도 동일하게 수정
  - 기존: `if '0,A:' in sentence or '0,B:' in sentence:`
  - 변경: `if 'A:' in sentence or 'B:' in sentence:`

#### 2. UI 개선
- **Enter 키 버튼 자동 실행 방지**: 모든 버튼에 `setAutoDefault(False)` 적용
- **"적용" 버튼 제거**: 실질적 기능이 없어 제거 (device_settings_dialog.py)
- **배터리 타입 명칭 변경**: "Li-pol" → "LiPo" (전체 파일)
- **중요 버튼 강조** (device_settings_dialog.py:41-97):
  - "장비에서 읽기": 파란색 배경(#2196F3), 흰색 글자, 높이 40px
  - "장비로 쓰기": 주황색 배경(#FF9800), 흰색 글자, 높이 40px
  - 굵은 폰트(11pt), border 추가, hover/pressed/disabled 효과 적용
  - 나머지 버튼은 기본 스타일 유지

#### 3. 디버깅 메시지 추가
시리얼 통신 문제 진단을 위해 상세 디버그 메시지 추가:
- **device_settings_dialog.py**: 버튼 클릭 시그널 추적
- **main_window.py**: 설정 읽기/쓰기 요청 및 응답 핸들러 추적
- **serial_worker.py**:
  - 명령 큐 추가/제거 추적
  - NMEA 명령 생성 및 전송 추적
  - 수신 라인 추적
  - $LISTE 파싱 과정 추적
  - EEPROM 1/2 구분 로직 추적

#### 4. 현재 상태
**완료:**
- 배터리 타입 파싱 로직 수정 (nmea_parser.py, serial_worker.py)
- UI 개선 및 버튼 강조
- 디버그 메시지 추가

**미해결:**
- 시리얼 통신 문제로 "장비에서 읽기" 명령 전송 후 응답 수신 안 됨
- 명령은 큐에 추가되나 실제 전송 여부 미확인
- PC 재부팅 후 재테스트 예정

---

## 이전 업데이트 (2026-01-09 - EEPROM 쓰기 기능 완성)

### EEPROM 쓰기 프로토콜 구현 완료

#### 1. nmea_parser.py 업데이트
- `create_write_eeprom1_command(settings)` 함수 수정
  - battery_type 파라미터 추가
  - 명령 형식: `$LICMD,7,{battery_type},A:...,B:...*CC`
- `parse_listok(sentence)` 함수 추가
  - $LISTOK 응답 검증 및 파싱

#### 2. serial_worker.py 업데이트
- **상태 추적 변수 추가:**
  - `writing_settings` - 설정 쓰기 진행 중 플래그
  - `eeprom1_written` - EEPROM 1 쓰기 완료 플래그

- **$LISTOK 응답 처리 추가:**
  - EEPROM 1 쓰기 완료 시: eeprom1_written = True 설정
  - EEPROM 2 쓰기 완료 시: settings_write_ack 시그널 발생
  - 에러 처리: 파싱 실패 시 적절한 에러 메시지 전달

- **request_write_settings() 메서드 업데이트:**
  - 쓰기 시작 시 상태 초기화 (writing_settings = True)
  - EEPROM 1, 2 명령을 순차적으로 큐에 추가

#### 3. 동작 흐름
```
1. UI에서 "장비로 쓰기" 버튼 클릭
2. DeviceSettingsDialog → write_settings_requested 시그널 발생
3. MainWindow → SerialWorker.request_write_settings() 호출
4. SerialWorker:
   - writing_settings = True, eeprom1_written = False 초기화
   - EEPROM 1 쓰기 명령 큐에 추가: $LICMD,7,{type},A:...,B:...*CC
   - EEPROM 2 쓰기 명령 큐에 추가: $LICMD,9,C:...,D:...*CC
5. 명령 전송 및 응답 처리:
   - EEPROM 1 명령 전송
   - $LISTOK 수신 → eeprom1_written = True
   - EEPROM 2 명령 전송
   - $LISTOK 수신 → settings_write_ack(True, "성공") 시그널 발생
6. MainWindow → QMessageBox로 성공/실패 메시지 표시
```

#### 4. 에러 처리
- $LISTOK 파싱 실패 시
  - writing_settings, eeprom1_written 플래그 초기화
  - error_count 증가
  - settings_write_ack(False, "에러 메시지") 시그널 발생

---

## 다음 작업 계획

1. **설정 프로파일 관리**
   - 여러 설정 세트 관리 (예: "여름용", "겨울용", "테스트용")
   - 프로파일 선택 UI
   - 프로파일 전환 기능

2. **설정값 검증 로직**
   - 필드 간 종속성 체크 (예: 최대 충전 전압 > 부동 충전 전압)
   - 값 범위 경고 표시
   - 실시간 검증 피드백

3. **기타 설정 연동**
   - 현재는 충방전 설정만 EEPROM 연동
   - 기타 탭의 설정도 장비와 연동 필요 시 추가 구현

4. **UI/UX 개선**
   - 설정 변경 이력 추적
   - 변경 사항 비교 기능
   - 툴팁 추가로 각 설정 항목 설명

---

## 참고 사항

- 모든 전압 단위: V (Volt)
- 모든 전류 단위: A (Ampere)
- NMEA 체크섬: XOR 방식
- 시리얼 통신: 9600 baud, 8N1
- UI 업데이트 시 신호 차단 필수 (blockSignals)

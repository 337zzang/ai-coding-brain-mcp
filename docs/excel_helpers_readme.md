# Excel 헬퍼 함수 사용 가이드

AI Coding Brain MCP의 Excel 실시간 작업 헬퍼 함수들을 사용하여 Excel을 자동화할 수 있습니다.

## 설치 요구사항

- Windows 환경
- Microsoft Excel 설치
- pywin32 패키지 (`pip install pywin32`)

## 주요 기능

### 1. 연결 관리
- `excel_connect(file_path=None)` - Excel 연결/생성
- `excel_disconnect(save=True)` - 안전한 연결 해제

### 2. 데이터 작업
- `excel_read_range(sheet, range)` - 범위 데이터 읽기
- `excel_read_table(sheet, start_cell)` - 테이블 형태 읽기
- `excel_write_range(sheet, range, data)` - 데이터 쓰기

### 3. 시트 관리
- `excel_list_sheets()` - 시트 목록 조회
- `excel_add_sheet(name)` - 시트 추가
- `excel_delete_sheet(name)` - 시트 삭제
- `excel_select_sheet(name)` - 시트 선택

### 4. 고급 기능
- `excel_create_pivot(source, target_sheet, target_cell, rows, columns, values)` - 피벗 테이블 생성
- `excel_apply_formula(range, formula, sheet=None)` - 수식 적용

## 사용 예제

### 기본 사용법

```python
import ai_helpers_new as h

# 1. Excel 연결
result = h.excel_connect()  # 새 Excel 창
# 또는
result = h.excel_connect("data.xlsx")  # 특정 파일

# 2. 데이터 쓰기
data = [
    ["이름", "나이", "도시"],
    ["홍길동", 30, "서울"],
    ["김철수", 25, "부산"]
]
h.excel_write_range("Sheet1", "A1", data)

# 3. 데이터 읽기
result = h.excel_read_range("Sheet1", "A1:C3")
print(result['data']['data'])

# 4. 연결 해제
h.excel_disconnect(save=True)
```

### Context Manager 사용

```python
from ai_helpers_new import excel_session

with excel_session("report.xlsx") as manager:
    # 시트 추가
    h.excel_add_sheet("월간보고서")

    # 데이터 작성
    h.excel_write_range("월간보고서", "A1", [["2024년 1월 매출 보고서"]])

    # 수식 적용
    h.excel_apply_formula("B10", "=SUM(B2:B9)")
```

### 기존 Excel 파일 재사용

```python
# 이미 열려있는 Excel 파일에 연결
result = h.excel_connect("C:/data/sales.xlsx")

if result['data']['connected_to_existing']:
    print("기존 열려있는 파일에 연결됨")
else:
    print("새로 파일을 열었음")
```

### 피벗 테이블 생성

```python
# 데이터 준비
sales_data = [
    ["날짜", "제품", "지역", "매출"],
    ["2024-01-01", "A", "서울", 100],
    ["2024-01-01", "B", "서울", 200],
    ["2024-01-02", "A", "부산", 150],
    # ... 더 많은 데이터
]

h.excel_write_range("Sheet1", "A1", sales_data)

# 피벗 테이블 생성
h.excel_create_pivot(
    source_range="Sheet1!A1:D100",
    target_sheet="피벗분석",
    target_cell="A1",
    rows=["지역"],
    columns=["제품"],
    values=["매출"]
)
```

## 주의사항

1. **스레드 안전성**: 모든 함수는 스레드 안전하게 설계되었습니다.
2. **COM 객체 관리**: 작업 완료 후 반드시 `excel_disconnect()`를 호출하세요.
3. **에러 처리**: 모든 함수는 `{'ok': bool, 'data'/'error': ...}` 형식으로 반환합니다.

## 문제 해결

### Excel이 응답하지 않을 때
```python
from ai_helpers_new.excel import get_excel_manager
manager = get_excel_manager()
manager.quit_excel(force=True)  # 강제 종료
```

### COM 오류 발생 시
- Excel 프로세스가 백그라운드에 남아있는지 확인
- 작업 관리자에서 EXCEL.EXE 프로세스 종료
- 컴퓨터 재시작

## 성능 팁

1. 대량 데이터는 한 번에 쓰기
2. CurrentRegion을 활용한 테이블 읽기
3. 수식은 범위로 한 번에 적용

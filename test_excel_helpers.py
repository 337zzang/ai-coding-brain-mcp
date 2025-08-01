"""
Excel 헬퍼 함수 테스트
실제 Excel COM 객체를 사용하는 통합 테스트
"""

import os
import sys
import time

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# AI Helpers 임포트
from python import ai_helpers_new as h

def test_excel_connection():
    """Excel 연결 테스트"""
    print("\n=== Excel 연결 테스트 ===")

    # Excel 연결
    result = h.excel_connect()
    assert result['ok'], f"Excel 연결 실패: {result.get('error')}"
    print("✅ Excel 연결 성공")

    # 연결 해제
    result = h.excel_disconnect()
    assert result['ok'], f"Excel 해제 실패: {result.get('error')}"
    print("✅ Excel 연결 해제 성공")

def test_excel_file_operations():
    """Excel 파일 작업 테스트"""
    print("\n=== Excel 파일 작업 테스트 ===")

    test_file = os.path.join(project_root, "test_excel_data.xlsx")

    # 파일로 연결
    result = h.excel_connect(test_file)
    assert result['ok'], f"Excel 파일 연결 실패: {result.get('error')}"
    print(f"✅ Excel 파일 연결 성공: {test_file}")

    # 시트 목록 확인
    result = h.excel_list_sheets()
    assert result['ok'], f"시트 목록 실패: {result.get('error')}"
    print(f"✅ 시트 목록: {result['data']['sheets']}")

    # 연결 해제 (파일은 열어둠)
    result = h.excel_disconnect(save=True)
    assert result['ok'], f"Excel 해제 실패: {result.get('error')}"
    print("✅ Excel 파일 저장 및 연결 해제")

def test_data_operations():
    """데이터 읽기/쓰기 테스트"""
    print("\n=== 데이터 읽기/쓰기 테스트 ===")

    # Excel 연결
    result = h.excel_connect()
    assert result['ok'], "Excel 연결 실패"

    # 테스트 데이터
    test_data = [
        ["이름", "나이", "도시"],
        ["홍길동", 30, "서울"],
        ["김철수", 25, "부산"],
        ["이영희", 35, "대구"]
    ]

    # 데이터 쓰기
    result = h.excel_write_range("Sheet1", "A1", test_data)
    assert result['ok'], f"데이터 쓰기 실패: {result.get('error')}"
    print(f"✅ 데이터 쓰기 성공: {result['data']['rows_written']}행 x {result['data']['cols_written']}열")

    # 데이터 읽기
    result = h.excel_read_range("Sheet1", "A1:C4")
    assert result['ok'], f"데이터 읽기 실패: {result.get('error')}"
    print(f"✅ 데이터 읽기 성공: {result['data']['data']}")

    # 테이블로 읽기
    result = h.excel_read_table("Sheet1", "A1")
    assert result['ok'], f"테이블 읽기 실패: {result.get('error')}"
    print(f"✅ 테이블 헤더: {result['data']['headers']}")
    print(f"✅ 테이블 데이터: {result['data']['data']}")

    # 연결 해제
    h.excel_disconnect()

def test_sheet_management():
    """시트 관리 테스트"""
    print("\n=== 시트 관리 테스트 ===")

    # Excel 연결
    result = h.excel_connect()
    assert result['ok'], "Excel 연결 실패"

    # 새 시트 추가
    result = h.excel_add_sheet("테스트시트")
    assert result['ok'], f"시트 추가 실패: {result.get('error')}"
    print(f"✅ 시트 추가 성공: {result['data']['sheet_name']}")

    # 시트 선택
    result = h.excel_select_sheet("테스트시트")
    assert result['ok'], f"시트 선택 실패: {result.get('error')}"
    print(f"✅ 시트 선택 성공: {result['data']['selected_sheet']}")

    # 시트 삭제
    result = h.excel_delete_sheet("테스트시트")
    assert result['ok'], f"시트 삭제 실패: {result.get('error')}"
    print(f"✅ 시트 삭제 성공")

    # 연결 해제
    h.excel_disconnect()

def test_formula_application():
    """수식 적용 테스트"""
    print("\n=== 수식 적용 테스트 ===")

    # Excel 연결
    result = h.excel_connect()
    assert result['ok'], "Excel 연결 실패"

    # 테스트 데이터 준비
    data = [[1], [2], [3], [4], [5]]
    result = h.excel_write_range("Sheet1", "A1", data)
    assert result['ok'], "데이터 쓰기 실패"

    # 수식 적용
    result = h.excel_apply_formula("B1", "=A1*2")
    assert result['ok'], f"수식 적용 실패: {result.get('error')}"
    print(f"✅ 단일 셀 수식 적용 성공")

    # 범위에 수식 적용
    result = h.excel_apply_formula("B1:B5", "=A1*2")
    assert result['ok'], f"범위 수식 적용 실패: {result.get('error')}"
    print(f"✅ 범위 수식 적용 성공: {result['data']['cells_affected']}개 셀")

    # 합계 수식
    result = h.excel_apply_formula("A7", "=SUM(A1:A5)")
    assert result['ok'], "합계 수식 적용 실패"
    print("✅ SUM 수식 적용 성공")

    # 연결 해제
    h.excel_disconnect()

def run_all_tests():
    """모든 테스트 실행"""
    print("🧪 Excel 헬퍼 함수 테스트 시작")
    print("=" * 50)

    try:
        test_excel_connection()
        test_excel_file_operations()
        test_data_operations()
        test_sheet_management()
        test_formula_application()

        print("\n✅ 모든 테스트 통과!")

    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
    finally:
        # 정리
        try:
            h.excel_disconnect()
        except:
            pass

if __name__ == "__main__":
    run_all_tests()

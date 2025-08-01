"""
Excel 자동화 예제
AI Coding Brain MCP의 Excel 헬퍼 함수 활용 예제
"""

import os
import sys

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from python import ai_helpers_new as h
from python.ai_helpers_new import excel_session

def example_sales_report():
    """월간 매출 보고서 자동 생성 예제"""
    print("📊 월간 매출 보고서 생성 예제")
    print("=" * 50)

    # Excel 파일 경로
    report_file = os.path.join(project_root, "monthly_sales_report.xlsx")

    # Context Manager로 안전하게 작업
    with excel_session(report_file) as excel:
        print("✅ Excel 연결 성공")

        # 1. 원본 데이터 시트 생성
        print("\n1️⃣ 원본 데이터 입력")

        # 샘플 매출 데이터
        sales_data = [
            ["날짜", "제품", "지역", "판매량", "단가", "매출"],
            ["2024-01-01", "노트북", "서울", 5, 1200000, "=D2*E2"],
            ["2024-01-01", "마우스", "서울", 20, 30000, "=D3*E3"],
            ["2024-01-02", "노트북", "부산", 3, 1200000, "=D4*E4"],
            ["2024-01-02", "키보드", "부산", 10, 80000, "=D5*E5"],
            ["2024-01-03", "노트북", "대구", 4, 1200000, "=D6*E6"],
            ["2024-01-03", "마우스", "대구", 15, 30000, "=D7*E7"],
            ["2024-01-04", "키보드", "서울", 8, 80000, "=D8*E8"],
            ["2024-01-05", "노트북", "부산", 2, 1200000, "=D9*E9"],
        ]

        # 데이터 쓰기
        result = h.excel_write_range("Sheet1", "A1", sales_data)
        if result['ok']:
            print(f"✅ 매출 데이터 입력 완료: {result['data']['rows_written']}행")

        # 수식 적용 (매출 계산)
        h.excel_apply_formula("F2:F9", "=D2*E2")
        print("✅ 매출 계산 수식 적용")

        # 2. 요약 시트 생성
        print("\n2️⃣ 요약 시트 생성")
        h.excel_add_sheet("요약")
        h.excel_select_sheet("요약")

        # 요약 정보
        summary_data = [
            ["월간 매출 요약"],
            [""],
            ["항목", "값"],
            ["총 매출", "=SUM(Sheet1!F2:F9)"],
            ["평균 매출", "=AVERAGE(Sheet1!F2:F9)"],
            ["최대 매출", "=MAX(Sheet1!F2:F9)"],
            ["최소 매출", "=MIN(Sheet1!F2:F9)"],
            ["거래 건수", "=COUNTA(Sheet1!A2:A9)"]
        ]

        h.excel_write_range("요약", "A1", summary_data)
        print("✅ 요약 정보 생성 완료")

        # 3. 피벗 테이블 생성
        print("\n3️⃣ 피벗 테이블 생성")
        try:
            h.excel_add_sheet("피벗분석")

            result = h.excel_create_pivot(
                source_range="Sheet1!A1:F9",
                target_sheet="피벗분석", 
                target_cell="A3",
                rows=["지역"],
                columns=["제품"],
                values=["매출"],
                name="지역별제품매출"
            )

            if result['ok']:
                print("✅ 피벗 테이블 생성 성공")
                print(f"   - 행: {result['data']['row_fields']}")
                print(f"   - 열: {result['data']['column_fields']}")
                print(f"   - 값: {result['data']['value_fields']}")
        except Exception as e:
            print(f"⚠️ 피벗 테이블 생성 실패: {e}")

        # 4. 차트용 데이터 준비
        print("\n4️⃣ 지역별 매출 집계")
        h.excel_add_sheet("지역별매출")
        h.excel_select_sheet("지역별매출")

        region_summary = [
            ["지역별 매출 집계"],
            [""],
            ["지역", "매출"],
            ["서울", "=SUMIF(Sheet1!C:C,\"서울\",Sheet1!F:F)"],
            ["부산", "=SUMIF(Sheet1!C:C,\"부산\",Sheet1!F:F)"],
            ["대구", "=SUMIF(Sheet1!C:C,\"대구\",Sheet1!F:F)"],
            [""],
            ["합계", "=SUM(B4:B6)"]
        ]

        h.excel_write_range("지역별매출", "A1", region_summary)
        print("✅ 지역별 매출 집계 완료")

        print("\n✅ 월간 매출 보고서 생성 완료!")
        print(f"📁 파일 위치: {report_file}")

def example_data_analysis():
    """데이터 분석 자동화 예제"""
    print("\n📈 데이터 분석 자동화 예제")
    print("=" * 50)

    # 간단한 성적 분석
    with excel_session() as excel:
        # 학생 성적 데이터
        grades_data = [
            ["학생", "국어", "영어", "수학", "과학", "평균", "등급"],
            ["홍길동", 85, 90, 78, 82, "=AVERAGE(B2:E2)", "=IF(F2>=90,\"A\",IF(F2>=80,\"B\",IF(F2>=70,\"C\",\"D\")))"],
            ["김철수", 92, 88, 95, 90, "=AVERAGE(B3:E3)", "=IF(F3>=90,\"A\",IF(F3>=80,\"B\",IF(F3>=70,\"C\",\"D\")))"],
            ["이영희", 78, 85, 88, 79, "=AVERAGE(B4:E4)", "=IF(F4>=90,\"A\",IF(F4>=80,\"B\",IF(F4>=70,\"C\",\"D\")))"],
            ["박민수", 88, 82, 85, 87, "=AVERAGE(B5:E5)", "=IF(F5>=90,\"A\",IF(F5>=80,\"B\",IF(F5>=70,\"C\",\"D\")))"],
            ["정수진", 95, 93, 92, 94, "=AVERAGE(B6:E6)", "=IF(F6>=90,\"A\",IF(F6>=80,\"B\",IF(F6>=70,\"C\",\"D\")))"],
        ]

        # 데이터 입력
        h.excel_write_range("Sheet1", "A1", grades_data)
        print("✅ 성적 데이터 입력 완료")

        # 평균 및 등급 수식 적용
        h.excel_apply_formula("F2:F6", "=AVERAGE(B2:E2)")
        h.excel_apply_formula("G2:G6", '=IF(F2>=90,"A",IF(F2>=80,"B",IF(F2>=70,"C","D")))')
        print("✅ 평균 및 등급 계산 완료")

        # 과목별 통계
        h.excel_write_range("Sheet1", "A8", [
            [""],
            ["과목별 통계"],
            ["과목", "평균", "최고", "최저"],
            ["국어", "=AVERAGE(B2:B6)", "=MAX(B2:B6)", "=MIN(B2:B6)"],
            ["영어", "=AVERAGE(C2:C6)", "=MAX(C2:C6)", "=MIN(C2:C6)"],
            ["수학", "=AVERAGE(D2:D6)", "=MAX(D2:D6)", "=MIN(D2:D6)"],
            ["과학", "=AVERAGE(E2:E6)", "=MAX(E2:E6)", "=MIN(E2:E6)"],
        ])
        print("✅ 과목별 통계 생성 완료")

def example_batch_processing():
    """여러 Excel 파일 일괄 처리 예제"""
    print("\n📁 Excel 파일 일괄 처리 예제")
    print("=" * 50)

    # 테스트용 파일들 생성
    test_files = ["sales_jan.xlsx", "sales_feb.xlsx", "sales_mar.xlsx"]

    for i, filename in enumerate(test_files, 1):
        filepath = os.path.join(project_root, filename)

        # 각 파일에 연결
        result = h.excel_connect(filepath)
        if result['ok']:
            print(f"\n✅ {filename} 처리 중...")

            # 샘플 데이터 생성
            sample_data = [
                ["날짜", "매출"],
                [f"2024-{i:02d}-01", 1000000 + i * 100000],
                [f"2024-{i:02d}-15", 1500000 + i * 150000],
                [f"2024-{i:02d}-30", 2000000 + i * 200000],
            ]

            h.excel_write_range("Sheet1", "A1", sample_data)

            # 합계 추가
            h.excel_write_range("Sheet1", "A6", [["합계", "=SUM(B2:B4)"]])

            # 저장하고 닫기
            h.excel_disconnect(save=True)
            print(f"   ✅ {filename} 생성 완료")

def run_all_examples():
    """모든 예제 실행"""
    try:
        example_sales_report()
        example_data_analysis()
        example_batch_processing()

        print("\n✅ 모든 예제 실행 완료!")

    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_examples()

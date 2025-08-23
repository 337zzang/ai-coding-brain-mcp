
def execute_with_think(code):
    """코드 실행 후 자동으로 Think 프롬프트 추가"""
    import sys
    from io import StringIO

    # 코드 실행
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        exec(code, globals())
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    # 결과와 Think 프롬프트 함께 반환
    result = output + """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤔 실행 완료 - Think 도구로 결과를 분석하세요
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Think 도구를 사용하여:
- 실행 결과 검증
- 패턴 분석
- 다음 단계 계획
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(result)
    return result

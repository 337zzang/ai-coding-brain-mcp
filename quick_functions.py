# Quick 함수 정의 - REPL 친화적 단축 명령어
def qs(pattern):
    """Quick search - 코드에서 패턴 검색"""
    return helpers.search_code(".", pattern)

def qfind(path, pattern):
    """Quick find - 파일 이름으로 검색"""  
    return helpers.search_files(path, pattern)

def qc(pattern):
    """Quick current - 현재 디렉토리에서 코드 검색"""
    return helpers.search_code(".", pattern)

def qv(file, func):
    """Quick view - 특정 함수 코드 보기"""
    # ez_view가 없다면 대체 구현
    try:
        return helpers.ez_view(file, func)
    except:
        # 대체 구현
        parse_result = helpers.parse_file(file)
        if isinstance(parse_result, dict):
            functions = parse_result.get('functions', {})
        else:
            functions = parse_result.functions

        if func in functions:
            print(f"\n📄 {file} - {func}():")
            print(functions[func])
        else:
            print(f"❌ '{func}' 함수를 {file}에서 찾을 수 없습니다.")

def qproj():
    """Quick project - 현재 프로젝트 정보 표시"""
    current = helpers.get_current_project()
    print(f"\n📁 프로젝트: {current['name']}")
    print(f"📍 경로: {current['path']}")

    # 추가 정보
    if helpers.file_exists(".workflow.json"):
        wf_data = helpers.read_json(".workflow.json")
        tasks = wf_data.get('tasks', [])
        pending = [t for t in tasks if not t.get('completed')]
        print(f"📋 대기 작업: {len(pending)}개")

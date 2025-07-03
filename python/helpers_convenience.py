
# 🔥 편의 함수: 전역 wrapped_helpers 생성
def init_wrapped_helpers():
    """전역 wrapped_helpers 초기화"""
    import builtins
    from helpers_wrapper import HelpersWrapper
    
    # helpers 찾기
    if 'helpers' in globals():
        wrapped = HelpersWrapper(globals()['helpers'])
    elif 'helpers' in builtins.__dict__:
        wrapped = HelpersWrapper(builtins.__dict__['helpers'])
    else:
        # JSON REPL 환경에서 helpers 찾기
        import sys
        frame = sys._getframe()
        while frame:
            if 'helpers' in frame.f_globals:
                wrapped = HelpersWrapper(frame.f_globals['helpers'])
                break
            frame = frame.f_back
        else:
            raise ValueError("helpers를 찾을 수 없습니다")
    
    # 전역 변수로 설정
    globals()['wrapped_helpers'] = wrapped
    globals()['w'] = wrapped  # 짧은 별칭
    
    print("✅ wrapped_helpers 초기화 완료!")
    print("   사용법: wrapped_helpers.메서드() 또는 w.메서드()")
    return wrapped

# 사용 예시
if __name__ == "__main__":
    # 초기화
    w = init_wrapped_helpers()
    
    # 예시 1: 파일 읽기 (에러 처리 간편화)
    result = w.read_file('some_file.py')
    if result['success']:
        print(f"파일 내용: {result['data'][:100]}...")
    else:
        print(f"오류: {result['error']}")
    
    # 예시 2: 코드 블록 교체 (성공 여부 확인 간편화)
    result = w.replace_block('file.py', 'func_name', 'new code')
    if result['success']:
        print("✅ 코드 교체 성공!")
    else:
        print(f"❌ 코드 교체 실패: {result['data']}")
    
    # 예시 3: 파일 검색 (결과 개수 바로 확인)
    result = w.search_files_advanced('.', '*.py')
    print(f"찾은 파일: {result['found_count']}개")
    
    # 예시 4: Git 상태 (간편한 정보 접근)
    result = w.git_status()
    print(f"수정된 파일: {result['modified_count']}개")
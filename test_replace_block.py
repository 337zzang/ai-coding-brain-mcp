"""replace_block 함수 문제 분석 스크립트"""

def analyze_replace_block():
    # 1. 정확한 매칭 문제
    print("="*50)
    print("1. 정확한 매칭 문제 분석")
    print("="*50)
    
    # 원본 코드 (수정하려던 부분)
    old_code = """            # 워크플로우/히스토리 매니저 재초기화
            self._workflow_manager = None
            self._history_manager = None"""
    
    # 파일에서 읽은 실제 코드
    with open("python/json_repl_session.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    # 문자열이 있는지 확인
    if old_code in content:
        print("✅ 정확한 매칭 성공")
    else:
        print("❌ 정확한 매칭 실패")
        
        # 각 줄이 있는지 확인
        lines = old_code.split('\n')
        for i, line in enumerate(lines):
            if line in content:
                print(f"  ✅ 라인 {i+1} 있음: {repr(line[:50])}")
            else:
                print(f"  ❌ 라인 {i+1} 없음: {repr(line[:50])}")
                
        # 줄바꿈 문자 확인
        print("\n줄바꿈 문자:")
        print(f"  - old_code: {repr(old_code[:50])}")
        
        # 파일에서 해당 부분 찾기
        search_text = "워크플로우/히스토리 매니저 재초기화"
        if search_text in content:
            idx = content.index(search_text)
            print(f"\n실제 파일 내용 (위치 {idx}):")
            print(repr(content[idx-50:idx+150]))
            
    # 2. 들여쓰기 문제
    print("\n" + "="*50)
    print("2. 들여쓰기 문제 분석")
    print("="*50)
    
    # 탭 vs 스페이스
    if '\t' in content:
        print("⚠️ 파일에 탭 문자 있음")
    else:
        print("✅ 파일에 탭 문자 없음 (스페이스만 사용)")
        
    # Windows vs Unix 줄바꿈
    if '\r\n' in content:
        print("⚠️ Windows 줄바꿈 (\\r\\n) 사용")
    else:
        print("✅ Unix 줄바꿈 (\\n) 사용")

if __name__ == "__main__":
    analyze_replace_block()

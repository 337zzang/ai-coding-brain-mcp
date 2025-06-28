#!/usr/bin/env python3
"""
하드코딩된 경로 수정 스크립트
Wisdom System 자동 수정 기능 없이 실행
"""
import os
import sys

def fix_python_path():
    """python-path.ts 파일의 잘못된 경로 수정"""
    file_path = "src/utils/python-path.ts"
    
    print(f"📝 {file_path} 수정 중...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 수정할 내용 확인
        if "'C:os.path.join" in content:
            print("  🔍 잘못된 경로 발견")
            
            # 잘못된 경로를 올바른 경로로 교체
            content = content.replace(
                "'C:os.path.join(os.path.join(\", \"))Python312os.path.join(os.path.join(\", \"))python.exe'",
                "'C:\\\\Python312\\\\python.exe'"
            )
            content = content.replace(
                "'C:os.path.join(\", \")Python311os.path.join(\", \")python.exe'",
                "'C:\\\\Python311\\\\python.exe'"
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ {file_path} 수정 완료")
        else:
            print("  ✅ 이미 수정됨")
            
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        return False
    
    return True

def fix_git_handlers():
    """git-handlers.ts 파일의 Administrator 하드코딩 제거"""
    file_path = "src/handlers/git-handlers.ts"
    
    print(f"\n📝 {file_path} 수정 중...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Administrator 하드코딩이 포함된 라인 제거
        new_lines = []
        removed = 0
        for line in lines:
            if 'C:\\\\Users\\\\Administrator\\\\Desktop\\\\ai-coding-brain-mcp' not in line:
                new_lines.append(line)
            else:
                removed += 1
                print(f"  ❌ 제거: {line.strip()}")
        
        if removed > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"  ✅ {file_path} 수정 완료 ({removed}개 라인 제거)")
        else:
            print("  ✅ 이미 수정됨")
            
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        return False
    
    return True

def main():
    """메인 함수"""
    print("🔧 하드코딩된 경로 수정 시작...\n")
    
    # 현재 디렉토리 확인
    current_dir = os.getcwd()
    if not current_dir.endswith('ai-coding-brain-mcp'):
        print(f"❌ 잘못된 디렉토리: {current_dir}")
        print("ai-coding-brain-mcp 프로젝트 루트에서 실행하세요.")
        sys.exit(1)
    
    # 파일 수정
    success = True
    success &= fix_python_path()
    success &= fix_git_handlers()
    
    if success:
        print("\n✅ 모든 수정 완료!")
        print("\n다음 명령어로 TypeScript를 컴파일하세요:")
        print("  npx tsc")
    else:
        print("\n❌ 일부 수정 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()

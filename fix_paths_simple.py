#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
하드코딩된 경로 수정 스크립트
"""
import os
import sys

def fix_python_path():
    """python-path.ts 파일의 잘못된 경로 수정"""
    file_path = "src/utils/python-path.ts"
    
    print("[INFO] Fixing python-path.ts...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 수정할 내용 확인
        if "'C:os.path.join" in content:
            print("  Found incorrect paths")
            
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
            print("  [OK] python-path.ts fixed")
        else:
            print("  [OK] Already fixed")
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False
    
    return True

def fix_git_handlers():
    """git-handlers.ts 파일의 Administrator 하드코딩 제거"""
    file_path = "src/handlers/git-handlers.ts"
    
    print("\n[INFO] Fixing git-handlers.ts...")
    
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
                print(f"  Removing: {line.strip()}")
        
        if removed > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"  [OK] git-handlers.ts fixed ({removed} lines removed)")
        else:
            print("  [OK] Already fixed")
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False
    
    return True

def main():
    """메인 함수"""
    print("Fixing hardcoded paths...\n")
    
    # 현재 디렉토리 확인
    current_dir = os.getcwd()
    if not current_dir.endswith('ai-coding-brain-mcp'):
        print(f"[ERROR] Wrong directory: {current_dir}")
        print("Please run from ai-coding-brain-mcp project root.")
        sys.exit(1)
    
    # 파일 수정
    success = True
    success &= fix_python_path()
    success &= fix_git_handlers()
    
    if success:
        print("\n[SUCCESS] All fixes completed!")
        print("\nNext, compile TypeScript with:")
        print("  npx tsc")
    else:
        print("\n[ERROR] Some fixes failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

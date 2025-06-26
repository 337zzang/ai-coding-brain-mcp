#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 명령어를 기존 파일에 적용하는 스크립트
"""

import os
import shutil
from datetime import datetime

def apply_improvements():
    """개선된 파일들을 기존 위치에 복사"""
    
    # 백업 디렉토리 생성
    backup_dir = f"python/commands/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 파일 매핑
    file_mappings = [
        ("python/commands/improved/plan_improved.py", "python/commands/plan.py"),
        ("python/commands/improved/task_improved.py", "python/commands/task.py"),
        ("python/commands/improved/next_improved.py", "python/commands/next.py"),
    ]
    
    print("[*] 개선된 명령어 적용 시작\n")
    
    for src, dst in file_mappings:
        if os.path.exists(src):
            # 기존 파일 백업
            if os.path.exists(dst):
                backup_path = os.path.join(backup_dir, os.path.basename(dst))
                shutil.copy2(dst, backup_path)
                print(f"[+] 백업: {dst} -> {backup_path}")
            
            # 개선된 파일 복사
            shutil.copy2(src, dst)
            print(f"[+] 적용: {src} -> {dst}")
            
            # import 문 수정 (improved 디렉토리 참조 제거)
            with open(dst, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # import 수정
            content = content.replace("from commands.improved.plan_improved", "from commands.plan")
            content = content.replace("from commands.improved.task_improved", "from commands.task")
            content = content.replace("from commands.improved.next_improved", "from commands.next")
            content = content.replace("from plan_improved", "from commands.plan")
            content = content.replace("from task_improved", "from commands.task")
            content = content.replace("from next_improved", "from commands.next")
            
            with open(dst, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"[+] import 문 수정 완료: {dst}")
        else:
            print(f"[-] 소스 파일 없음: {src}")
    
    # next.py 파일 생성 (없을 경우)
    if not os.path.exists("python/commands/next.py"):
        # next_improved.py의 내용으로 next.py 생성
        if os.path.exists("python/commands/improved/next_improved.py"):
            shutil.copy2("python/commands/improved/next_improved.py", "python/commands/next.py")
            print("[+] next.py 파일 생성")
            
            # import 수정
            with open("python/commands/next.py", 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = content.replace("from plan_improved", "from commands.plan")
            content = content.replace("from task_improved", "from commands.task")
            
            with open("python/commands/next.py", 'w', encoding='utf-8') as f:
                f.write(content)
    
    print(f"\n[+] 모든 개선사항이 적용되었습니다!")
    print(f"[*] 백업 위치: {backup_dir}")
    
    # 개선 내용 요약
    print("\n[*] 개선 내용:")
    print("1. ProjectContext와 dict 모두 지원")
    print("2. Plan 객체와 dict 간 자동 변환")
    print("3. 안전한 속성 접근 (get_plan, set_plan 등)")
    print("4. 작업 큐 관리 개선")
    print("5. 에러 처리 강화")
    
    print("\n[*] 사용 방법:")
    print("- plan '계획명' '설명' - 새 계획 생성")
    print("- task add phase-1 '작업명' '설명' - 작업 추가")
    print("- next - 다음 작업 시작")
    print("- task done - 현재 작업 완료")
    print("- task list - 전체 작업 목록")


if __name__ == "__main__":
    # 현재 디렉토리가 프로젝트 루트인지 확인
    if not os.path.exists("python/commands"):
        print("[-] python/commands 디렉토리를 찾을 수 없습니다.")
        print("프로젝트 루트 디렉토리에서 실행하세요.")
    else:
        apply_improvements()

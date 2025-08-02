#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
json_repl_session.py에서 레거시 스텁을 제거하는 스크립트
"""
import os
import re
import shutil
from datetime import datetime

def remove_legacy_stubs(filepath):
    """레거시 스텁 관련 코드 제거"""

    # 백업 생성
    backup_path = f"{filepath}.legacy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"[BACKUP] Created: {backup_path}")

    # 파일 읽기
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 레거시 관련 부분 찾기 및 제거
    lines = content.split('\n')
    new_lines = []
    skip_mode = False
    in_load_helpers = False
    load_helpers_indent = 0

    for i, line in enumerate(lines):
        # create_legacy_stub 함수 정의 제거
        if 'def create_legacy_stub' in line:
            skip_mode = True
            continue

        # _legacy_warnings 변수 제거
        if '_legacy_warnings = set()' in line:
            continue

        # load_helpers 함수 내부 처리
        if 'def load_helpers' in line:
            in_load_helpers = True
            load_helpers_indent = len(line) - len(line.lstrip())
            new_lines.append(line)
            continue

        if in_load_helpers:
            current_indent = len(line) - len(line.lstrip())

            # 함수 끝 감지
            if line.strip() and current_indent == load_helpers_indent and i > 0:
                in_load_helpers = False

            # 레거시 관련 코드 제거
            if any(keyword in line for keyword in [
                'legacy_functions', 'create_legacy_stub', 
                'for func_name in legacy_functions',
                'if hasattr(h, func_name)',
                '# 레거시 호환성을 위한',
                '# 가장 자주 사용되는 함수들만',
                '# 스텁 함수 생성 및 등록',
                '# 실제로 존재하는 함수만'
            ]):
                continue

        # skip_mode 해제
        if skip_mode:
            if line and not line[0].isspace():
                skip_mode = False
            else:
                continue

        new_lines.append(line)

    # 새 내용으로 저장
    new_content = '\n'.join(new_lines)

    # 불필요한 빈 줄 정리
    new_content = re.sub(r'\n\n\n+', '\n\n', new_content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"[OK] Legacy stubs removed from {filepath}")

    # 변경 내용 요약
    original_lines = len(lines)
    new_line_count = len(new_content.split('\n'))
    print(f"[SUMMARY] Lines removed: {original_lines - new_line_count}")

if __name__ == "__main__":
    # json_repl_session.py 경로
    target_file = os.path.join(
        os.path.expanduser("~"),
        "Desktop",
        "ai-coding-brain-mcp",
        "python",
        "json_repl_session.py"
    )

    if os.path.exists(target_file):
        remove_legacy_stubs(target_file)
    else:
        print(f"[ERROR] File not found: {target_file}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Helpers 레거시 패턴을 h.* 패턴으로 자동 전환하는 스크립트
"""
import re
import os
import glob
import shutil
from datetime import datetime
import sys

# UTF-8 인코딩 설정
if sys.platform == 'win32':
    import locale
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# 전환할 함수 목록
FUNCTIONS_TO_MIGRATE = [
    # 파일 작업
    'read', 'write', 'append', 'read_json', 'write_json', 'exists',
    'scan_directory', 'get_file_info',

    # 코드 분석
    'parse', 'view', 'replace', 'insert', 'functions', 'classes',

    # 검색
    'search_files', 'search_code', 'find_function', 'find_class', 'grep',

    # Git
    'git_status', 'git_add', 'git_commit', 'git_push', 'git_pull',
    'git_branch', 'git_log', 'git_diff', 'git_checkout', 'git_checkout_b',
    'git_stash', 'git_stash_pop', 'git_reset_hard', 'git_merge',

    # LLM
    'ask_o3_async', 'check_o3_status', 'get_o3_result', 'show_o3_progress',
    'ask_o3_practical', 'O3ContextBuilder', 'quick_o3_context',

    # Flow & 프로젝트
    'flow', 'create_task_logger', 'get_current_project', 
    'flow_project_with_workflow', 'get_flow_manager',

    # 웹 자동화
    'web_start', 'web_goto', 'web_click', 'web_type', 'web_extract',

    # Excel
    'excel_connect', 'excel_disconnect', 'excel_read_range', 'excel_write_range'
]

class CodeMigrator:
    def __init__(self):
        self.changes_log = []
        self.error_log = []
        self.backup_dir = f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def create_backup(self, filepath):
        """파일 백업 생성"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        rel_path = os.path.relpath(filepath)
        backup_path = os.path.join(self.backup_dir, rel_path)

        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(filepath, backup_path)

    def should_skip_file(self, filepath):
        """스킵해야 할 파일 판단"""
        skip_patterns = [
            'json_repl_session.py',  # 이미 수정됨
            'migration_',            # 마이그레이션 스크립트
            '__pycache__',          # 캐시 폴더
            '.git',                 # Git 폴더
            'backup',               # 백업 폴더
        ]

        for pattern in skip_patterns:
            if pattern in filepath:
                return True
        return False

    def migrate_line(self, line, line_num, filepath):
        """한 줄씩 마이그레이션"""
        original_line = line
        changes = []

        # 이미 h.로 시작하는 경우 스킵
        if 'h.' in line:
            return line, []

        # import 문은 스킵
        if line.strip().startswith(('import ', 'from ')):
            return line, []

        # 함수 정의는 스킵 (def read(...))
        if re.match(r'^\s*def\s+\w+\s*\(', line):
            return line, []

        # 각 함수에 대해 패턴 매칭 및 치환
        for func in FUNCTIONS_TO_MIGRATE:
            # 정확한 함수 호출 패턴 매칭
            # \b는 단어 경계를 의미 (readfile은 매칭 안됨)
            pattern = rf'\b{func}\s*\('

            if re.search(pattern, line):
                # 치환
                new_line = re.sub(pattern, f'h.{func}(', line)
                if new_line != line:
                    changes.append({
                        'function': func,
                        'line_num': line_num,
                        'old': line.strip(),
                        'new': new_line.strip()
                    })
                    line = new_line

        return line, changes

    def migrate_file(self, filepath):
        """파일 전체 마이그레이션"""
        if self.should_skip_file(filepath):
            return 0

        try:
            # 파일 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 백업 생성
            self.create_backup(filepath)

            # 마이그레이션
            new_lines = []
            file_changes = []

            for line_num, line in enumerate(lines, 1):
                new_line, changes = self.migrate_line(line, line_num, filepath)
                new_lines.append(new_line)
                file_changes.extend(changes)

            # 변경사항이 있으면 파일 저장
            if file_changes:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)

                self.changes_log.append({
                    'file': filepath,
                    'changes': file_changes,
                    'count': len(file_changes)
                })

                return len(file_changes)

        except Exception as e:
            self.error_log.append({
                'file': filepath,
                'error': str(e)
            })

        return 0

    def migrate_project(self, root_dir):
        """프로젝트 전체 마이그레이션"""
        print(f"[MIGRATION] Starting migration: {root_dir}")
        print(f"[BACKUP] Backup folder: {self.backup_dir}\n")

        total_files = 0
        total_changes = 0

        # Python 파일 찾기
        for pattern in ['**/*.py', '**/*.pyw']:
            for filepath in glob.glob(os.path.join(root_dir, pattern), recursive=True):
                changes = self.migrate_file(filepath)
                if changes > 0:
                    total_files += 1
                    total_changes += changes
                    print(f"[OK] {os.path.relpath(filepath)}: {changes} changes")

        # 결과 요약
        print(f"\n[SUMMARY] Migration completed:")
        print(f"  - Modified files: {total_files}")
        print(f"  - Total changes: {total_changes}")
        print(f"  - Backup location: {self.backup_dir}")

        if self.error_log:
            print(f"\n[WARNING] Errors in {len(self.error_log)} files:")
            for error in self.error_log:
                print(f"  - {error['file']}: {error['error']}")

        return total_files, total_changes

    def generate_report(self, output_file="migration_report.md"):
        """상세 리포트 생성"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# AI Helpers Migration Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Summary\n")
            f.write(f"- Modified files: {len(self.changes_log)}\n")
            f.write(f"- Total changes: {sum(log['count'] for log in self.changes_log)}\n")
            f.write(f"- Backup folder: `{self.backup_dir}`\n\n")

            f.write("## Detailed Changes\n\n")
            for log in self.changes_log:
                f.write(f"### {log['file']}\n")
                f.write(f"Changes: {log['count']}\n\n")

                for change in log['changes'][:5]:  # 처음 5개만 표시
                    f.write(f"**Line {change['line_num']}**: `{change['function']}` function\n")
                    f.write(f"- Before: `{change['old']}`\n")
                    f.write(f"- After: `{change['new']}`\n\n")

                if log['count'] > 5:
                    f.write(f"... and {log['count'] - 5} more changes\n\n")

        print(f"\n[REPORT] Detailed report generated: {output_file}")

if __name__ == "__main__":
    migrator = CodeMigrator()

    # 프로젝트 루트 경로
    project_root = os.path.join(os.path.expanduser("~"), "Desktop", "ai-coding-brain-mcp")

    # Python 폴더 마이그레이션
    python_dir = os.path.join(project_root, "python")
    if os.path.exists(python_dir):
        migrator.migrate_project(python_dir)
        migrator.generate_report()
    else:
        print(f"[ERROR] Directory not found: {python_dir}")

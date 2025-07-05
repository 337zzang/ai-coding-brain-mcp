#!/usr/bin/env python3
"""
Search API 자동 마이그레이션 스크립트
기존 search 함수 호출을 새로운 표준 API로 자동 변환
"""

import os
import re
import shutil
from datetime import datetime
from typing import List, Tuple


class SearchAPIMigrator:
    """Search API 마이그레이션 도구"""

    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.changes = []

        # 변환 패턴 정의
        self.patterns = [
            # search_files_advanced → list_file_paths
            (
                r"(\w+)\s*=\s*helpers\.search_files_advanced\((.*?)\)",
                r"\1 = helpers.list_file_paths(\2)",
                "search_files_advanced → list_file_paths"
            ),
            # result.data['results'] → result.data['paths'] (for file search)
            (
                r"(\w+)\.data\['results'\]\s*(.*)\s*#\s*from search_files_advanced",
                r"\1.data['paths']\2  # migrated",
                "results → paths (file search)"
            ),
            # search_code_content → grep_code
            (
                r"(\w+)\s*=\s*helpers\.search_code_content\((.*?)\)",
                r"\1 = helpers.grep_code(\2)",
                "search_code_content → grep_code"
            ),
            # scan_directory_dict → scan_dir
            (
                r"(\w+)\s*=\s*helpers\.scan_directory_dict\((.*?)\)",
                r"\1 = helpers.scan_dir(\2, as_dict=True)",
                "scan_directory_dict → scan_dir"
            ),
        ]

        # 추가 수정이 필요한 패턴
        self.manual_review_patterns = [
            (r"for\s+\w+\s+in\s+\w+\.data\['results'\]:", "List iteration on results"),
            (r"\w+\.data\['results'\]\.items\(\)", "Dict iteration on results"),
            (r"\w+\['path'\]", "Accessing path from file info"),
        ]

    def migrate_file(self, filepath: str) -> bool:
        """단일 파일 마이그레이션"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            file_changes = []

            # 자동 변환 패턴 적용
            for pattern, replacement, description in self.patterns:
                new_content, count = re.subn(pattern, replacement, content)
                if count > 0:
                    content = new_content
                    file_changes.append(f"{description} ({count} occurrences)")

            # 수동 검토가 필요한 부분 확인
            manual_reviews = []
            for pattern, description in self.manual_review_patterns:
                if re.search(pattern, content):
                    manual_reviews.append(description)

            # 변경사항이 있으면 처리
            if content != original_content:
                if not self.dry_run:
                    # 백업 생성
                    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(filepath, backup_path)

                    # 파일 업데이트
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)

                self.changes.append({
                    'file': filepath,
                    'changes': file_changes,
                    'manual_reviews': manual_reviews
                })
                return True

            return False

        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")
            return False

    def migrate_project(self, root_dir: str, file_pattern: str = "*.py"):
        """프로젝트 전체 마이그레이션"""
        print(f"🔍 Scanning {root_dir} for {file_pattern} files...")

        # 파일 찾기
        py_files = []
        for dirpath, _, filenames in os.walk(root_dir):
            # Skip 디렉토리
            if any(skip in dirpath for skip in ['.git', '__pycache__', 'node_modules', 'venv']):
                continue

            for filename in filenames:
                if filename.endswith('.py'):
                    py_files.append(os.path.join(dirpath, filename))

        print(f"📄 Found {len(py_files)} Python files")

        # 각 파일 처리
        migrated_count = 0
        for filepath in py_files:
            if self.migrate_file(filepath):
                migrated_count += 1

        # 결과 출력
        self.print_summary(migrated_count)

    def print_summary(self, migrated_count: int):
        """마이그레이션 요약 출력"""
        print(f"\n{'='*60}")
        print(f"🎯 Migration Summary {'(DRY RUN)' if self.dry_run else ''}")
        print(f"{'='*60}")
        print(f"✅ Files to be migrated: {migrated_count}")

        if self.changes:
            print(f"\n📋 Detailed Changes:")
            for change in self.changes[:10]:  # 처음 10개만 표시
                print(f"\n📄 {change['file']}:")
                for c in change['changes']:
                    print(f"  ✓ {c}")
                if change['manual_reviews']:
                    print(f"  ⚠️  Manual review needed:")
                    for mr in change['manual_reviews']:
                        print(f"    - {mr}")

            if len(self.changes) > 10:
                print(f"\n... and {len(self.changes) - 10} more files")

        if self.dry_run:
            print(f"\n💡 This was a dry run. Use --apply to make actual changes.")


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate search API usage')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run)')
    parser.add_argument('--path', default='.', help='Project root path')
    args = parser.parse_args()

    migrator = SearchAPIMigrator(dry_run=not args.apply)
    migrator.migrate_project(args.path)


if __name__ == "__main__":
    main()

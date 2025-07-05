#!/usr/bin/env python3
"""
Git Helper Script for AI Coding Brain MCP
Git 작업을 안전하고 쉽게 수행하기 위한 헬퍼 스크립트
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional

class GitHelper:
    """Git 작업을 위한 헬퍼 클래스"""

    def __init__(self):
        self.git_path = self._find_git()
        self.encoding = 'cp949' if sys.platform == 'win32' else 'utf-8'
        self.work_dir = os.getcwd()

    def _find_git(self) -> Optional[str]:
        """Git 실행 파일 찾기"""
        # Windows Git 경로들
        if sys.platform == 'win32':
            possible_paths = [
                r"C:\Program Files\Git\cmd\git.exe",
                r"C:\Program Files\Git\bin\git.exe",
                r"C:\Program Files (x86)\Git\cmd\git.exe",
                r"C:\Program Files (x86)\Git\bin\git.exe",
            ]

            # 사용자 로컬 설치 경로 추가
            user_home = os.path.expanduser("~")
            possible_paths.extend([
                os.path.join(user_home, "AppData\Local\Programs\Git\cmd\git.exe"),
                os.path.join(user_home, "scoop\shims\git.exe"),
            ])

            for path in possible_paths:
                if os.path.exists(path):
                    return path

        # which/where 명령으로 찾기
        try:
            cmd = 'where git' if sys.platform == 'win32' else 'which git'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip().split('\n')[0]
        except:
            pass

        # 기본값
        return 'git'

    def _check_lock_file(self) -> bool:
        """Git lock 파일 확인 및 제거"""
        lock_file = os.path.join(self.work_dir, '.git', 'index.lock')
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print("🔓 Git lock 파일 제거됨")
                return True
            except Exception as e:
                print(f"❌ Lock 파일 제거 실패: {e}")
                return False
        return True

    def run_command(self, args: str) -> Tuple[bool, str, str]:
        """Git 명령 실행"""
        # Lock 파일 확인
        self._check_lock_file()

        # 명령 구성
        if self.git_path and os.path.exists(self.git_path):
            cmd = f'"{self.git_path}" {args}'
        else:
            cmd = f'git {args}'

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding=self.encoding,
                cwd=self.work_dir
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def status(self) -> dict:
        """Git 상태 확인"""
        success, stdout, stderr = self.run_command('status --porcelain')
        if success:
            lines = stdout.strip().split('\n') if stdout.strip() else []
            modified = [l[3:] for l in lines if l.startswith(' M')]
            added = [l[3:] for l in lines if l.startswith('A ')]
            deleted = [l[3:] for l in lines if l.startswith(' D')]
            untracked = [l[3:] for l in lines if l.startswith('??')]

            return {
                'success': True,
                'modified': modified,
                'added': added,
                'deleted': deleted,
                'untracked': untracked,
                'total_changes': len(lines)
            }
        return {'success': False, 'error': stderr}

    def add(self, files: str = '.') -> dict:
        """파일 추가"""
        success, stdout, stderr = self.run_command(f'add {files}')
        return {
            'success': success,
            'message': 'Files added successfully' if success else stderr
        }

    def commit(self, message: str) -> dict:
        """커밋 생성"""
        # 메시지에 큰따옴표가 있으면 이스케이프
        message = message.replace('"', '\"')
        success, stdout, stderr = self.run_command(f'commit -m "{message}"')

        if success:
            # 커밋 해시 추출
            import re
            match = re.search(r'\[\w+ ([a-f0-9]+)\]', stdout)
            commit_hash = match.group(1) if match else 'unknown'
            return {
                'success': True,
                'commit_hash': commit_hash,
                'message': stdout
            }
        elif 'nothing to commit' in stdout or 'nothing to commit' in stderr:
            return {
                'success': True,
                'message': 'Nothing to commit, working tree clean'
            }
        else:
            return {
                'success': False,
                'error': stderr
            }

    def push(self, remote: str = 'origin', branch: str = None) -> dict:
        """Push 수행"""
        if not branch:
            # 현재 브랜치 가져오기
            success, stdout, _ = self.run_command('branch --show-current')
            branch = stdout.strip() if success else 'master'

        success, stdout, stderr = self.run_command(f'push {remote} {branch}')

        if success:
            return {'success': True, 'message': 'Push successful'}
        elif 'Everything up-to-date' in stderr or 'Everything up-to-date' in stdout:
            return {'success': True, 'message': 'Everything up-to-date'}
        elif 'no upstream branch' in stderr:
            # 업스트림 설정 후 재시도
            success, stdout, stderr = self.run_command(
                f'push --set-upstream {remote} {branch}'
            )
            if success:
                return {'success': True, 'message': 'Upstream set and pushed'}
            else:
                return {'success': False, 'error': stderr}
        else:
            return {'success': False, 'error': stderr}

    def quick_push(self, message: str) -> dict:
        """빠른 add-commit-push"""
        print(f"🚀 Quick Push: {message}")

        # 1. Status
        status = self.status()
        if status['success']:
            total = status['total_changes']
            if total == 0:
                return {'success': True, 'message': 'No changes to push'}
            print(f"  📊 {total} changes detected")

        # 2. Add
        add_result = self.add()
        if not add_result['success']:
            return add_result
        print("  ✅ Files added")

        # 3. Commit
        commit_result = self.commit(message)
        if not commit_result['success']:
            return commit_result
        print(f"  ✅ Committed: {commit_result.get('commit_hash', 'unknown')[:7]}")

        # 4. Push
        push_result = self.push()
        if push_result['success']:
            print(f"  ✅ Pushed: {push_result['message']}")
        else:
            print(f"  ❌ Push failed: {push_result['error']}")

        return push_result


def main():
    """CLI 인터페이스"""
    import argparse

    parser = argparse.ArgumentParser(description='Git Helper for AI Coding Brain MCP')
    parser.add_argument('action', choices=['status', 'add', 'commit', 'push', 'quick'],
                       help='Git action to perform')
    parser.add_argument('-m', '--message', help='Commit message')
    parser.add_argument('-f', '--files', default='.', help='Files to add')
    parser.add_argument('-r', '--remote', default='origin', help='Remote name')
    parser.add_argument('-b', '--branch', help='Branch name')

    args = parser.parse_args()

    git = GitHelper()

    if args.action == 'status':
        result = git.status()
        if result['success']:
            print(f"Modified: {len(result['modified'])}")
            print(f"Added: {len(result['added'])}")
            print(f"Deleted: {len(result['deleted'])}")
            print(f"Untracked: {len(result['untracked'])}")
        else:
            print(f"Error: {result['error']}")

    elif args.action == 'add':
        result = git.add(args.files)
        print("✅ Added" if result['success'] else f"❌ {result['message']}")

    elif args.action == 'commit':
        if not args.message:
            print("❌ Commit message required (-m)")
            sys.exit(1)
        result = git.commit(args.message)
        print(f"✅ {result['message']}" if result['success'] else f"❌ {result['error']}")

    elif args.action == 'push':
        result = git.push(args.remote, args.branch)
        print(f"✅ {result['message']}" if result['success'] else f"❌ {result['error']}")

    elif args.action == 'quick':
        if not args.message:
            print("❌ Commit message required (-m)")
            sys.exit(1)
        result = git.quick_push(args.message)
        if not result['success']:
            sys.exit(1)


if __name__ == '__main__':
    main()

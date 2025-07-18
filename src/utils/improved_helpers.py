# AI Coding Brain MCP - Improved Helpers Module
# Generated: 2025-07-15 07:04:24

import os
import json
import shutil
import time
import random
from datetime import datetime
from pathlib import Path

class Helpers:
    """향상된 Helpers 클래스 - MCP 통합용"""

    def __init__(self):
        self.base_dir = os.getcwd()
        self.memory_dir = os.path.join(self.base_dir, 'memory')
        self.context_file = os.path.join(self.memory_dir, 'context.json')
        self.current_project = None

        # memory 디렉토리 확인 및 생성
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)

        # context 초기화
        self._init_context()

    def _init_context(self):
        """context.json 초기화"""
        if not os.path.exists(self.context_file):
            default_context = {
                "current_project": None,
                "projects": {},
                "last_updated": datetime.now().isoformat()
            }
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(default_context, f, indent=2, ensure_ascii=False)

        # 현재 context 로드
        with open(self.context_file, 'r', encoding='utf-8') as f:
            self.context = json.load(f)
            self.current_project = self.context.get('current_project')

    def get_current_project(self):
        """현재 프로젝트 반환"""
        return self.current_project

    def scan_directory_dict(self, path):
        """디렉토리 스캔 - 딕셔너리 형태로 반환"""
        path = os.path.abspath(path)
        result = {
            'files': [],
            'directories': []
        }

        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    result['files'].append(item)
                elif os.path.isdir(item_path) and not item.startswith('.'):
                    result['directories'].append(item)
        except Exception as e:
            print(f"스캔 오류: {e}")

        return result

    def read_file(self, path):
        """파일 읽기"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    def create_file(self, path, content):
        """파일 생성/쓰기"""
        try:
            # 디렉토리가 없으면 생성
            dir_path = os.path.dirname(path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"파일 생성 오류: {e}")
            return False

    def update_context(self, key, value):
        """context 업데이트"""
        self.context[key] = value
        self.context['last_updated'] = datetime.now().isoformat()

        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(self.context, f, indent=2, ensure_ascii=False)

    def cmd_flow_with_context(self, project_name):
        """프로젝트 전환 및 컨텍스트 로드"""
        print(f"\n🔄 프로젝트 전환: {project_name}")

        # 이전 프로젝트 컨텍스트 백업
        if self.current_project and self.current_project != project_name:
            self._backup_current_context()

        # 프로젝트 디렉토리 확인/생성
        project_path = os.path.join(self.base_dir, 'projects', project_name)
        if not os.path.exists(project_path):
            os.makedirs(project_path, exist_ok=True)
            print(f"✅ 프로젝트 디렉토리 생성: {project_path}")

            # 기본 구조 생성
            for subdir in ['src', 'docs', 'tests', 'memory']:
                os.makedirs(os.path.join(project_path, subdir), exist_ok=True)

            # 기본 README 생성
            readme_content = f"""# {project_name}

프로젝트 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 개요
{project_name} 프로젝트입니다.

## 구조
- `src/` - 소스 코드
- `docs/` - 문서
- `tests/` - 테스트
- `memory/` - 프로젝트 컨텍스트
"""
            self.create_file(os.path.join(project_path, 'README.md'), readme_content)

        # 프로젝트 컨텍스트 로드/생성
        project_context_file = os.path.join(project_path, 'memory', 'context.json')
        if os.path.exists(project_context_file):
            with open(project_context_file, 'r', encoding='utf-8') as f:
                project_context = json.load(f)
            print(f"✅ 기존 프로젝트 컨텍스트 로드")
        else:
            project_context = {
                'name': project_name,
                'created_at': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'tasks': [],
                'notes': []
            }
            os.makedirs(os.path.dirname(project_context_file), exist_ok=True)
            with open(project_context_file, 'w', encoding='utf-8') as f:
                json.dump(project_context, f, indent=2, ensure_ascii=False)
            print(f"✅ 새 프로젝트 컨텍스트 생성")

        # 현재 프로젝트 업데이트
        self.current_project = project_name
        self.context['current_project'] = project_name

        # 프로젝트 목록에 추가
        if project_name not in self.context.get('projects', {}):
            self.context.setdefault('projects', {})[project_name] = {
                'path': project_path,
                'created_at': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat()
            }
        else:
            self.context['projects'][project_name]['last_accessed'] = datetime.now().isoformat()

        # context 저장
        self.update_context('current_project', project_name)

        # 프로젝트 브리핑
        print(f"\n📋 프로젝트 브리핑: {project_name}")
        print(f"  - 경로: {project_path}")
        print(f"  - 생성일: {project_context.get('created_at', 'Unknown')}")
        print(f"  - 작업 수: {len(project_context.get('tasks', []))}개")

        # file_directory.md 생성/업데이트
        self._update_file_directory(project_path)

        return {
            'project': project_name,
            'path': project_path,
            'context': project_context,
            'status': 'switched'
        }

    def _backup_current_context(self):
        """현재 프로젝트 컨텍스트 백업"""
        if not self.current_project:
            return

        backup_data = {
            'project': self.current_project,
            'timestamp': datetime.now().isoformat(),
            'session_data': {
                'variables': len(globals()),
                'cache_size': 0  # 실제 구현시 캐시 크기 추가
            }
        }

        backup_file = os.path.join(self.memory_dir, f"backup_{self.current_project}_{int(time.time())}.json")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        print(f"💾 이전 프로젝트 백업: {backup_file}")

    def _update_file_directory(self, project_path):
        """file_directory.md 업데이트"""
        content = f"# File Directory - {os.path.basename(project_path)}\n\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for root, dirs, files in os.walk(project_path):
            level = root.replace(project_path, '').count(os.sep)
            indent = '  ' * level
            content += f"{indent}{os.path.basename(root)}/\n"

            subindent = '  ' * (level + 1)
            for file in files:
                content += f"{subindent}{file}\n"

        self.create_file(os.path.join(project_path, 'file_directory.md'), content)

    def search_files_advanced(self, path, pattern):
        """파일 검색 (패턴 매칭)"""
        results = {'results': []}

        for root, dirs, files in os.walk(path):
            for file in files:
                if pattern in file:
                    results['results'].append({
                        'path': os.path.join(root, file),
                        'name': file
                    })

        return results

    def search_code_content(self, path, pattern, file_pattern="*"):
        """코드 내용 검색"""
        results = {'results': []}

        import fnmatch

        for root, dirs, files in os.walk(path):
            for file in files:
                if fnmatch.fnmatch(file, file_pattern):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if pattern in content:
                                # 매칭된 라인 찾기
                                lines = content.split('\n')
                                matches = []
                                for i, line in enumerate(lines):
                                    if pattern in line:
                                        matches.append({
                                            'line': i + 1,
                                            'content': line.strip()
                                        })

                                results['results'].append({
                                    'file': file_path,
                                    'matches': matches
                                })
                    except:
                        pass

        return results

    def replace_block(self, file_path, target, new_code):
        """코드 블록 교체"""
        try:
            content = self.read_file(file_path)
            if target in content:
                new_content = content.replace(target, new_code)
                self.create_file(file_path, new_content)
                return True
            return False
        except:
            return False
if __name__ != "__main__":
    helpers = Helpers()
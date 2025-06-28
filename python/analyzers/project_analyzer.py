"""
ProjectAnalyzer - 프로젝트 분석 오케스트레이터

프로젝트 전체를 스캔하고 분석하여 구조화된 메타데이터를 생성합니다.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import logging

# Logger 설정
logger = logging.getLogger(__name__)

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
python_path = Path(__file__).parent.parent
if str(python_path) not in sys.path:
    sys.path.insert(0, str(python_path))

from python.analyzers.unified_analyzer import UnifiedAnalyzer
from analyzers.manifest_manager import ManifestManager
from project_wisdom import get_wisdom_manager


class ProjectAnalyzer:
    """프로젝트 분석을 총괄하는 메인 클래스"""
    
    def __init__(self, project_root: str):
        """
        Args:
            project_root: 분석할 프로젝트의 루트 디렉토리 경로
        """
        self.project_root = Path(project_root).resolve()
        self.project_name = self.project_root.name
        self.manifest_manager = ManifestManager(self.project_root)
        # wisdom_manager 초기화
        self.wisdom_manager = get_wisdom_manager()
        self.file_analyzer = UnifiedAnalyzer(wisdom_manager=self.wisdom_manager)
        
        # 무시할 디렉토리/파일 패턴
        self.ignore_dirs = {
            '__pycache__', '.git', 'node_modules', 'dist', 'build',
            '.pytest_cache', '.mypy_cache', 'venv', '.venv', 'env',
            'backups', 'test', 'tests'
        }
        self.ignore_extensions = {'.pyc', '.pyo', '.pyd', '.so', '.dll'}
        
    def analyze_and_update(self, force_full_scan: bool = False) -> Dict[str, Any]:
        """
        프로젝트를 분석하고 manifest를 업데이트합니다.
        
        Args:
            force_full_scan: True면 캐시를 무시하고 전체 재분석
            
        Returns:
            분석 결과 요약 딕셔너리
        """
        print(f"🔍 프로젝트 분석 시작: {self.project_name}")
        
        # 1. 기존 manifest 로드
        manifest = self.manifest_manager.load()
        old_files = set(manifest.get('files', {}).keys()) if not force_full_scan else set()
        
        # 2. 현재 파일 시스템 스캔
        current_files = self._scan_project_files()
        current_file_set = set(current_files.keys())
        
        # 3. 변경 사항 계산
        new_files = current_file_set - old_files
        deleted_files = old_files - current_file_set
        
        # 수정된 파일 찾기
        modified_files = set()
        if not force_full_scan:
            for file_path in current_file_set & old_files:
                old_mtime = manifest['files'][file_path].get('last_modified', '')
                new_mtime = current_files[file_path]['last_modified']
                if old_mtime != new_mtime:
                    modified_files.add(file_path)
        else:
            modified_files = current_file_set
        
        # 4. 분석 수행
        total_to_analyze = len(new_files) + len(modified_files)
        
        if total_to_analyze > 0:
            print(f"📊 분석 대상: 신규 {len(new_files)}개, 수정 {len(modified_files)}개")
            
            # 신규/수정 파일 분석
            analyzed_count = 0
            for file_path in new_files | modified_files:
                try:
                    if file_path in new_files:
                        print(f"  ✨ 신규: {file_path}")
                    else:
                        print(f"  📝 수정: {file_path}")
                        
                    file_info = self._analyze_file(file_path, current_files[file_path])
                    manifest['files'][file_path] = file_info
                    analyzed_count += 1
                    
                except Exception as e:
                    print(f"  ❌ 오류: {file_path} - {str(e)}")
        
        # 5. 삭제된 파일 처리
        for file_path in deleted_files:
            print(f"  🗑️ 삭제: {file_path}")
            del manifest['files'][file_path]
        
        # 6. 전체 프로젝트 통계 업데이트
        manifest.update({
            'project_name': self.project_name,
            'last_analyzed': datetime.now().isoformat(),
            'total_files': len(current_file_set),
            'analyzed_files': len(manifest['files']),
            'structure': self._build_directory_structure(current_file_set)
        })
        
        # 7. 의존성 그래프 생성
        manifest['dependencies'] = self._build_dependency_graph(list(manifest['files'].values()))
        
        # 8. Manifest 저장
        self.manifest_manager.save(manifest)
        
        print(f"✅ 분석 완료! (전체 {len(current_file_set)}개 파일)")
        
        return {
            'success': True,
            'total_files': len(current_file_set),
            'analyzed': total_to_analyze,
            'new': len(new_files),
            'modified': len(modified_files),
            'deleted': len(deleted_files)
        }
    
    def _scan_project_files(self) -> Dict[str, Dict[str, Any]]:
        """프로젝트의 모든 Python/TypeScript 파일을 스캔합니다."""
        files = {}
        
        for root, dirs, filenames in os.walk(self.project_root):
            # 무시할 디렉토리 제외
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for filename in filenames:
                # 무시할 확장자 체크
                if any(filename.endswith(ext) for ext in self.ignore_extensions):
                    continue
                    
                # Python과 TypeScript 파일만 포함
                if filename.endswith(('.py', '.ts', '.js', '.tsx', '.jsx')):
                    file_path = Path(root) / filename
                    relative_path = file_path.relative_to(self.project_root)
                    
                    files[str(relative_path).replace('\\', '/')] = {
                        'absolute_path': str(file_path),
                        'last_modified': datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                        'size': file_path.stat().st_size
                    }
        
        return files
    
    def _analyze_file(self, relative_path: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """개별 파일을 분석합니다."""
        absolute_path = file_info['absolute_path']
        
        try:
            # UnifiedAnalyzer를 사용하여 분석
            analysis_result = self.file_analyzer.analyze(absolute_path)
            
            if 'error' in analysis_result:
                logger.warning(f"파일 분석 실패: {absolute_path} - {analysis_result['error']}")
                # 에러가 있어도 기본 정보는 반환
                return {
                    'path': relative_path,
                    'last_modified': file_info['last_modified'],
                    'size': file_info['size'],
                    'language': self._detect_file_language(relative_path),
                    'summary': f"분석 실패: {analysis_result['error']}",
                    'imports': {'internal': [], 'external': []},
                    'classes': [],
                    'functions': []
                }
                
            # UnifiedAnalyzer 결과를 기존 형식으로 변환
            file_result = {
                'path': relative_path,
                'last_modified': file_info['last_modified'],
                'size': file_info['size'],
                'language': analysis_result.get('language', self._detect_file_language(relative_path)),
                'summary': analysis_result.get('summary', ''),
                'imports': analysis_result.get('structure', {}).get('imports', {'internal': [], 'external': []}),
                'classes': analysis_result.get('structure', {}).get('classes', []),
                'functions': analysis_result.get('structure', {}).get('functions', []),
                'wisdom_insights': analysis_result.get('wisdom_insights', {})
            }
            
            # 품질 정보도 추가 (새로운 기능)
            if 'quality' in analysis_result:
                file_result['quality'] = {
                    'issues_count': len(analysis_result['quality'].get('issues', [])),
                    'complexity': analysis_result['quality'].get('stats', {}).get('complexity', 0),
                    'code_lines': analysis_result['quality'].get('stats', {}).get('code_lines', 0)
                }
                
            return file_result
            
        except Exception as e:
            logger.error(f"파일 분석 중 오류 발생: {absolute_path} - {str(e)}")
            # 오류가 발생해도 기본 정보는 반환
            return {
                'path': relative_path,
                'last_modified': file_info['last_modified'],
                'size': file_info['size'],
                'language': self._detect_file_language(relative_path),
                'summary': f"분석 오류: {str(e)}",
                'imports': {'internal': [], 'external': []},
                'classes': [],
                'functions': []
            }
        
        # 함수 목록 추가
        functions = file_info.get('functions', [])
        if functions:
            context += "\n### 주요 함수\n"
            for func in functions[:5]:  # 상위 5개만
                context += f"- **{func.get('name', 'unknown')}**: {func.get('summary', 'No summary')}\n"
        
        return context


# 사용 예시

    def _build_directory_structure(self, files: Set[str]) -> Dict[str, Any]:
        """디렉토리 구조를 계층적으로 구성"""
        structure = {
            'type': 'directory',
            'path': str(self.project_root),
            'children': {}
        }
        
        for file_path in sorted(files):
            try:
                # 절대 경로로 변환하여 비교
                abs_file_path = Path(file_path).resolve()
                abs_project_root = Path(self.project_root).resolve()
                
                # 프로젝트 루트 내부 파일인지 확인
                if not str(abs_file_path).startswith(str(abs_project_root)):
                    continue  # 외부 파일은 스킵
                
                relative_path = abs_file_path.relative_to(abs_project_root)
                parts = relative_path.parts
    
                current = structure['children']
                for i, part in enumerate(parts[:-1]):
                    if part not in current:
                        current[part] = {
                            'type': 'directory',
                            'path': str(Path(*parts[:i+1])),
                            'children': {}
                        }
                    current = current[part]['children']
                
                # 파일 추가
                current[parts[-1]] = {
                    'type': 'file',
                    'path': str(relative_path).replace('\\', '/')
                }
            except Exception as e:
                # 경로 문제가 있는 파일은 스킵
                continue
        
        return structure
    def _build_dependency_graph(self, analyses: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """파일 간 의존성 그래프 구성"""
        graph = {}
        
        for analysis in analyses:
            file_path = analysis.get('file_path', '')
            imports = analysis.get('imports', [])
            
            # 간단한 의존성 그래프
            dependencies = []
            for imp in imports:
                # 상대 경로나 프로젝트 내부 import만 추가
                if isinstance(imp, dict):
                    module = imp.get('module', '')
                    if not module.startswith(('.', self.project_name)):
                        continue
                    dependencies.append(module)
            
            if file_path:
                graph[file_path] = dependencies
        
        return graph
    
    def _detect_language(self) -> str:
        """프로젝트의 주 언어 감지"""
        # 파일 확장자별 카운트
        extension_counts = {}
        
        for root, dirs, files in os.walk(self.project_root):
            # 무시할 디렉토리 건너뛰기
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in self.ignore_extensions:
                    continue
                    
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        # 가장 많은 확장자로 언어 결정
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React',
            '.tsx': 'React TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust'
        }
        
        # 가장 많은 파일 타입 찾기
        if extension_counts:
            most_common_ext = max(extension_counts, key=extension_counts.get)
            return language_map.get(most_common_ext, 'Unknown')
        
        return 'Unknown'


    def _detect_file_language(self, file_path: str) -> str:
        """개별 파일의 언어 감지"""
        ext = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript', 
            '.ts': 'TypeScript',
            '.jsx': 'JavaScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.r': 'R',
            '.m': 'MATLAB',
            '.lua': 'Lua',
            '.pl': 'Perl',
            '.sh': 'Shell',
            '.bat': 'Batch',
            '.ps1': 'PowerShell',
            '.html': 'HTML',
            '.css': 'CSS',
            '.xml': 'XML',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.md': 'Markdown',
            '.sql': 'SQL'
        }
        
        return language_map.get(ext, 'Unknown')
if __name__ == '__main__':
    analyzer = ProjectAnalyzer('.')
    result = analyzer.analyze_and_update()
    print(f"\n분석 결과: {result}")
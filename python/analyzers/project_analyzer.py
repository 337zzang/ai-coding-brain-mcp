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

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .file_analyzer import FileAnalyzer
from .manifest_manager import ManifestManager


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
        self.file_analyzer = FileAnalyzer()
        
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
        manifest['dependencies'] = self._build_dependency_graph(manifest['files'])
        
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
        
        # FileAnalyzer를 사용하여 분석
        analysis = self.file_analyzer.analyze(absolute_path)
        
        # 기본 파일 정보와 분석 결과 병합
        return {
            'path': relative_path,
            'last_modified': file_info['last_modified'],
            'size': file_info['size'],
            'language': self._detect_language(relative_path),
            **analysis
        }
    
    def _detect_language(self, file_path: str) -> str:
        """파일 확장자로 언어를 감지합니다."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.js': 'javascript',
            '.jsx': 'javascript'
        }
        return language_map.get(ext, 'unknown')
    
    def _build_directory_structure(self, file_paths: Set[str]) -> Dict[str, Any]:
        """디렉토리 구조를 구축합니다."""
        structure = {}
        
        for file_path in file_paths:
            parts = Path(file_path).parts
            current = structure
            
            for i, part in enumerate(parts[:-1]):  # 파일명 제외
                if part not in current:
                    current[part] = {
                        'type': 'directory',
                        'file_count': 0,
                        'subdirs': {}
                    }
                current[part]['file_count'] += 1
                current = current[part]['subdirs']
        
        return structure
    
    def _build_dependency_graph(self, files: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """파일 간 의존성 그래프를 구축합니다."""
        graph = {}
        
        for file_path, file_info in files.items():
            imports = file_info.get('imports', {})
            internal_deps = imports.get('internal', [])
            
            # 내부 의존성만 그래프에 포함
            if internal_deps:
                graph[file_path] = internal_deps
        
        return {'graph': graph}
    
    def get_manifest(self) -> Dict[str, Any]:
        """현재 manifest를 반환합니다."""
        return self.manifest_manager.load()
    
    def get_briefing_data(self) -> Dict[str, Any]:
        """브리핑용 요약 데이터를 생성합니다."""
        manifest = self.get_manifest()
        
        # 파일 타입별 통계
        file_stats = {'python': 0, 'typescript': 0, 'javascript': 0, 'other': 0}
        for file_info in manifest.get('files', {}).values():
            lang = file_info.get('language', 'other')
            if lang in file_stats:
                file_stats[lang] += 1
            else:
                file_stats['other'] += 1
        
        return {
            'project_name': manifest.get('project_name', 'Unknown'),
            'last_analyzed': manifest.get('last_analyzed', 'Never'),
            'total_files': manifest.get('total_files', 0),
            'analyzed_files': manifest.get('analyzed_files', 0),
            'file_stats': file_stats,
            'structure': manifest.get('structure', {})
        }
    
    def generate_structure_report(self, format: str = 'markdown') -> str:
        """파일 구조 리포트를 생성합니다."""
        manifest = self.get_manifest()
        files = manifest.get('files', {})
        
        if format == 'markdown':
            lines = [f"# {manifest.get('project_name', 'Project')} File Structure\n"]
            lines.append(f"*Last analyzed: {manifest.get('last_analyzed', 'Never')}*\n")
            lines.append(f"**Total files**: {manifest.get('total_files', 0)}\n")
            
            # 디렉토리별로 그룹화
            dirs = {}
            for file_path in sorted(files.keys()):
                dir_path = str(Path(file_path).parent)
                if dir_path not in dirs:
                    dirs[dir_path] = []
                dirs[dir_path].append(file_path)
            
            # 디렉토리 트리 생성
            for dir_path in sorted(dirs.keys()):
                lines.append(f"\n## {dir_path}/")
                for file_path in dirs[dir_path]:
                    file_info = files[file_path]
                    summary = file_info.get('summary', 'No summary')
                    lines.append(f"- **{Path(file_path).name}**: {summary}")
            
            return '\n'.join(lines)
        
        return "Unsupported format"
    
    def get_file_context(self, file_path: str) -> Optional[str]:
        """특정 파일의 컨텍스트 정보를 생성합니다."""
        manifest = self.get_manifest()
        files = manifest.get('files', {})
        
        # 상대 경로로 정규화
        normalized_path = str(Path(file_path).as_posix())
        
        if normalized_path not in files:
            return None
        
        file_info = files[normalized_path]
        deps_graph = manifest.get('dependencies', {}).get('graph', {})
        
        # 이 파일이 의존하는 파일들
        dependencies = deps_graph.get(normalized_path, [])
        
        # 이 파일을 의존하는 파일들
        dependents = [
            f for f, deps in deps_graph.items() 
            if normalized_path in deps
        ]
        
        context = f"""## {normalized_path}

**요약**: {file_info.get('summary', 'No summary')}
**언어**: {file_info.get('language', 'unknown')}
**크기**: {file_info.get('size', 0)} bytes
**최종 수정**: {file_info.get('last_modified', 'unknown')}

### 구조
- 클래스: {len(file_info.get('classes', []))}개
- 함수: {len(file_info.get('functions', []))}개

### 의존성
- 이 파일이 사용: {', '.join(dependencies) if dependencies else 'None'}
- 이 파일을 사용: {', '.join(dependents) if dependents else 'None'}
"""
        
        # 함수 목록 추가
        functions = file_info.get('functions', [])
        if functions:
            context += "\n### 주요 함수\n"
            for func in functions[:5]:  # 상위 5개만
                context += f"- **{func.get('name', 'unknown')}**: {func.get('summary', 'No summary')}\n"
        
        return context


# 사용 예시
if __name__ == '__main__':
    analyzer = ProjectAnalyzer('.')
    result = analyzer.analyze_and_update()
    print(f"\n분석 결과: {result}")

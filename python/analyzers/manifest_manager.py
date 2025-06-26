"""
ManifestManager - 프로젝트 매니페스트 관리

project_manifest.json 파일의 읽기/쓰기 및 버전 관리를 담당합니다.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import shutil


class ManifestManager:
    """프로젝트 매니페스트 파일을 관리하는 클래스"""
    
    MANIFEST_VERSION = "1.0.0"
    MANIFEST_FILENAME = "project_manifest.json"
    
    def __init__(self, project_root: str):
        """
        Args:
            project_root: 프로젝트 루트 디렉토리 경로
        """
        self.project_root = Path(project_root)
        self.memory_dir = self.project_root / "memory"
        self.manifest_path = self.memory_dir / self.MANIFEST_FILENAME
        
        # memory 디렉토리가 없으면 생성
        self.memory_dir.mkdir(exist_ok=True)
    
    def load(self) -> Dict[str, Any]:
        """
        매니페스트 파일을 로드합니다.
        
        Returns:
            매니페스트 데이터 (없으면 빈 구조 반환)
        """
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                # 버전 확인 및 마이그레이션
                if manifest.get('version') != self.MANIFEST_VERSION:
                    manifest = self._migrate_manifest(manifest)
                
                return manifest
                
            except json.JSONDecodeError as e:
                print(f"⚠️ Manifest 파일 파싱 오류: {e}")
                # 백업 생성
                backup_path = self.manifest_path.with_suffix('.json.backup')
                shutil.copy2(self.manifest_path, backup_path)
                print(f"   백업 생성: {backup_path}")
                
        # 새 매니페스트 구조 반환
        return self._create_empty_manifest()
    
    def save(self, manifest: Dict[str, Any]) -> bool:
        """
        매니페스트를 파일로 저장합니다.
        
        Args:
            manifest: 저장할 매니페스트 데이터
            
        Returns:
            저장 성공 여부
        """
        try:
            # 버전 정보 추가
            manifest['version'] = self.MANIFEST_VERSION
            manifest['last_saved'] = datetime.now().isoformat()
            
            # 임시 파일에 먼저 저장 (안전성)
            temp_path = self.manifest_path.with_suffix('.json.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            # 기존 파일이 있으면 백업
            if self.manifest_path.exists():
                # 날짜별 백업 (하루에 하나만 유지)
                today = datetime.now().strftime('%Y%m%d')
                backup_path = self.memory_dir / f"manifest_backup_{today}.json"
                
                if not backup_path.exists():
                    shutil.copy2(self.manifest_path, backup_path)
            
            # 임시 파일을 실제 파일로 이동
            temp_path.replace(self.manifest_path)
            
            return True
            
        except Exception as e:
            print(f"❌ Manifest 저장 오류: {e}")
            return False
    
    def _create_empty_manifest(self) -> Dict[str, Any]:
        """빈 매니페스트 구조를 생성합니다."""
        return {
            'version': self.MANIFEST_VERSION,
            'project_name': self.project_root.name,
            'created_at': datetime.now().isoformat(),
            'last_analyzed': None,
            'total_files': 0,
            'analyzed_files': 0,
            'structure': {},
            'files': {},
            'dependencies': {'graph': {}}
        }
    
    def _migrate_manifest(self, old_manifest: Dict[str, Any]) -> Dict[str, Any]:
        """구 버전 매니페스트를 현재 버전으로 마이그레이션합니다."""
        old_version = old_manifest.get('version', '0.0.0')
        print(f"📦 Manifest 마이그레이션: {old_version} → {self.MANIFEST_VERSION}")
        
        # 버전별 마이그레이션 로직
        manifest = old_manifest.copy()
        
        # 0.0.0 → 1.0.0
        if old_version == '0.0.0':
            # 필수 필드 추가
            if 'structure' not in manifest:
                manifest['structure'] = {}
            if 'dependencies' not in manifest:
                manifest['dependencies'] = {'graph': {}}
            if 'created_at' not in manifest:
                manifest['created_at'] = datetime.now().isoformat()
        
        manifest['version'] = self.MANIFEST_VERSION
        return manifest
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        특정 파일의 정보를 가져옵니다.
        
        Args:
            file_path: 파일 경로 (프로젝트 루트 기준 상대 경로)
            
        Returns:
            파일 정보 딕셔너리 (없으면 None)
        """
        manifest = self.load()
        files = manifest.get('files', {})
        
        # 경로 정규화 (역슬래시를 슬래시로)
        normalized_path = str(Path(file_path).as_posix())
        
        return files.get(normalized_path)
    
    def update_file_info(self, file_path: str, file_info: Dict[str, Any]) -> bool:
        """
        특정 파일의 정보를 업데이트합니다.
        
        Args:
            file_path: 파일 경로 (프로젝트 루트 기준 상대 경로)
            file_info: 업데이트할 파일 정보
            
        Returns:
            업데이트 성공 여부
        """
        manifest = self.load()
        
        # 경로 정규화
        normalized_path = str(Path(file_path).as_posix())
        
        # 파일 정보 업데이트
        if 'files' not in manifest:
            manifest['files'] = {}
        
        manifest['files'][normalized_path] = file_info
        manifest['analyzed_files'] = len(manifest['files'])
        
        return self.save(manifest)
    
    def remove_file_info(self, file_path: str) -> bool:
        """
        특정 파일의 정보를 제거합니다.
        
        Args:
            file_path: 파일 경로 (프로젝트 루트 기준 상대 경로)
            
        Returns:
            제거 성공 여부
        """
        manifest = self.load()
        files = manifest.get('files', {})
        
        # 경로 정규화
        normalized_path = str(Path(file_path).as_posix())
        
        if normalized_path in files:
            del files[normalized_path]
            manifest['analyzed_files'] = len(files)
            return self.save(manifest)
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """매니페스트의 통계 정보를 반환합니다."""
        manifest = self.load()
        
        stats = {
            'total_files': manifest.get('total_files', 0),
            'analyzed_files': manifest.get('analyzed_files', 0),
            'last_analyzed': manifest.get('last_analyzed', 'Never'),
            'manifest_size': self.manifest_path.stat().st_size if self.manifest_path.exists() else 0,
            'file_types': {}
        }
        
        # 파일 타입별 통계
        for file_info in manifest.get('files', {}).values():
            lang = file_info.get('language', 'unknown')
            stats['file_types'][lang] = stats['file_types'].get(lang, 0) + 1
        
        return stats
    
    def export_summary(self, output_path: Optional[str] = None) -> str:
        """
        매니페스트의 요약을 내보냅니다.
        
        Args:
            output_path: 출력 파일 경로 (없으면 문자열로 반환)
            
        Returns:
            요약 내용
        """
        manifest = self.load()
        stats = self.get_statistics()
        
        summary_lines = [
            f"# {manifest.get('project_name', 'Unknown Project')} Analysis Summary",
            f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Last Analysis**: {stats['last_analyzed']}",
            f"\n## Statistics",
            f"- Total Files: {stats['total_files']}",
            f"- Analyzed Files: {stats['analyzed_files']}",
            f"- Coverage: {stats['analyzed_files'] / max(stats['total_files'], 1) * 100:.1f}%",
            f"\n## File Types"
        ]
        
        for lang, count in sorted(stats['file_types'].items()):
            summary_lines.append(f"- {lang}: {count} files")
        
        # 주요 모듈 정보
        summary_lines.append("\n## Key Modules")
        
        # 큰 파일들 (상위 10개)
        files_by_size = sorted(
            manifest.get('files', {}).items(),
            key=lambda x: x[1].get('size', 0),
            reverse=True
        )[:10]
        
        if files_by_size:
            summary_lines.append("\n### Largest Files")
            for file_path, file_info in files_by_size:
                size_kb = file_info.get('size', 0) / 1024
                summary_lines.append(
                    f"- **{file_path}** ({size_kb:.1f} KB): {file_info.get('summary', 'No summary')}"
                )
        
        # 복잡한 모듈들 (함수가 많은 파일)
        files_by_functions = sorted(
            manifest.get('files', {}).items(),
            key=lambda x: len(x[1].get('functions', [])),
            reverse=True
        )[:10]
        
        if files_by_functions:
            summary_lines.append("\n### Most Complex Modules")
            for file_path, file_info in files_by_functions:
                func_count = len(file_info.get('functions', []))
                if func_count > 0:
                    summary_lines.append(
                        f"- **{file_path}** ({func_count} functions): {file_info.get('summary', 'No summary')}"
                    )
        
        summary = '\n'.join(summary_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(summary)
        
        return summary
    
    def migrate_from_file_directory(self, file_directory_path: str) -> bool:
        """
        기존 file_directory.md에서 데이터를 마이그레이션합니다.
        
        Args:
            file_directory_path: file_directory.md 파일 경로
            
        Returns:
            마이그레이션 성공 여부
        """
        try:
            # file_directory.md 읽기
            with open(file_directory_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 기본 구조 파싱 (간단한 구현)
            manifest = self.load()
            
            # 파일 목록 추출 (정규식 사용)
            import re
            file_pattern = r'[-*]\s+`?([^`\s]+\.(?:py|ts|js|tsx|jsx))`?'
            files = re.findall(file_pattern, content)
            
            # 각 파일을 manifest에 추가 (기본 정보만)
            for file_path in files:
                if file_path not in manifest['files']:
                    manifest['files'][file_path] = {
                        'path': file_path,
                        'summary': 'Migrated from file_directory.md',
                        'last_modified': datetime.now().isoformat(),
                        'size': 0,
                        'language': self._detect_language(file_path),
                        'imports': {'internal': [], 'external': []},
                        'classes': [],
                        'functions': []
                    }
            
            manifest['total_files'] = len(files)
            manifest['analyzed_files'] = len(manifest['files'])
            
            print(f"✅ {len(files)}개 파일을 마이그레이션했습니다.")
            return self.save(manifest)
            
        except Exception as e:
            print(f"❌ 마이그레이션 오류: {e}")
            return False
    
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


# 테스트 코드
if __name__ == '__main__':
    manager = ManifestManager('.')
    
    # 통계 출력
    stats = manager.get_statistics()
    print(f"매니페스트 통계: {stats}")
    
    # 요약 생성
    summary = manager.export_summary()
    print(f"\n요약:\n{summary}")

from python.workflow_integration import switch_project_workflow
"""
통합된 컨텍스트 관리자
프로젝트별 상태와 워크플로우 데이터를 관리합니다.
"""
import json
from pathlib import Path
from datetime import datetime
import os
from typing import Dict, Any, Optional

try:
    from core.path_utils import (
        get_context_path, 
        get_workflow_path,
        get_project_root,
        get_cache_dir
    )
except ImportError:
    # 상대 임포트 실패 시 절대 경로로 시도
    import sys
    sys.path.append("python")
    from core.path_utils import (
        get_context_path,
        get_workflow_path,
        get_project_root,
        get_cache_dir
    )
from utils.io_helpers import atomic_write, write_json, read_json

class ContextManager:
    """프로젝트별 컨텍스트를 관리하는 클래스"""
    
    def __init__(self):
        self.context = {}
        self.workflow_data = {}
        self.current_project_name = None
        self.cache = {}  # 메모리 캐시
        
    def get_current_project_name(self) -> str:
        """현재 프로젝트 이름을 반환합니다."""
        if self.current_project_name:
            return self.current_project_name
        
        # 현재 디렉토리 기반으로 프로젝트 이름 추론
        current = Path.cwd()
        return current.name
    
    def initialize(self, project_name: str = None):
        """컨텍스트 매니저를 초기화합니다."""
        if not project_name:
            project_name = self.get_current_project_name()
            
        self.current_project_name = project_name
        self.load_all()
        print(f"✅ ContextManager 초기화: {project_name}")
    
    def switch_project(self, new_project_name: str):
        """프로젝트를 전환합니다."""
        if self.current_project_name == new_project_name:
            print(f"이미 '{new_project_name}' 프로젝트입니다.")
            return
            
        # 1. 현재 프로젝트 데이터 저장
        if self.current_project_name:
            self.save_all()
            print(f"💾 '{self.current_project_name}' 프로젝트 데이터 저장")
            
        # 2. 새 프로젝트로 전환
        self.current_project_name = new_project_name
        project_root = get_project_root(new_project_name)
        
        # 프로젝트 디렉토리가 없으면 에러
        if not project_root.exists():
            raise ValueError(f"프로젝트 디렉토리가 없습니다: {project_root}")
            
        # 3. 새 프로젝트 데이터 로드
        # 워크플로우 인스턴스도 전환 (Task 1 개선)
        switch_project_workflow(new_project_name)
        
        self.load_all()
        
        print(f"✅ 프로젝트 '{new_project_name}'로 전환 완료")
        
    def load_all(self):
        """모든 데이터를 로드합니다."""
        if not self.current_project_name:
            self.current_project_name = self.get_current_project_name()
            
        # context.json 로드
        context_path = get_context_path(self.current_project_name)
        if context_path.exists():
            try:
                with open(context_path, 'r', encoding='utf-8') as f:
                    self.context = json.load(f)
                print(f"  ✓ context.json 로드 ({len(self.context)} keys)")
            except Exception as e:
                print(f"  ❌ context.json 로드 실패: {e}")
                self.context = {}
        else:
            # 기존 캐시 파일들을 통합
            self._migrate_old_cache()
            
        # workflow.json 로드
        workflow_path = get_workflow_path(self.current_project_name)
        if workflow_path.exists():
            try:
                with open(workflow_path, 'r', encoding='utf-8') as f:
                    self.workflow_data = json.load(f)
                print(f"  ✓ workflow.json 로드")
            except Exception as e:
                print(f"  ❌ workflow.json 로드 실패: {e}")
                self.workflow_data = {}
        else:
            # 기존 workflow_data.json에서 로드
            self._migrate_old_workflow()
                
    def save_all(self):
        """모든 데이터를 저장합니다."""
        if not self.current_project_name:
            return
            
        # context.json 저장 (최적화된 버전)
        context_path = get_context_path(self.current_project_name)
        
        # 저장할 데이터 준비 (불필요한 필드 제외)
        context_to_save = {}
        excluded_keys = ['__mcp_shared_vars__', 'analyzed_files', 'cache']
        
        for key, value in self.context.items():
            if key not in excluded_keys:
                context_to_save[key] = value
        
        # analyzed_files는 별도 캐시 파일로 저장
        if 'analyzed_files' in self.context and self.context['analyzed_files']:
            cache_dir = os.path.join(os.path.dirname(context_path), 'cache')
            os.makedirs(cache_dir, exist_ok=True)
            analyzed_files_path = os.path.join(cache_dir, 'analyzed_files.json')
            
            try:
                write_json({
                    'analyzed_files': self.context['analyzed_files'],
                    'last_updated': datetime.now().isoformat()
                }, Path(analyzed_files_path))
            except Exception as e:
                print(f"  ⚠️ analyzed_files 캐시 저장 실패: {e}")
        
        context_to_save['last_modified'] = datetime.now().isoformat()
        context_to_save['project_name'] = self.current_project_name
        
        try:
            write_json(context_to_save, Path(context_path))
            print(f"  ✓ context.json 저장 (원자적 쓰기 적용)")
        except Exception as e:
            print(f"  ❌ context.json 저장 실패: {e}")
            
        # workflow.json 저장
        if self.workflow_data:
            workflow_path = get_workflow_path(self.current_project_name)
            try:
                write_json(self.workflow_data, Path(workflow_path))
                print(f"  ✓ workflow.json 저장 (원자적 쓰기 적용)")
            except Exception as e:
                print(f"  ❌ workflow.json 저장 실패: {e}")
    
    def save(self):
        """save_all의 별칭 (기존 코드 호환성)"""
        self.save_all()
                
    def _migrate_old_cache(self):
        """기존 캐시 파일들을 새 구조로 마이그레이션합니다."""
        old_cache_dir = Path('memory/.cache')
        if not old_cache_dir.exists():
            self.context = {'cache': {}}
            return
            
        print("  🔄 기존 캐시 파일 마이그레이션 중...")
        
        # 기존 캐시 파일들 통합
        self.context = {
            'project_name': self.current_project_name,
            'core': {},
            'analyzed_files': [],
            'cache': {}
        }
        
        # cache_core.json
        core_file = old_cache_dir / 'cache_core.json'
        if core_file.exists():
            try:
                with open(core_file, 'r', encoding='utf-8') as f:
                    self.context['core'] = json.load(f)
            except:
                pass
                
        # cache_analyzed_files.json
        analyzed_file = old_cache_dir / 'cache_analyzed_files.json'
        if analyzed_file.exists():
            try:
                with open(analyzed_file, 'r', encoding='utf-8') as f:
                    self.context['analyzed_files'] = json.load(f)
            except:
                pass
                
        print("  ✅ 캐시 마이그레이션 완료")
        
    def _migrate_old_workflow(self):
        """기존 워크플로우 데이터를 마이그레이션합니다."""
        # workflow_data.json
        old_workflow = Path('workflow_data.json')
        if old_workflow.exists():
            try:
                with open(old_workflow, 'r', encoding='utf-8') as f:
                    self.workflow_data = json.load(f)
                print("  ✓ workflow_data.json 마이그레이션")
            except:
                self.workflow_data = {}
                
        # 기존 캐시의 워크플로우 관련 데이터
        old_cache_dir = Path('memory/.cache')
        if old_cache_dir.exists():
            for cache_file in ['cache_plan.json', 'cache_tasks.json', 'cache_work_tracking.json']:
                filepath = old_cache_dir / cache_file
                if filepath.exists():
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            key = cache_file.replace('cache_', '').replace('.json', '')
                            self.workflow_data[key] = json.load(f)
                    except:
                        pass
                        
    def update_context(self, *args, **kwargs):
        """컨텍스트를 업데이트합니다."""
        if args and len(args) == 2:
            key, value = args
            self.context[key] = value
            self.cache[key] = value  # 메모리 캐시에도 저장
        elif kwargs:
            self.context.update(kwargs)
            self.cache.update(kwargs)
    
    def update_cache(self, *args, **kwargs):
        """update_context의 별칭 (기존 코드 호환성)"""
        self.update_context(*args, **kwargs)
            
    def get_value(self, key: str, default=None):
        """컨텍스트에서 값을 가져옵니다."""
        # 먼저 메모리 캐시 확인
        if key in self.cache:
            return self.cache[key]
        # 다음 컨텍스트 확인
        return self.context.get(key, default)
        
    def get_context(self) -> dict:
        """전체 컨텍스트를 반환합니다 (최적화된 버전)."""
        # __mcp_shared_vars__ 등 불필요한 키 제외
        filtered_context = {}
        excluded_keys = ['__mcp_shared_vars__']
        
        for key, value in self.context.items():
            if key not in excluded_keys:
                filtered_context[key] = value
                
        return filtered_context
    
    def get(self, key: str, default=None):
        """get_value의 별칭"""
        return self.get_value(key, default)
    
    def track_file_access(self, filepath: str):
        """파일 접근을 추적합니다."""
        if 'accessed_files' not in self.context:
            self.context['accessed_files'] = []
        
        access_info = {
            'path': filepath,
            'timestamp': datetime.now().isoformat()
        }
        
        # 중복 제거를 위해 경로만 체크
        paths = [f['path'] for f in self.context['accessed_files']]
        if filepath not in paths:
            self.context['accessed_files'].append(access_info)
            
    def track_function_edit(self, file: str, function: str, changes: str):
        """함수 수정을 추적합니다."""
        if 'function_edits' not in self.context:
            self.context['function_edits'] = []
            
        edit_info = {
            'file': file,
            'function': function,
            'changes': changes,
            'timestamp': datetime.now().isoformat()
        }
        
        self.context['function_edits'].append(edit_info)

# 싱글톤 인스턴스
_context_manager_instance = None

def get_context_manager() -> ContextManager:
    """싱글톤 ContextManager 인스턴스를 반환합니다."""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager()
        _context_manager_instance.initialize()
    return _context_manager_instance
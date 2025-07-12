# from python.workflow_integration import switch_project_workflow  # Moved to method to avoid circular import
"""
통합된 컨텍스트 관리자
프로젝트별 상태와 워크플로우 데이터를 관리합니다.
"""
import json
from pathlib import Path
from datetime import datetime
import os
import logging
from typing import Dict, Any, Optional, List

try:
    from path_utils import (
        get_context_path, 
        get_workflow_path,
        get_project_root,
        get_cache_dir
    )
except ImportError:
    # 상대 임포트 실패 시 절대 경로로 시도
    import sys
    sys.path.append("python")
    from path_utils import (
        get_context_path,
        get_workflow_path,
        get_project_root,
        get_cache_dir
    )
from utils.io_helpers import atomic_write, write_json, read_json
from core.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)

class CacheAPI:
    """ContextManager를 통한 일관된 캐시 접근 인터페이스"""

    def __init__(self, cache_manager):
        """
        Args:
            cache_manager: CacheManager 인스턴스 또는 None
        """
        self._manager = cache_manager
        self._fallback_cache = {}  # CacheManager가 없을 때 사용할 폴백

    def get(self, key: str, default=None):
        """캐시에서 값 조회"""
        if self._manager:
            value = self._manager.get(key)
            return value if value is not None else default
        else:
            return self._fallback_cache.get(key, default)

    def set(self, key: str, value: Any, ttl: int = None, dependencies: List[str] = None):
        """캐시에 값 저장"""
        if self._manager:
            # Path 객체 리스트로 변환
            dep_paths = [Path(d) for d in dependencies] if dependencies else []
            self._manager.set(key, value, ttl=ttl, dependencies=dep_paths)
        else:
            self._fallback_cache[key] = value

    def invalidate(self, key: str):
        """특정 키 무효화"""
        if self._manager:
            self._manager.invalidate(key)
        else:
            self._fallback_cache.pop(key, None)

    def invalidate_by_file(self, filepath: str) -> List[str]:
        """파일 변경에 따른 무효화"""
        if self._manager:
            return self._manager.invalidate_by_file(Path(filepath))
        else:
            # 폴백 모드에서는 전체 캐시 클리어
            keys = list(self._fallback_cache.keys())
            self._fallback_cache.clear()
            return keys

    def clear(self):
        """전체 캐시 클리어"""
        if self._manager:
            self._manager.clear_all()
        self._fallback_cache.clear()

    def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        if self._manager:
            return self._manager.get(key) is not None
        else:
            return key in self._fallback_cache

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        if self._manager:
            return self._manager.get_statistics()
        else:
            return {
                'mode': 'fallback',
                'items': len(self._fallback_cache),
                'cache_manager_available': False
            }

    def set_with_file_dependency(self, key: str, value: Any, filepath: str):
        """파일 의존성과 함께 캐시 설정 (편의 메서드)"""
        self.set(key, value, dependencies=[filepath])



class ContextManager:
    """프로젝트별 컨텍스트를 관리하는 클래스"""
    
    def __init__(self):
        self.context = {}
        self.workflow_data = {}
        self.current_project_name = None
        # self.cache = {}  # [REMOVED] 레거시 캐시 제거됨 - cache property 사용
        self._cache_api = None  # CacheAPI 인스턴스 (나중에 초기화)
        self._cache_manager = None  # 새로운 캐시 매니저
        
    def get_current_project_name(self) -> str:
        """현재 프로젝트 이름을 반환합니다."""
        if self.current_project_name:
            return self.current_project_name
    
    @property
    def cache(self):
        """레거시 호환성을 위한 캐시 접근자"""
        if not hasattr(self, '_cache_api') or self._cache_api is None:
            # 초기화되지 않은 경우 폴백
            if not hasattr(self, '_fallback_cache'):
                self._fallback_cache = {}
            return self._fallback_cache
        return self._cache_api
    
    def initialize(self, project_name: str = None):
        """컨텍스트 매니저를 초기화합니다."""
        self.current_project_name = project_name or self.get_current_project_name()
        
        # 캐시 매니저 초기화 - 지연 초기화로 변경
        self._cache_manager = None  # 초기화하지 않음
        self._cache_dir = None  # 나중에 사용할 캐시 디렉토리 저장
        
        # CacheAPI는 즉시 초기화 (캐시 매니저 없이도 작동)
        self._cache_api = CacheAPI(None)  # None으로 초기화하면 폴백 모드
        
        # 통합 tracking 시스템 초기화
        if 'tracking' not in self.context:
            self.context['tracking'] = {
                'tasks': {},
                'files': {},
                'operations': [],
                'errors': [],
                'statistics': {
                    'total_operations': 0,
                    'successful_operations': 0,
                    'failed_operations': 0,
                    'total_execution_time': 0
                }
            }
        
        if not project_name:
            project_name = self.get_current_project_name()
            
        self.current_project_name = project_name
        self.load_all()
        # print(f"ContextManager initialized: {project_name}")
    
    def _ensure_cache_manager(self):
        """캐시 매니저를 지연 초기화합니다 (필요할 때만)"""
        if self._cache_manager is None and self.current_project_name:
            try:
                # 캐시 디렉토리 설정
                if self._cache_dir is None:
                    self._cache_dir = get_cache_dir(self.current_project_name)
                
                # 캐시 매니저 초기화
                self._cache_manager = get_cache_manager(self._cache_dir)
                
                # CacheAPI에 캐시 매니저 연결
                if hasattr(self, '_cache_api') and self._cache_api:
                    self._cache_api._manager = self._cache_manager
                    
                logger.debug(f"Cache manager initialized for project: {self.current_project_name}")
                
            except Exception as e:
                logger.warning(f"Failed to initialize cache manager: {e}")
                self._cache_manager = None
    
    def switch_project(self, new_project_name: str):
        """프로젝트를 전환합니다."""
        # 지연 import로 순환 참조 해결
        from python.workflow_integration import switch_project_workflow

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
        
        # print(f"프로젝트 '{new_project_name}'로 전환 완료")
        
    def load_all(self):
        """모든 데이터를 로드합니다."""
        if not self.current_project_name:
            self.current_project_name = self.get_current_project_name()
            
        # context.json 로드
        context_path = get_context_path(self.current_project_name)
        if context_path.exists():
            try:
                self.context = read_json(context_path, default={})
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
                self.workflow_data = read_json(workflow_path, default={})
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
                
        # print("  캐시 마이그레이션 완료")
        
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
            # self.cache[key] = value  # [DEPRECATED]
            if hasattr(self, "_cache_api") and self._cache_api:
                self._cache_api.set(key, value)
            
            # 새로운 캐시 매니저에도 저장
            if self._cache_manager:
                # 현재 작업 디렉토리의 파일들을 의존성으로 추가
                dependencies = []
                if 'current_file' in self.context:
                    dependencies.append(Path(self.context['current_file']))
                
                self._cache_manager.set(f"context_{key}", value, dependencies=dependencies)
                
        elif kwargs:
            self.context.update(kwargs)
            # self.cache.update(kwargs)  # [DEPRECATED]
            if hasattr(self, "_cache_api") and self._cache_api:
                for k, v in kwargs.items():
                    self._cache_api.set(k, v)
            
            # 새로운 캐시 매니저에도 저장
            if self._cache_manager:
                for k, v in kwargs.items():
                    self._cache_manager.set(f"context_{k}", v)
    
    def update_cache(self, *args, **kwargs):
        """update_context의 별칭 (기존 코드 호환성)"""
        self.update_context(*args, **kwargs)
            
    def get_value(self, key: str, default=None):
        """컨텍스트에서 값을 가져옵니다."""
        # 캐시 API 사용
        if hasattr(self, "_cache_api") and self._cache_api:
            cache_key = "context_" + str(key)
            cached_value = self._cache_api.get(cache_key)
            if cached_value is not None:
                return cached_value
        
        # 컨텍스트에서 조회
        value = self.context.get(key, default)
        
        # 캐시에 저장
        if value is not None and hasattr(self, "_cache_api") and self._cache_api:
            cache_key = "context_" + str(key)
            self._cache_api.set(cache_key, value)
        
        return value
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
            
        # 캐시 매니저에 파일 변경 감지 요청
        if self._cache_manager:
            # 이 파일에 의존하는 캐시들을 무효화
            invalidated = self._cache_manager.invalidate_by_file(Path(filepath))
            if invalidated:
                print(f"[Cache] Invalidated {len(invalidated)} cache entries due to file access: {filepath}")
            
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


    # ===== 워크플로우 V3 통합 메서드 =====

    def update_workflow_summary(self, summary: Dict[str, Any]) -> None:
        """워크플로우 요약 정보 업데이트"""
        if not hasattr(self, 'workflow_data'):
            self.workflow_data = {}

        self.workflow_data['summary'] = {
            'current_plan': summary.get('current_plan'),
            'progress': summary.get('progress', 0),
            'total_tasks': summary.get('total_tasks', 0),
            'completed_tasks': summary.get('completed_tasks', 0),
            'updated_at': datetime.now().isoformat()
        }
        self.save()  # _mark_dirty 대신 save 사용

    def add_workflow_event(self, event: Dict[str, Any]) -> None:
        """워크플로우 이벤트 추가 (중요 이벤트만)"""
        if not hasattr(self, 'workflow_data'):
            self.workflow_data = {}

        if 'events' not in self.workflow_data:
            self.workflow_data['events'] = []

        # 최대 50개 이벤트만 유지
        self.workflow_data['events'].append(event)
        if len(self.workflow_data['events']) > 50:
            self.workflow_data['events'] = self.workflow_data['events'][-50:]

        self.save()

    def get_task_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """특정 태스크의 컨텍스트 조회"""
        # 태스크별 컨텍스트는 workflow_v3에서 관리하므로
        # 여기서는 간단한 참조만 반환
        if hasattr(self, 'workflow_data') and 'tasks' in self.workflow_data:
            return self.workflow_data['tasks'].get(task_id)
        return None

    def clear_workflow_data(self) -> None:
        """워크플로우 데이터 초기화"""
        if hasattr(self, 'workflow_data'):
            self.workflow_data = {}
            self.save()

    def get_recent_workflow_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 워크플로우 이벤트 조회"""
        if hasattr(self, 'workflow_data') and 'events' in self.workflow_data:
            return self.workflow_data['events'][-limit:]
        return []
    
    # ===== 캐시 무효화 메서드 =====
    
    def invalidate_cache(self, key: str):
        """특정 캐시 항목 무효화"""
        # CacheAPI를 통한 무효화
        if hasattr(self, '_cache_api') and self._cache_api is not None:
            self._cache_api.invalidate(key)
        elif hasattr(self, '_fallback_cache'):
            self._fallback_cache.pop(key, None)
        
        # 새로운 캐시 매니저 (지연 초기화)
        self._ensure_cache_manager()
        if self._cache_manager:
            self._cache_manager.invalidate(f"context_{key}")
    
    def invalidate_cache_by_file(self, filepath: str) -> List[str]:
        """파일 변경에 따른 캐시 무효화"""
        invalidated = []
        
        # 지연 초기화
        self._ensure_cache_manager()
        
        if self._cache_manager:
            invalidated = self._cache_manager.invalidate_by_file(Path(filepath))
            
            # 레거시 메모리 캐시도 클리어 (안전을 위해)
            if invalidated:
                if hasattr(self, '_cache_api') and self._cache_api is not None:
                    self._cache_api.clear()
                elif hasattr(self, '_fallback_cache'):
                    self._fallback_cache.clear()
                
        return invalidated
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        stats = {}
        
        # CacheAPI가 초기화된 경우에만 get_stats() 호출
        if hasattr(self, '_cache_api') and self._cache_api is not None:
            stats = self._cache_api.get_stats()
        else:
            # 폴백 모드
            stats = {
                'mode': 'fallback',
                'items': len(getattr(self, '_fallback_cache', {})),
                'cache_manager_available': False
            }
        
        # 추가 정보
        stats['cache_manager_available'] = self._cache_manager is not None
        
        # 캐시 매니저 통계 (지연 초기화)
        if stats['cache_manager_available']:
            self._ensure_cache_manager()
            if self._cache_manager:
                manager_stats = self._cache_manager.get_statistics()
                stats.update(manager_stats)
            
        return stats
    
    def set_cache_with_dependencies(self, key: str, value: Any, dependencies: List[str]):
        """의존성이 있는 캐시 항목 설정"""
        # CacheAPI를 통한 캐시 설정
        if hasattr(self, "_cache_api") and self._cache_api:
            self._cache_api.set_with_file_dependency(key, value, dependencies[0] if dependencies else None)
        else:
            # 폴백 - CacheManager 직접 사용 (지연 초기화)
            self._ensure_cache_manager()
            if self._cache_manager:
                dep_paths = [Path(d) for d in dependencies]
                self._cache_manager.set(f"context_{key}", value, dependencies=dep_paths)
    
    # ===== 통합 Tracking 시스템 메서드 =====
    
    def get_tracking(self) -> Dict[str, Any]:
        """통합 tracking 데이터 반환"""
        if 'tracking' not in self.context:
            self.context['tracking'] = {
                'tasks': {},
                'files': {},
                'operations': [],
                'errors': [],
                'statistics': {
                    'total_operations': 0,
                    'successful_operations': 0,
                    'failed_operations': 0,
                    'total_execution_time': 0
                }
            }
        return self.context['tracking']
    
    def get_file_access_history(self) -> List[Dict[str, Any]]:
        """파일 접근 이력 반환 (레거시 호환성)"""
        tracking = self.get_tracking()
        history = []
        for file_path, file_data in tracking['files'].items():
            for op in file_data.get('operations', []):
                history.append({
                    'file': file_path,
                    'operation': op['action'],
                    'timestamp': op['timestamp'],
                    'task_id': op.get('task_id')
                })
        # 시간 역순 정렬
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)[:100]
    
    def get_error_log(self) -> List[Dict[str, Any]]:
        """에러 로그 반환 (레거시 호환성)"""
        tracking = self.get_tracking()
        return tracking.get('errors', [])
    
    def get_tracking_statistics(self) -> Dict[str, Any]:
        """추적 통계 반환"""
        tracking = self.get_tracking()
        stats = tracking.get('statistics', {}).copy()
        stats['total_files_tracked'] = len(tracking.get('files', {}))
        stats['total_tasks_tracked'] = len(tracking.get('tasks', {}))
        return stats

# 싱글톤 인스턴스
_context_manager_instance = None

def get_context_manager() -> ContextManager:
    """싱글톤 ContextManager 인스턴스를 반환합니다."""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager()
        _context_manager_instance.initialize()
    return _context_manager_instance
#!/usr/bin/env python3
"""
Enhanced flow command with integrated file structure management and complete briefing
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# helpers 전역 변수 접근
helpers = globals().get('helpers', None)

# 기본 imports
import sys
import os

# Python 경로 설정 - 상대 import 문제 해결
python_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if python_path not in sys.path:
    sys.path.insert(0, python_path)

# 이제 절대 import 사용
from core.context_manager import get_context_manager, initialize_context
from core.config import get_project_path
from smart_print import smart_print
from analyzers.project_analyzer import ProjectAnalyzer
from project_briefing import print_project_briefing



# 캐싱 설정
CACHE_EXPIRY_HOURS = 24  # file_directory.md 캐시 유효 시간
MAX_CACHE_SIZE_MB = 100  # 최대 캐시 크기
PERFORMANCE_TRACKING = True  # 성능 추적 활성화

def debug_log(message):
    """디버깅 메시지를 파일에 기록"""
    import datetime
    with open("debug_flow.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now()}] {message}\n")
        f.flush()

    def __init__(self, project_path: str, helpers=None):
        self.project_path = project_path
        self.helpers = helpers or globals().get('helpers', None)
        self.structure_cache = {}
        self.file_metadata = {}
        
    def scan_project_structure(self) -> Dict[str, Any]:
        """프로젝트 구조를 스캔하고 분석 (핵심 파일 필터링 포함)"""
        
        self.core_paths = ['src/', 'python/', 'memory/']
        self.exclude_paths = [
            'vendor/', 'backups/', 'test/', '__tests__/', 'tests/',
            '.git/', 'node_modules/', '__pycache__/', 'dist/', 
            'build/', '.next/', '.cache/', 'coverage/', 'venv/', 
            'env/', '.env/', '.idea/', '.vscode/'
        ]
        self.core_extensions = {'.ts', '.js', '.py', '.json', '.md', '.yml', '.yaml'}
        self.exclude_extensions = {'.bak', '.log', '.tmp', '.cache', '.lock', '.resolved'}
        
        structure = {
            "files": {},
            "directories": {},
            "statistics": {
                "total_files": 0,
                "core_files": 0,
                "excluded_files": 0,
                "by_extension": {},
                "by_directory": {},
                "large_files": [],
                "recent_files": []
            },
            "key_files": {
                "entry_points": [],
                "configs": [],
                "tests": [],
                "docs": []
            }
        }
        
        def is_core_file(rel_path: str, file_name: str) -> bool:
            """핵심 파일인지 확인"""
            # 제외 경로 체크
            path_parts = rel_path.replace('\\', '/').lower()
            if any(exc in path_parts for exc in self.exclude_paths):
                return False
            
            # 제외 확장자 체크
            if any(file_name.endswith(ext) for ext in self.exclude_extensions):
                return False
            
            # 숨김 파일/폴더 제외
            if any(part.startswith('.') for part in rel_path.split(os.sep)):
                return False
            
            # 핵심 경로 체크
            in_core_path = any(core in rel_path.replace('\\', '/') for core in self.core_paths)
            
            # 핵심 확장자 체크
            ext = Path(file_name).suffix
            has_core_ext = ext in self.core_extensions
            
            # 루트 설정 파일 체크
            is_root_config = rel_path.count(os.sep) <= 1 and ext in {'.json', '.yml', '.yaml', '.toml'}
            
            return (in_core_path and has_core_ext) or is_root_config
        
        # 디렉토리 순회
        for root, dirs, files in os.walk(self.project_path):
            rel_root = os.path.relpath(root, self.project_path)
            
            # 제외할 디렉토리 필터링
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in {'node_modules', '__pycache__', 'dist', 'build', 
                               '.next', 'venv', 'env', 'coverage', 'backups'}]
            
            structure["directories"][rel_root] = {
                "file_count": len(files),
                "subdirs": dirs
            }
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_path)
                
                try:
                    stat = os.stat(file_path)
                    file_info = {
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "extension": Path(file).suffix,
                        "is_core": is_core_file(rel_path, file)
                    }
                    
                    structure["files"][rel_path] = file_info
                    
                    # 통계 업데이트
                    structure["statistics"]["total_files"] += 1
                    if file_info["is_core"]:
                        structure["statistics"]["core_files"] += 1
                    else:
                        structure["statistics"]["excluded_files"] += 1
                    
                    ext = Path(file).suffix
                    structure["statistics"]["by_extension"][ext] = \
                        structure["statistics"]["by_extension"].get(ext, 0) + 1
                    
                    # 핵심 파일만 추가 분석
                    if file_info["is_core"]:
                        # 큰 파일 추적 (100KB 이상)
                        if stat.st_size > 100000:
                            structure["statistics"]["large_files"].append({
                                "path": rel_path,
                                "size": stat.st_size
                            })
                        
                        # 주요 파일 분류
                        if file in ['index.py', 'main.py', 'app.py', 'index.ts', 'main.ts']:
                            structure["key_files"]["entry_points"].append(rel_path)
                        elif file.endswith(('.json', '.yaml', '.yml', '.toml')) and rel_path.count(os.sep) <= 1:
                            structure["key_files"]["configs"].append(rel_path)
                        elif 'test' in file.lower() or 'spec' in file.lower():
                            structure["key_files"]["tests"].append(rel_path)
                        elif file.endswith('.md'):
                            structure["key_files"]["docs"].append(rel_path)
                        
                except Exception as e:
                    structure["files"][rel_path] = {"error": str(e)}
        
        # 최근 수정된 핵심 파일 (상위 10개)
        recent_files = sorted(
            [(p, f["modified"]) for p, f in structure["files"].items() 
             if "modified" in f and f.get("is_core", False)],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        structure["statistics"]["recent_files"] = [
            {"path": p, "modified": m} for p, m in recent_files
        ]
        
        self.structure_cache = structure
        return structure

    def scan_directory(self) -> Dict[str, Any]:
        """scan_project_structure의 별칭 (호환성을 위해)"""
        return self.scan_project_structure()

    def get_file_context(self, file_path: str) -> Dict[str, Any]:
        """특정 파일의 context 정보 반환"""
        rel_path = os.path.relpath(file_path, self.project_path)
        
        if rel_path in self.structure_cache.get("files", {}):
            file_info = self.structure_cache["files"][rel_path].copy()
            
            # 추가 context 정보
            file_info["directory"] = os.path.dirname(rel_path)
            file_info["filename"] = os.path.basename(rel_path)
            
            # 같은 디렉토리의 관련 파일들
            same_dir_files = [
                f for f in self.structure_cache["files"]
                if os.path.dirname(f) == file_info["directory"] and f != rel_path
            ]
            file_info["related_files"] = same_dir_files[:5]
            
            return file_info
        
        return {}
    
    def update_file_access(self, file_path: str):
        """파일 접근 시 metadata 업데이트"""
        rel_path = os.path.relpath(file_path, self.project_path)
        if rel_path not in self.file_metadata:
            self.file_metadata[rel_path] = {
                "access_count": 0,
                "last_accessed": None,
                "modifications": []
            }
        
        self.file_metadata[rel_path]["access_count"] += 1
        self.file_metadata[rel_path]["last_accessed"] = datetime.now().isoformat()



    def get_core_files(self) -> List[Dict[str, Any]]:
        """프로젝트 핵심 파일만 가져오기"""
        if not self.structure_cache:
            self.scan_project_structure()
        
        core_files = []
        for path, info in self.structure_cache.get("files", {}).items():
            if info.get("is_core", False):
                core_files.append({
                    "path": path,
                    "name": os.path.basename(path),
                    "type": "file",
                    "size": info.get("size", 0),
                    "modified": info.get("modified", ""),
                    "extension": info.get("extension", "")
                })
        
        return core_files
    
    def search_core_files(self, pattern: str) -> List[Dict[str, Any]]:
        """핵심 파일에서만 검색"""
        if not self.structure_cache:
            self.scan_project_structure()
        
        pattern_lower = pattern.lower()
        results = []
        
        for path, info in self.structure_cache.get("files", {}).items():
            if info.get("is_core", False) and pattern_lower in path.lower():
                results.append({
                    "path": path,
                    "name": os.path.basename(path),
                    "type": "file",
                    "size": info.get("size", 0),
                    "modified": info.get("modified", ""),
                    "extension": info.get("extension", "")
                })
        
        return results

def create_progress_bar(percentage: float, width: int = 30) -> str:
    """시각적 진행률 바 생성"""
    filled = int(width * percentage / 100)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    return f"[{bar}] {percentage:.1f}%"


def format_task_status(task) -> str:
    """작업 상태를 이모지로 표현"""
    if task.completed:
        return "✅"
    elif hasattr(task, 'in_progress') and task.in_progress:
        return "🔄"
    elif hasattr(task, 'priority') and task.priority == 'high':
        return "🔴"
    elif hasattr(task, 'priority') and task.priority == 'medium':
        return "🟡"
    else:
        return "⏳"


def get_today_completed_tasks(all_tasks) -> list:
    """오늘 완료된 작업들 가져오기"""
    from datetime import datetime, date
    today = date.today()
    completed_today = []
    
    for task in all_tasks:
        if task.completed and hasattr(task, 'completed_at'):
            try:
                completed_date = datetime.fromisoformat(task.completed_at).date()
                if completed_date == today:
                    completed_today.append(task)
            except:
                pass
    
    return completed_today


def estimate_remaining_time(pending_tasks) -> str:
    """남은 작업들의 예상 소요시간 계산"""
    total_hours = 0
    for task in pending_tasks:
        if hasattr(task, 'estimated_hours'):
            total_hours += task.estimated_hours if task.estimated_hours is not None else 0
        else:
            # 기본값: 작업당 2시간
            total_hours += 2
    
    if total_hours < 8:
        return f"{total_hours}시간"
    else:
        days = total_hours / 8  # 하루 8시간 기준
        return f"{days:.1f}일 ({total_hours}시간)"

def generate_complete_briefing(context: Any, structure: Dict[str, Any], cache_status: Dict[str, Any] = None) -> str:
    """완전한 프로젝트 브리핑 생성 - ProjectContext 전용"""
    briefing_lines = []
    cache_status = cache_status or {}
    debug_log(f"🐛 브리핑 함수: cache_status = {cache_status}")
    
    # context 타입 확인
    from core.models import ProjectContext
    is_pydantic = isinstance(context, ProjectContext)
    
    # Pydantic이 아니면 변환 시도
    if not is_pydantic:
        try:
            context = ProjectContext.from_dict(context)
            is_pydantic = True
        except:
            # 변환 실패시 기본 dict로 처리
            pass
    
    # 즉시 컨텍스트 정보 표시
    briefing_lines.append("\n" + "="*70)
    briefing_lines.append("📊 **현재 컨텍스트 정보 (즉시 표시)**")
    briefing_lines.append("="*70)
    
    if is_pydantic:
        briefing_lines.append(f"🎯 프로젝트: {context.project_name}")
        briefing_lines.append(f"📍 Phase: {getattr(context, 'metadata', {}).get('phase', 'initialization')}")
        
        current_task = context.current_task
        if current_task and isinstance(current_task, dict):
            briefing_lines.append(f"✏️ 현재 작업: [{current_task.get('id', 'N/A')}] {current_task.get('title', '없음')}")
        elif current_task:
            briefing_lines.append(f"✏️ 현재 작업: {current_task}")
        else:
            briefing_lines.append(f"✏️ 현재 작업: 설정되지 않음")
    else:
        # dict 처리
        briefing_lines.append(f"🎯 프로젝트: {context.get('project_name', 'Unknown')}")
        briefing_lines.append(f"📍 Phase: {context.get('phase', 'initialization')}")
        
        current_task = context.get('current_task')
        if current_task and isinstance(current_task, dict):
            briefing_lines.append(f"✏️ 현재 작업: [{current_task.get('id', 'N/A')}] {current_task.get('title', '없음')}")
        else:
            briefing_lines.append(f"✏️ 현재 작업: 설정되지 않음")
    
    # tasks 처리
    if (is_pydantic and context.plan) or (isinstance(context, dict) and 'plan' in context and context['plan']):
        all_tasks = context.get_all_tasks() if hasattr(context, 'get_all_tasks') else []
        # dict context에서 plan이 있는 경우
        if isinstance(context, dict) and 'plan' in context and context['plan']:
            plan = context['plan']
            if hasattr(plan, 'get_all_tasks'):
                all_tasks = plan.get_all_tasks()
        pending_tasks = [t for t in all_tasks if not t.completed]
        completed_tasks = [t for t in all_tasks if t.completed]
        
        if all_tasks:
            briefing_lines.append(f"\n  • 전체 작업: {len(all_tasks)}개 (완료: {len(completed_tasks)}, 대기: {len(pending_tasks)})")
        else:
            briefing_lines.append(f"\n  • 작업 현황: 등록된 작업 없음")
    else:
        briefing_lines.append(f"📋 작업 현황: 등록된 작업 없음")
    # 전체 요약 추가 (즉시 컨텍스트 정보 다음)
    if (is_pydantic and context.plan) or (isinstance(context, dict) and 'plan' in context and context['plan']):
        all_tasks = context.get_all_tasks() if hasattr(context, 'get_all_tasks') else []
        # dict context에서 plan이 있는 경우
        if isinstance(context, dict) and 'plan' in context and context['plan']:
            plan = context['plan']
            if hasattr(plan, 'get_all_tasks'):
                all_tasks = plan.get_all_tasks()
        if all_tasks:
            completed_count = len([t for t in all_tasks if t.completed])
            total_count = len(all_tasks)
            progress = (completed_count / total_count * 100) if total_count > 0 else 0
            
            briefing_lines.append(f"\n🎯 **프로젝트 진행 요약**")
            briefing_lines.append(f"  • 전체 진행률: {create_progress_bar(progress, width=20)}")
            briefing_lines.append(f"  • 작업 현황: {completed_count}/{total_count} 완료")
            
            # 오늘의 성과
            today_completed = get_today_completed_tasks(all_tasks)
            if today_completed:
                briefing_lines.append(f"  • 오늘 완료: {len(today_completed)}개 작업")
            
            # 현재 진행 중
            in_progress = [t for t in all_tasks if hasattr(t, 'in_progress') and t.in_progress and not t.completed]
            if in_progress:
                briefing_lines.append(f"  • 진행 중: {in_progress[0].title[:30]}...")
            
            # 다음 목표
            pending = [t for t in all_tasks if not t.completed]
            if pending:
                high_priority = [t for t in pending if hasattr(t, 'priority') and t.priority == 'high']
                next_target = high_priority[0] if high_priority else pending[0]
                briefing_lines.append(f"  • 다음 목표: {next_target.title[:30]}...")
    
    
    briefing_lines.append("\n" + "="*70)
    briefing_lines.append("📊 **프로젝트 상태 브리핑**")
    briefing_lines.append("="*70)
    
    # 1. 프로젝트 정보
    briefing_lines.append(f"\n📍 **프로젝트 정보**")
    if is_pydantic:
        briefing_lines.append(f"  • 이름: {context.project_name}")
        briefing_lines.append(f"  • 경로: {context.project_path}")
        briefing_lines.append(f"  • 언어: Python/TypeScript")
    else:
        briefing_lines.append(f"  • 이름: {context.get('project_name', 'Unknown')}")
        briefing_lines.append(f"  • 경로: {context.get('project_path', os.getcwd())}")
        briefing_lines.append(f"  • 언어: {context.get('language', 'Python/TypeScript')}")
    
    # 파일 통계
    stats = structure.get("statistics", {})
    briefing_lines.append(f"  • 전체 파일: {stats.get('total_files', 0)}개")
    
    # 주요 확장자별 통계
    ext_stats = stats.get("by_extension", {})
    if ext_stats:
        top_exts = sorted(ext_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        ext_str = ", ".join([f"{ext or 'no-ext'}: {count}" for ext, count in top_exts])
        briefing_lines.append(f"  • 파일 타입: {ext_str}")
    
    # 2. 프로젝트 구조 하이라이트
    briefing_lines.append(f"\n📂 **프로젝트 구조**")
    key_files = structure.get("key_files", {})
    
    if key_files.get("entry_points"):
        briefing_lines.append(f"  • 진입점: {', '.join(key_files['entry_points'][:3])}")
    
    if key_files.get("configs"):
        briefing_lines.append(f"  • 설정 파일: {', '.join(key_files['configs'][:3])}")
    
    # 3. 최근 수정된 파일들
    briefing_lines.append(f"\n📝 **최근 수정된 파일** (상위 5개)")
    recent_files = structure.get("recent_files", [])[:5]
    for file_info in recent_files:
        modified = file_info["modified"].split("T")[0]  # 날짜만
        briefing_lines.append(f"  • {file_info['path']} ({modified})")
    
    # 4. 현재 작업 - 더 자세히
    briefing_lines.append(f"\n📋 **작업 상태**")
    if is_pydantic:
        if context.current_task and context.plan:
            task_obj = context.plan.get_task_by_id(context.current_task)
            if task_obj:
                status_emoji = format_task_status(task_obj)
                briefing_lines.append(f"  {status_emoji} 현재 작업: [{task_obj.id}] {task_obj.title}")
                briefing_lines.append(f"  • 상태: {'✅ 완료' if task_obj.completed else '🔄 진행 중' if hasattr(task_obj, 'in_progress') and task_obj.in_progress else '⏳ 대기 중'}")
                
                # 추가 정보
                if hasattr(task_obj, 'assigned_to'):
                    briefing_lines.append(f"  • 담당: {task_obj.assigned_to}")
                if hasattr(task_obj, 'started_at') and task_obj.started_at:
                    briefing_lines.append(f"  • 시작: {task_obj.started_at}")
                if hasattr(task_obj, 'progress_percentage'):
                    progress_bar = create_progress_bar(task_obj.progress_percentage, width=20)
                    briefing_lines.append(f"  • 진행도: {progress_bar}")
            else:
                briefing_lines.append(f"  • 현재 작업: {context.current_task}")
        else:
            briefing_lines.append(f"  • 현재 작업: 없음")
        
        # Phase별 진행 상황
        if ((hasattr(context, 'plan') and context.plan) or (isinstance(context, dict) and 'plan' in context and context['plan'])) and hasattr(context.get('plan', context.plan if hasattr(context, 'plan') else None), 'phases'):
            briefing_lines.append(f"\n📂 **Phase별 진행 상황**")
            for phase_id in context.plan.phase_order[:3]:  # 처음 3개 Phase만
                phase = context.plan.phases.get(phase_id)
                if phase and phase.tasks:
                    phase_completed = len([t for t in phase.tasks.values() if t.completed])
                    phase_total = len(phase.tasks)
                    phase_progress = (phase_completed / phase_total * 100) if phase_total > 0 else 0
                    
                    briefing_lines.append(f"  • {phase.name}: {phase_progress:.0f}% ({phase_completed}/{phase_total})")
                    if phase_progress < 100:
                        # 해당 Phase의 다음 작업 표시
                        next_in_phase = next((t for t in phase.tasks.values() if not t.completed), None)
                        if next_in_phase:
                            briefing_lines.append(f"    다음: [{next_in_phase.id}] {next_in_phase.title}")
    else:
        current_task = context.get('current_task') if not is_pydantic else None
        if current_task:
            # current_task가 문자열(Task ID)인 경우
            if isinstance(current_task, str):
                briefing_lines.append(f"  • 현재 작업 ID: {current_task}")
                # Plan에서 Task 정보 가져오기
                if 'plan' in context and context['plan']:
                    plan = context['plan']
                    # plan이 dict가 아닌 객체인 경우
                    if hasattr(plan, 'get_task_by_id'):
                        task_obj = plan.get_task_by_id(current_task)
                        if task_obj:
                            briefing_lines.append(f"  • 작업명: {task_obj.title}")
                            briefing_lines.append(f"  • 상태: {'✅ 완료' if task_obj.completed else '⏳ 진행 중'}")
            # current_task가 dict인 경우 (기존 코드)
            else:
                briefing_lines.append(f"  • 현재 작업: [{current_task.get('id', 'N/A')}] {current_task.get('title', '제목 없음')}")
                briefing_lines.append(f"  • 상태: {'✅ 완료' if current_task.get('completed') else '⏳ 진행 중'}")
        else:
            briefing_lines.append(f"  • 현재 작업: 없음")
    # 4-1. 진행률 표시
    if (is_pydantic and context.plan) or (isinstance(context, dict) and 'plan' in context and context['plan']):
        all_tasks = context.get_all_tasks() if hasattr(context, 'get_all_tasks') else []
        # dict context에서 plan이 있는 경우
        if isinstance(context, dict) and 'plan' in context and context['plan']:
            plan = context['plan']
            if hasattr(plan, 'get_all_tasks'):
                all_tasks = plan.get_all_tasks()
        completed_tasks = [t for t in all_tasks if t.completed]
        pending_tasks = [t for t in all_tasks if not t.completed]
        in_progress_tasks = [t for t in pending_tasks if hasattr(t, 'in_progress') and t.in_progress]
        
        if all_tasks:
            total_progress = (len(completed_tasks) / len(all_tasks) * 100)
            
            # 시각적 진행률 바 추가
            briefing_lines.append(f"\n📊 **전체 진행 상황**")
            progress_bar = create_progress_bar(total_progress)
            briefing_lines.append(f"  {progress_bar}")
            briefing_lines.append(f"  • ✅ 완료: {len(completed_tasks)}개")
            briefing_lines.append(f"  • 🔄 진행 중: {len(in_progress_tasks)}개")
            briefing_lines.append(f"  • ⏳ 대기: {len(pending_tasks) - len(in_progress_tasks)}개")
            
            # 예상 남은 시간
            if pending_tasks:
                remaining_time = estimate_remaining_time(pending_tasks)
                briefing_lines.append(f"  • ⏱️ 예상 남은 시간: {remaining_time}")
            
            # 오늘 완료한 작업들
            today_completed = get_today_completed_tasks(all_tasks)
            if today_completed:
                briefing_lines.append(f"\n✨ **오늘 완료한 작업** ({len(today_completed)}개)")
                for task in today_completed[:3]:  # 최대 3개만 표시
                    briefing_lines.append(f"  ✅ [{task.id}] {task.title}")
                if len(today_completed) > 3:
                    briefing_lines.append(f"  ... 외 {len(today_completed) - 3}개")
            
            # 현재 진행 중인 작업 상세
            if in_progress_tasks:
                briefing_lines.append(f"\n🔄 **현재 진행 중인 작업**")
                for task in in_progress_tasks:
                    status_emoji = format_task_status(task)
                    briefing_lines.append(f"  {status_emoji} [{task.id}] {task.title}")
                    if hasattr(task, 'progress_percentage'):
                        task_progress_bar = create_progress_bar(task.progress_percentage, width=20)
                        briefing_lines.append(f"     {task_progress_bar}")
                    if hasattr(task, 'current_step'):
                        briefing_lines.append(f"     현재 단계: {task.current_step}")
            
            # 다음 할일 (우선순위별)
            if pending_tasks:
                briefing_lines.append(f"\n🎯 **다음 할일** (우선순위순)")
                
                # 우선순위별로 정렬
                high_priority = [t for t in pending_tasks if hasattr(t, 'priority') and t.priority == 'high']
                medium_priority = [t for t in pending_tasks if hasattr(t, 'priority') and t.priority == 'medium']
                normal_priority = [t for t in pending_tasks if not hasattr(t, 'priority') or t.priority == 'normal']
                
                # 높은 우선순위
                if high_priority:
                    briefing_lines.append(f"\n  🔴 **긴급**")
                    for task in high_priority[:2]:
                        briefing_lines.append(f"    • [{task.id}] {task.title}")
                        if hasattr(task, 'deadline'):
                            briefing_lines.append(f"      마감: {task.deadline}")
                
                # 중간 우선순위
                if medium_priority:
                    briefing_lines.append(f"\n  🟡 **중요**")
                    for task in medium_priority[:2]:
                        briefing_lines.append(f"    • [{task.id}] {task.title}")
                
                # 일반 우선순위
                if normal_priority:
                    briefing_lines.append(f"\n  🟢 **일반**")
                    for task in normal_priority[:3]:
                        briefing_lines.append(f"    • [{task.id}] {task.title}")
                
                # 다음 작업 추천
                next_task = high_priority[0] if high_priority else (medium_priority[0] if medium_priority else pending_tasks[0])
                briefing_lines.append(f"\n  💡 **추천 다음 작업**: [{next_task.id}] {next_task.title}")
                if hasattr(next_task, 'estimated_time'):
                    briefing_lines.append(f"     예상 시간: {next_task.estimated_time}")
                if hasattr(next_task, 'description') and next_task.description:
                    desc_preview = next_task.description[:80] + "..." if len(next_task.description) > 80 else next_task.description
                    briefing_lines.append(f"     설명: {desc_preview}")
                briefing_lines.append(f"\n  🚀 시작하려면: `next_task()` 명령을 사용하세요")
    # 5. Phase 정보 추가
    phase = getattr(context, 'phase', None) if is_pydantic else context.get('phase')
    if phase:
        briefing_lines.append(f"\n🎯 **현재 Phase**: {phase}")
        phase_goals = {
            "initialization": "프로젝트 구조 파악 및 초기 설정",
            "planning": "작업 계획 수립 및 우선순위 결정", 
            "development": "기능 개발 및 코드 작성",
            "testing": "테스트 작성 및 실행",
            "refactoring": "코드 개선 및 최적화",
            "deployment": "배포 준비 및 실행",
            "maintenance": "버그 수정 및 유지보수"
        }
        briefing_lines.append(f"  • Phase 목표: {phase_goals.get(phase, '설정되지 않음')}")

    
    # 6. Wisdom 통계 추가
    try:
        from project_wisdom import get_wisdom_manager
        wisdom = get_wisdom_manager()
        if wisdom and hasattr(wisdom, 'wisdom_data'):
            mistakes = wisdom.wisdom_data.get('common_mistakes', {})
            if mistakes:
                briefing_lines.append(f"\n🧠 **프로젝트 지혜**")
                briefing_lines.append(f"  • 추적된 실수: {len(mistakes)}종류")
                # 가장 많이 발생한 실수 1개
                if mistakes:
                    top_mistake = max(mistakes.items(), key=lambda x: x[1].get('count', 0))
                    briefing_lines.append(f"  • 가장 빈번한 실수: {top_mistake[0]} ({top_mistake[1].get('count', 0)}회)")
    except:
        pass
    
    # 7. 파일 캐시 정보
    if is_pydantic:
        file_cache = getattr(context, 'file_cache', {})
    else:
        file_cache = context.get('file_cache', {})
        
    if file_cache and hasattr(file_cache, 'keys'):
        briefing_lines.append(f"\n💾 **캐시 정보**")
        briefing_lines.append(f"  • 캐시된 파일: {len(file_cache)}개")
        cache_size = sum(len(str(v)) for v in file_cache.values() if v)
        briefing_lines.append(f"  • 캐시 크기: ~{cache_size // 1024}KB")
    
    
    # 8. 캐시 정보 추가
    debug_log(f"🐛 캐시 정보 섹션 도달: cache_status = {cache_status}")
    if cache_status:
        briefing_lines.append(f"\n💾 **캐시 상태**")
        briefing_lines.append(f"  • 캐시 로드: {'✅ 성공' if cache_status.get('loaded_from_cache') else '🔄 새로 생성'}")
        briefing_lines.append(f"  • 캐시 크기: {cache_status.get('cache_size', 0)} bytes")
        # analyzed_files 개수 계산
        analyzed_count = 0
        if is_pydantic and hasattr(context, 'analyzed_files'):
            analyzed_count = len(context.analyzed_files)
        elif isinstance(context, dict) and 'analyzed_files' in context:
            analyzed_count = len(context.get('analyzed_files', {}))
        else:
            analyzed_count = cache_status.get('analyzed_files_count', 0)
        
        briefing_lines.append(f"  • 분석된 파일: {analyzed_count}개")

    return "\n".join(briefing_lines)

def find_project_root(project_name: str) -> Optional[Path]:
    """프로젝트 루트 디렉토리 찾기"""
    # 현재 작업 디렉토리가 프로젝트면 그대로 사용
    current_dir = Path.cwd()
    if current_dir.name == project_name:
        return current_dir
    
    # 상위 디렉토리에서 찾기
    for parent in current_dir.parents:
        if parent.name == project_name:
            return parent
    
    # Desktop에서 찾기
    desktop_path = Path.home() / "Desktop" / project_name
    if desktop_path.exists():
        return desktop_path
    
    # 현재 디렉토리의 하위에서 찾기
    for child in current_dir.iterdir():
        if child.is_dir() and child.name == project_name:
            return child
    
    return None


def get_project_wisdom_insights(project_name: str) -> Dict[str, Any]:
    """프로젝트별 Wisdom 기반 인사이트 제공"""
    wisdom = get_wisdom_manager()
    
    insights = {
        "recent_mistakes": [],
        "best_practices": [],
        "warnings": [],
        "tips": []
    }
    
    # 최근 실수 확인
    for mistake_type, data in wisdom.wisdom_data.get('common_mistakes', {}).items():
        if data['count'] > 0:
            insights['recent_mistakes'].append({
                'type': mistake_type,
                'count': data['count'],
                'tip': wisdom._get_mistake_tip(mistake_type)
            })
    
    # 프로젝트별 베스트 프랙티스
    for practice in wisdom.wisdom_data.get('best_practices', []):
        if project_name.lower() in practice.lower() or 'general' in practice.lower():
            insights['best_practices'].append(practice)
    
    # 경고 사항
    if len(insights['recent_mistakes']) > 3:
        insights['warnings'].append("⚠️ 최근 실수가 많습니다. 주의하세요!")
    
    return insights


def display_project_briefing(context, analyzer_result: Dict, wisdom_insights: Dict, verbose: bool = True):
    """프로젝트 브리핑 표시 (간결/상세 모드 지원)"""
    print("\n" + "=" * 70)
    print("📊 **프로젝트 상태 브리핑**")
    print("=" * 70)
    
    # 기본 정보 (항상 표시)
    print(f"\n📍 **프로젝트 정보**")
    print(f"  • 이름: {context.project_name}")
    print(f"  • 경로: {context.project_path}")
    print(f"  • 언어: {context.language or 'Unknown'}")
    print(f"  • 전체 파일: {len(analyzer_result.get('all_files', []))}개")
    
    if verbose:
        # 상세 정보
        print(f"\n📂 **프로젝트 구조**")
        dirs = analyzer_result.get('structure', {}).get('directories', [])
        print(f"  • 디렉토리: {len(dirs)}개")
        
        # 최근 수정 파일
        if analyzer_result.get('modified_files'):
            print(f"\n🔄 **최근 수정된 파일** (상위 5개):")
            for file in analyzer_result['modified_files'][:5]:
                print(f"  • {file['path']}")
    
    # Wisdom 인사이트 (중요한 것만)
    if wisdom_insights.get('warnings'):
        print(f"\n⚠️ **주의사항**")
        for warning in wisdom_insights['warnings']:
            print(f"  {warning}")
    
    if wisdom_insights.get('recent_mistakes') and verbose:
        print(f"\n❌ **최근 실수** (주의하세요!):")
        for mistake in wisdom_insights['recent_mistakes'][:3]:
            print(f"  • {mistake['type']}: {mistake['count']}회")
    
    print("\n" + "=" * 70)


def track_flow_performance(func_name: str, duration: float, success: bool):
    """flow 명령 성능 추적"""
    if not PERFORMANCE_TRACKING:
        return
    
    wisdom = get_wisdom_manager()
    perf_data = wisdom.wisdom_data.get('performance_metrics', {})
    
    if func_name not in perf_data:
        perf_data[func_name] = {
            'total_calls': 0,
            'successful_calls': 0,
            'total_duration': 0,
            'average_duration': 0
        }
    
    perf_data[func_name]['total_calls'] += 1
    if success:
        perf_data[func_name]['successful_calls'] += 1
    perf_data[func_name]['total_duration'] += duration
    perf_data[func_name]['average_duration'] = (
        perf_data[func_name]['total_duration'] / perf_data[func_name]['total_calls']
    )
    
    wisdom.wisdom_data['performance_metrics'] = perf_data
    wisdom._save_wisdom()


def validate_cache_integrity(cache_path: str) -> bool:
    """캐시 파일 무결성 검증"""
    try:
        if not os.path.exists(cache_path):
            return False
        
        # 파일 크기 확인
        size_mb = os.path.getsize(cache_path) / (1024 * 1024)
        if size_mb > MAX_CACHE_SIZE_MB:
            smart_print(f"⚠️ 캐시 크기 초과: {size_mb:.1f}MB > {MAX_CACHE_SIZE_MB}MB")
            return False
        
        # 캐시 만료 확인
        mod_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        age_hours = (datetime.now() - mod_time).total_seconds() / 3600
        if age_hours > CACHE_EXPIRY_HOURS:
            smart_print(f"⚠️ 캐시 만료: {age_hours:.1f}시간 경과")
            return False
        
        return True
    except Exception as e:
        smart_print(f"❌ 캐시 검증 실패: {e}")
        return False


def create_context_backup(project_name: str, context: Any) -> Optional[str]:
    """프로젝트 컨텍스트 자동 백업"""
    try:
        # 백업 디렉토리 생성
        backup_dir = Path("memory/context_backups") / datetime.now().strftime("%Y-%m-%d")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 백업 파일명
        timestamp = datetime.now().strftime("%H%M%S")
        backup_file = backup_dir / f"{project_name}_context_{timestamp}.json"
        
        # 컨텍스트를 JSON으로 저장
        context_data = {
            'project_name': project_name,
            'backup_time': datetime.now().isoformat(),
            'context': context if isinstance(context, dict) else context.dict() if hasattr(context, 'dict') else str(context)
        }
        
        # datetime 객체를 문자열로 변환하는 default 함수
        def json_default(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, indent=2, ensure_ascii=False, default=json_default)
        
        # 오래된 백업 정리 (7일 이상)
        cleanup_old_backups(backup_dir.parent, days=7)
        
        return str(backup_file)
    except Exception as e:
        smart_print(f"⚠️ 컨텍스트 백업 실패: {e}")
        return None


def cleanup_old_backups(backup_root: Path, days: int = 7):
    """오래된 백업 파일 정리"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for date_dir in backup_root.iterdir():
        if date_dir.is_dir():
            try:
                dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                if dir_date < cutoff_date:
                    shutil.rmtree(date_dir)
                    smart_print(f"🗑️ 오래된 백업 삭제: {date_dir.name}")
            except:
                pass


def load_project_config(project_path: Path) -> Dict[str, Any]:
    """프로젝트별 설정 파일 로드"""
    config_file = project_path / ".ai-brain.config.json"
    default_config = {
        "verbose": True,
        "auto_backup": True,
        "scan_exclude": ["node_modules", ".git", "__pycache__", "dist", "build"],
        "file_limit": 1000,
        "cache_expiry_hours": 24
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 기본 설정과 병합
                default_config.update(user_config)
                smart_print(f"📋 프로젝트 설정 로드: {config_file.name}")
        except Exception as e:
            smart_print(f"⚠️ 설정 파일 로드 실패: {e}")
    
    return default_config


def save_project_config(project_path: Path, config: Dict[str, Any]):
    """프로젝트 설정 저장"""
    config_file = project_path / ".ai-brain.config.json"
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        smart_print(f"💾 프로젝트 설정 저장: {config_file.name}")
    except Exception as e:
        smart_print(f"❌ 설정 저장 실패: {e}")


def analyze_folder_with_context(folder_path: str, recursive: bool = True, extensions: list = None) -> Dict[str, Any]:
    """
    폴더와 하위 파일들을 분석하여 컨텍스트 정보 생성
    
    Args:
        folder_path: 분석할 폴더 경로
        recursive: 하위 폴더도 분석할지 여부
        extensions: 분석할 파일 확장자 목록
        
    Returns:
        폴더 분석 결과 (구조, 파일 정보, 통계 등)
    """
    from pathlib import Path
    
    folder_path = Path(folder_path)
    if not folder_path.exists():
        return {"error": f"폴더가 존재하지 않습니다: {folder_path}"}
    
    if extensions is None:
        extensions = ['.py', '.ts', '.js', '.jsx', '.tsx', '.md', '.json']
    
    result = {
        "folder": str(folder_path),
        "name": folder_path.name,
        "structure": {},
        "files": {},
        "statistics": {
            "total_files": 0,
            "total_dirs": 0,
            "by_extension": {},
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0
        }
    }
    
    # 폴더 구조 구축
    def build_structure(path: Path, parent_dict: dict):
        try:
            for item in path.iterdir():
                if item.is_dir():
                    if item.name not in ['.git', '__pycache__', 'node_modules', '.venv', 'dist', 'build']:
                        result["statistics"]["total_dirs"] += 1
                        parent_dict[item.name] = {}
                        if recursive:
                            build_structure(item, parent_dict[item.name])
                elif item.is_file() and item.suffix in extensions:
                    parent_dict[item.name] = "file"
                    result["statistics"]["total_files"] += 1
                    
                    # 파일 통계
                    ext = item.suffix
                    result["statistics"]["by_extension"][ext] = result["statistics"]["by_extension"].get(ext, 0) + 1
                    
                    # 파일 분석 (Python 파일의 경우)
                    if item.suffix == '.py':
                        try:
                            relative_path = item.relative_to(folder_path)
                            file_result = helpers.parse_with_snippets(str(item))
                            if file_result['parsing_success']:
                                result["files"][str(relative_path)] = {
                                    "functions": len(file_result.get('functions', [])),
                                    "classes": len(file_result.get('classes', [])),
                                    "lines": file_result.get('line_count', 0)
                                }
                                result["statistics"]["total_functions"] += len(file_result.get('functions', []))
                                result["statistics"]["total_classes"] += len(file_result.get('classes', []))
                                result["statistics"]["total_lines"] += file_result.get('line_count', 0)
                        except:
                            pass
        except PermissionError:
            pass
    
    build_structure(folder_path, result["structure"])
    
    # 요약 정보 추가
    result["summary"] = generate_folder_summary(result)
    
    return result


def generate_folder_summary(analysis: Dict[str, Any]) -> str:
    """폴더 분석 결과를 요약"""
    stats = analysis['statistics']
    summary = f"""📂 {analysis['name']}
├─ 📄 파일: {stats['total_files']}개
├─ 📁 폴더: {stats['total_dirs']}개
├─ 📏 총 라인: {stats['total_lines']:,}줄
├─ 🔧 함수: {stats['total_functions']}개
├─ 🏗️ 클래스: {stats['total_classes']}개
└─ 📊 파일 유형: {', '.join(f"{k}({v})" for k, v in stats['by_extension'].items())}"""
    return summary


def flow_analyze_folder(folder_path: str, save_context: bool = True, verbose: bool = True) -> Dict[str, Any]:
    """
    특정 폴더를 분석하고 프로젝트 컨텍스트에 추가
    
    Args:
        folder_path: 분석할 폴더 경로
        save_context: 컨텍스트를 저장할지 여부
        verbose: 상세 정보 출력 여부
    """
    smart_print(f"\n📂 폴더 분석 시작: {folder_path}")
    
    # 1. 폴더 분석
    analysis = analyze_folder_with_context(folder_path, recursive=True)
    
    if "error" in analysis:
        smart_print(f"❌ {analysis['error']}")
        return analysis
    
    # 2. 분석 결과 출력
    if verbose:
        smart_print("\n" + analysis['summary'])
        
        # 주요 파일 정보
        if analysis['files']:
            smart_print("\n📄 주요 파일:")
            for file_path, info in list(analysis['files'].items())[:5]:
                smart_print(f"  - {file_path}: {info.get('functions', 0)}개 함수, {info.get('lines', 0)}줄")
    
    # 3. 컨텍스트 생성
    folder_context = {
        "type": "folder_analysis",
        "path": folder_path,
        "name": analysis['name'],
        "analysis": analysis,
        "timestamp": datetime.now().isoformat()
    }
    
    # 4. 컨텍스트 저장
    if save_context:
        # 현재 컨텍스트에 추가
        try:
            current_context = helpers.get_context()
            if hasattr(current_context, 'metadata'):
                if 'folder_analyses' not in current_context.metadata:
                    current_context.metadata['folder_analyses'] = {}
                current_context.metadata['folder_analyses'][analysis['name']] = folder_context
                helpers.save_context()
                smart_print(f"\n💾 폴더 분석 결과가 컨텍스트에 저장되었습니다.")
        except:
            pass
        
        # 별도 파일로도 저장
        context_file = Path(f"memory/folder_contexts/{analysis['name']}_context.json")
        context_file.parent.mkdir(parents=True, exist_ok=True)
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(folder_context, f, indent=2, ensure_ascii=False)
        smart_print(f"📁 컨텍스트 파일 저장: {context_file.name}")
    
    # 5. Wisdom 시스템에 기록
    wisdom = get_wisdom_manager()
    wisdom.add_best_practice(
        f"폴더 '{analysis['name']}' 분석 - {analysis['statistics']['total_files']}개 파일, {analysis['statistics']['total_lines']:,}줄",
        "folder_analysis"
    )
    
    return folder_context


def flow_compare_folders(folder1: str, folder2: str) -> Dict[str, Any]:
    """두 폴더를 비교 분석"""
    smart_print(f"\n🔄 폴더 비교: {folder1} vs {folder2}")
    
    # 각 폴더 분석
    analysis1 = analyze_folder_with_context(folder1)
    analysis2 = analyze_folder_with_context(folder2)
    
    # 비교 결과
    comparison = {
        "folder1": folder1,
        "folder2": folder2,
        "differences": {
            "files": {
                "only_in_1": [],
                "only_in_2": [],
                "in_both": []
            },
            "statistics": {
                "total_files": {
                    folder1: analysis1['statistics']['total_files'],
                    folder2: analysis2['statistics']['total_files']
                },
                "total_lines": {
                    folder1: analysis1['statistics']['total_lines'],
                    folder2: analysis2['statistics']['total_lines']
                }
            }
        }
    }
    
    # 파일 비교
    files1 = set(analysis1['files'].keys())
    files2 = set(analysis2['files'].keys())
    
    comparison['differences']['files']['only_in_1'] = list(files1 - files2)
    comparison['differences']['files']['only_in_2'] = list(files2 - files1)
    comparison['differences']['files']['in_both'] = list(files1 & files2)
    
    # 결과 출력
    smart_print(f"\n📊 비교 결과:")
    smart_print(f"  - {folder1}에만 있는 파일: {len(comparison['differences']['files']['only_in_1'])}개")
    smart_print(f"  - {folder2}에만 있는 파일: {len(comparison['differences']['files']['only_in_2'])}개")
    smart_print(f"  - 공통 파일: {len(comparison['differences']['files']['in_both'])}개")
    
    return comparison



def sync_context_from_plan(context: Any, plan: Any) -> Any:
    """Plan 객체의 데이터를 context 최상위 레벨로 동기화
    
    Args:
        context: 업데이트할 컨텍스트 (dict 또는 ProjectContext 객체)
        plan: WorkflowManager의 Plan 객체
        
    Returns:
        업데이트된 context
    """
    if not plan:
        return context
    
    # context가 dict인지 객체인지 확인
    is_dict = isinstance(context, dict)
    
    # 1. 현재 Phase 설정 (None이면 첫 번째 Phase로 설정)
    current_phase = plan.current_phase
    if not current_phase and plan.phase_order:
        current_phase = plan.phase_order[0]
    
    if is_dict:
        context['phase'] = current_phase
    else:
        # ProjectContext 객체인 경우 동적으로 속성 추가
        setattr(context, 'phase', current_phase)
    
    # 2. 전체 작업 목록 생성
    all_tasks = []
    for phase_id, phase in plan.phases.items():
        for task_id, task in phase.tasks.items():
            task_dict = {
                'id': task.id,
                'title': task.title,
                'status': task.status.value if hasattr(task.status, 'value') else str(task.status),
                'phase_id': task.phase_id,
                'priority': task.priority,
                'description': task.description
            }
            all_tasks.append(task_dict)
    
    if is_dict:
        context['tasks'] = all_tasks
    else:
        # ProjectContext는 tasks가 다른 구조이므로 all_tasks 속성 추가
        setattr(context, 'all_tasks', all_tasks)
    
    # 3. 현재 Phase 정보 추가
    if current_phase and current_phase in plan.phases:
        current_phase_obj = plan.phases[current_phase]
        if is_dict:
            context['phase_name'] = current_phase_obj.name
            context['phase_progress'] = current_phase_obj.progress
        else:
            setattr(context, 'phase_name', current_phase_obj.name)
            setattr(context, 'phase_progress', current_phase_obj.progress)
    
    # 4. 전체 진행률 추가
    if is_dict:
        context['overall_progress'] = plan.overall_progress
    else:
        setattr(context, 'overall_progress', plan.overall_progress)
    
    # 5. Phase별 작업 수 추가 (디버깅용)
    phase_task_counts = {
        phase_id: len(phase.tasks) 
        for phase_id, phase in plan.phases.items()
    }
    
    if is_dict:
        context['phase_task_counts'] = phase_task_counts
    else:
        setattr(context, 'phase_task_counts', phase_task_counts)
    
    return context
    
    # context가 dict인지 객체인지 확인
    is_dict = isinstance(context, dict)
    
    # 1. 현재 Phase 설정
    if is_dict:
        context['phase'] = plan.current_phase
    else:
        # ProjectContext 객체인 경우 동적으로 속성 추가
        setattr(context, 'phase', plan.current_phase)
    
    # 2. 전체 작업 목록 생성
    all_tasks = []
    for phase_id, phase in plan.phases.items():
        for task_id, task in phase.tasks.items():
            task_dict = {
                'id': task.id,
                'title': task.title,
                'status': task.status.value if hasattr(task.status, 'value') else str(task.status),
                'phase_id': task.phase_id,
                'priority': task.priority,
                'description': task.description
            }
            all_tasks.append(task_dict)
    
    if is_dict:
        context['tasks'] = all_tasks
    else:
        # ProjectContext는 tasks가 다른 구조이므로 all_tasks 속성 추가
        setattr(context, 'all_tasks', all_tasks)
    
    # 3. 현재 Phase 정보 추가
    if plan.current_phase and plan.current_phase in plan.phases:
        current_phase_obj = plan.phases[plan.current_phase]
        if is_dict:
            context['phase_name'] = current_phase_obj.name
            context['phase_progress'] = current_phase_obj.progress
        else:
            setattr(context, 'phase_name', current_phase_obj.name)
            setattr(context, 'phase_progress', current_phase_obj.progress)
    
    # 4. 전체 진행률 추가
    if is_dict:
        context['overall_progress'] = plan.overall_progress
    else:
        setattr(context, 'overall_progress', plan.overall_progress)
    
    # 5. Phase별 작업 수 추가 (디버깅용)
    phase_task_counts = {
        phase_id: len(phase.tasks) 
        for phase_id, phase in plan.phases.items()
    }
    
    if is_dict:
        context['phase_task_counts'] = phase_task_counts
    else:
        setattr(context, 'phase_task_counts', phase_task_counts)
    
    return context
def flow_project(project_name: str, verbose: Optional[bool] = None) -> Dict[str, Any]:
    """리팩토링된 flow_project - 자동 백업 및 프로젝트 설정 지원"""
    import time
    start_time = time.time()
    
    smart_print(f"🚀 **'{project_name}'** 프로젝트 세션을 시작합니다...")
    
    # helpers를 전역에서 가져오기
    helpers_obj = None
    
    # 1. global_helpers 확인 (json_repl_session에서 설정)
    if 'global_helpers' in globals():
        helpers_obj = globals()['global_helpers']
    # 2. 직접 전역에서 찾기
    elif 'helpers' in globals():
        helpers_obj = globals()['helpers']
    # 3. __main__ 모듈에서 찾기
    elif hasattr(sys.modules.get('__main__', None), 'helpers'):
        helpers_obj = sys.modules.get('__main__').helpers
    
    if not helpers_obj:
        raise RuntimeError("helpers 객체를 찾을 수 없습니다. execute_code 환경에서 실행하세요.")
    
    result = {
        'success': False,
        'project_name': project_name,
        'project_path': None,
        'context': None,
        'analysis': None,
        'error': None,
        'backup_path': None
    }
    
    # 이전 컨텍스트 백업
    try:
        current_context = helpers_obj.get_context()
        if current_context and hasattr(current_context, 'project_name'):
            if current_context.project_name != project_name:
                backup_path = create_context_backup(current_context.project_name, current_context)
                if backup_path:
                    smart_print(f"💾 이전 프로젝트 컨텍스트 백업: {Path(backup_path).name}")
                    result['backup_path'] = backup_path
    except:
        pass  # 백업 실패해도 계속 진행
    
    try:
        # 1. 프로젝트 이름 추출 및 경로 찾기
        clean_name = project_name.strip()  # extract_project_name 대신 직접 처리
        project_path = find_project_root(clean_name)  # find_project_path 대신 find_project_root 사용
        
        if not project_path:
            raise ValueError(f"프로젝트를 찾을 수 없습니다: {clean_name}")
        
        result['project_path'] = str(project_path)
        
        # 2. 작업 디렉토리 변경
        os.chdir(project_path)
        smart_print(f"📁 작업 디렉토리 변경: {project_path}")
        
        # 3. 프로젝트 설정 로드
        project_config = load_project_config(project_path)
        
        # verbose 매개변수가 None이면 설정 파일의 값 사용
        if verbose is None:
            verbose = project_config.get('verbose', True)
        
        # 4. Context 초기화 및 로드
        helpers_obj.initialize_context(project_path)
        context = helpers_obj.get_context()
        
        # 컨텍스트가 None이면 빈 딕셔너리로 초기화
        if context is None:
            context = {
                'project_name': clean_name,
                'project_path': str(project_path),                'created_at': datetime.now().isoformat()
            }
        
        # WorkflowManager의 context와 동기화
        try:
            from python.core.workflow_manager import get_workflow_manager
            workflow_manager = get_workflow_manager()
            
            # workflow_manager의 context가 ProjectContext 타입이고 같은 프로젝트인 경우
            if hasattr(workflow_manager, 'context') and hasattr(workflow_manager.context, 'project_name'):
                if workflow_manager.context.project_name == clean_name:
                    # plan 정보가 있으면 추가
                    if hasattr(workflow_manager.context, 'plan') and workflow_manager.context.plan:
                        context['plan'] = workflow_manager.context.plan
                        sync_context_from_plan(context, context['plan'])
                        context['current_task'] = getattr(workflow_manager.context, 'current_task', None)
                        # context['phase']는 sync_context_from_plan에서 설정됨
                    
                    smart_print("✅ WorkflowManager context 동기화 완료")
        except Exception as e:
            smart_print(f"⚠️ WorkflowManager context 동기화 중 오류: {e}")
        
        result['context'] = context
        
        # 5. 프로젝트 자동 분석 또는 캐시 사용
        smart_print("\n📂 프로젝트 구조를 분석하는 중...")
        
        try:
            analyzer = ProjectAnalyzer(project_path)
            analysis_result = analyzer.analyze_and_update()
            
            # 파일 구조 업데이트
            directory_tree = analysis_result.get('structure', {})
            file_count = analysis_result.get('file_count', 0)
            
        except Exception as e:
            print(f"⚠️ ProjectAnalyzer 오류 (계속 진행): {e}")
            # 기본값 설정
            analysis_result = {}
            directory_tree = {}
            file_count = 0
        analyzer = ProjectAnalyzer(project_path)
        # 설정에서 제외 패턴 적용
        if hasattr(analyzer, 'ignore_patterns'):
            analyzer.ignore_patterns.extend(project_config.get('scan_exclude', []))
        
        analysis_result = analyzer.analyze_and_update()
        result['analysis'] = analysis_result
        
        # 6. Wisdom 인사이트 가져오기
        try:
            from project_wisdom import get_wisdom_manager
            wisdom = get_wisdom_manager()
            
            # 최근 실수 경고
            mistakes = wisdom.wisdom_data.get('common_mistakes', {})
            if mistakes and verbose:
                smart_print("\n⚠️ 최근 주의사항:")
                for mistake, data in list(mistakes.items())[:3]:
                    if data['count'] > 0:
                        smart_print(f"  - {mistake}: {data['count']}회 발생")
        except:
            pass  # Wisdom 로드 실패 시 계속 진행
        
        # 6.5. 프로젝트 문서 자동 읽기 (README.md, PROJECT_CONTEXT.md)
        try:
            docs_read = []
            
            # README.md 읽기
            readme_path = os.path.join(project_path, 'README.md')
            if os.path.exists(readme_path):
                readme_size = os.path.getsize(readme_path)
                readme_content = helpers_obj.read_file(readme_path)
                smart_print(f"\n📄 README.md 읽기 완료 ({readme_size:,} bytes)")
                
                # 미리보기 (처음 5줄)
                preview_lines = readme_content.split('\n')[:5]
                smart_print("📋 README.md 미리보기:")
                for line in preview_lines:
                    smart_print(f"   {line}")
                if len(readme_content.split('\n')) > 5:
                    smart_print("   ...")
                docs_read.append('README.md')
            
            # PROJECT_CONTEXT.md 읽기
            context_path = os.path.join(project_path, 'PROJECT_CONTEXT.md')
            if os.path.exists(context_path):
                context_size = os.path.getsize(context_path)
                context_content = helpers_obj.read_file(context_path)
                smart_print(f"\n📄 PROJECT_CONTEXT.md 읽기 완료 ({context_size:,} bytes)")
                
                # 트리 구조 섹션 찾아서 미리보기
                lines_doc = context_content.split('\n')
                tree_section_found = False
                tree_preview = []
                
                for i, line in enumerate(lines_doc):
                    if "## 📂 디렉토리 트리 구조" in line or "## Project Structure" in line:
                        tree_section_found = True
                        tree_preview.append(line)
                    elif tree_section_found:
                        tree_preview.append(line)
                        if len(tree_preview) >= 15:  # 트리 구조 15줄만 미리보기
                            tree_preview.append("   ...")
                            break
                        if line.startswith("## "):  # 다음 섹션 시작
                            break
                
                if tree_preview:
                    smart_print("📋 디렉토리 트리 구조 미리보기:")
                    for line in tree_preview[:15]:
                        smart_print(f"   {line}")
                        
                docs_read.append('PROJECT_CONTEXT.md')
            
            if docs_read:
                smart_print(f"\n✅ 프로젝트 문서 {len(docs_read)}개 자동 로드 완료")
            
        except Exception as e:
            debug_log(f"⚠️ 문서 읽기 중 오류: {e}")
            # 오류가 발생해도 계속 진행


        # 7. 브리핑 생성 및 표시
        briefing = generate_complete_briefing(context, analysis_result)
        
        if verbose:
            smart_print(briefing)
        else:
            # 간결 모드 - 핵심 정보만
            smart_print(f"\n✅ 프로젝트: {clean_name}")
            smart_print(f"📁 경로: {project_path}")
            smart_print(f"📊 파일: {len(analysis_result.get('all_files', []))}개")
            smart_print(f"⚙️ 설정: {config_file.name if (config_file := project_path / '.ai-brain.config.json').exists() else '기본값'}")
        
        # 8. Wisdom 활성화
        smart_print("\n🧠 Wisdom 시스템 활성화")
        # activate_wisdom_system()  # TODO: 이 함수는 아직 구현되지 않음
        
        result['success'] = True
        
        # 성능 추적
        duration = time.time() - start_time
        smart_print(f"\n⏱️ 실행 시간: {duration:.2f}초")
        
    except Exception as e:
        result['error'] = str(e)
        smart_print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    return result
def flow_project_legacy(project_name: str) -> Dict[str, Any]:
    """[DEPRECATED] flow_project()를 사용하세요"""
    print("⚠️ flow_project_legacy는 deprecated되었습니다.")
    return flow_project(project_name, verbose=True)
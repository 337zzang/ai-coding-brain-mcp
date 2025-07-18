#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
🚀 JSON REPL Session for AI Coding Brain v6.0
==============================================

# 안전한 실행 헬퍼 (구문 검사 포함)
try:
    from safe_exec_helpers import enhanced_safe_exec, quick_syntax_check
    SAFE_EXEC_AVAILABLE = True
except ImportError:
    enhanced_safe_exec = None
    quick_syntax_check = None
    SAFE_EXEC_AVAILABLE = False


Claude Desktop과 통신하는 통합 JSON REPL 세션
- AI Helpers v2 완전 통합
- Workflow 시스템 통합
- 네임스페이스 보호 (AIHelpers 클래스)
- 최소 의존성, 핵심 기능만 유지

작성일: 2025-07-15
"""

import sys
import os

# Windows에서 UTF-8 출력 강제 설정
if sys.platform == 'win32':
    import locale
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import json
import io
import traceback
import time
import datetime as dt
import platform
import subprocess
import builtins
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager

# 기본 경로 설정


# Enhanced Safe Execution v2 - f-string 및 정규식 안전성 검사
try:
    from safe_execution_v2 import (
        safe_exec as safe_exec_v2,
        check_regex,
        benchmark_regex_safety
    )
    SAFE_EXEC_V2_AVAILABLE = True
except ImportError:
    SAFE_EXEC_V2_AVAILABLE = False
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# AI Helpers v2 통합
try:
    from ai_helpers_v2 import (
        # File operations
        read_file, write_file, create_file, file_exists, append_to_file,
        read_json, write_json,
        # Search operations
        search_code, search_files, grep, find_function, find_class,
        # Code operations
        parse_with_snippets, insert_block, replace_block,
        # Git operations
        git_status, git_add, git_commit, git_branch, git_push, git_pull,
        # Project operations
        get_current_project, scan_directory_dict, create_project_structure,
        # Core operations
        get_metrics, clear_cache, get_execution_history
    )
    AI_HELPERS_V2_LOADED = True
    print("✅ AI Helpers v2 로드 성공")
except ImportError as e:
    print(f"⚠️ AI Helpers v2 로드 실패: {e}")
    AI_HELPERS_V2_LOADED = False



# 실행 설정
CONFIG = {
    'use_safe_exec_v2': True,      # Enhanced Safe Execution v2 사용
    'fstring_check': True,         # f-string 미정의 변수 검사
    'regex_check': True,           # 정규식 안전성 검사
    'redos_protection': True,      # ReDoS 패턴 경고
    'show_warnings': True,         # 경고 메시지 표시
}

# ============================================================================
# 🌟 전역 변수 초기화
# ============================================================================
repl_globals = {}  # REPL 전역 네임스페이스
execution_count = 0  # 실행 카운터

class AIHelpersV2:
    """AI Helpers v2 통합 래퍼 - Workflow 시스템 포함"""
    
    def __init__(self):
        """AI Helpers v2 메서드들을 통합"""
        if not AI_HELPERS_V2_LOADED:
            print("⚠️ AI Helpers v2가 로드되지 않았습니다. 기능이 제한될 수 있습니다.")
            return
        
        # 영속적 히스토리 매니저 추가
        self._history_manager = None
            
        # File operations
        self.read_file = read_file
        self.write_file = write_file
        self.create_file = create_file
        self.file_exists = file_exists
        self.exists = file_exists  # 별칭
        self.append_to_file = append_to_file
        self.read_json = read_json
        self.write_json = write_json
        
        # Search operations
        self.search_code = search_code
        self.search_files = search_files
        self.search_in_files = search_code  # 별칭
        self.grep = grep
        self.find_function = find_function
        self.find_class = find_class
        
        # Code operations
        self.parse_with_snippets = parse_with_snippets
        self.insert_block = insert_block
        self.replace_block = replace_block
        
        # Git operations
        self.git_status = git_status
        self.git_add = git_add
        self.git_commit = git_commit
        self.git_branch = git_branch
        self.git_push = git_push
        self.git_pull = git_pull
        
        # Project operations
        self.get_current_project = get_current_project
        self.scan_directory_dict = scan_directory_dict
        self.create_project_structure = create_project_structure
        
        # Core operations
        self.get_metrics = get_metrics
        self.clear_cache = clear_cache
        self.get_execution_history = get_execution_history
        
        # flow_project 구현
        self.flow_project = self._flow_project
        self.cmd_flow_with_context = self._flow_project  # 별칭
        
        # Workflow 시스템 통합
        self.execute_workflow_command = self._execute_workflow_command
        self.get_workflow_status = self._get_workflow_status

        # workflow 메서드 별칭 추가
        def workflow(command=None, *args, **kwargs):
            if command:
                return self._execute_workflow_command(command, *args, **kwargs)
            else:
                return self._get_workflow_status()
        self.workflow = workflow
        self.update_file_directory = self._update_file_directory
        


        # LLM operations (llm_ops)
        try:
            from ai_helpers_v2.llm_ops import (
                ask_o3, analyze_code, explain_error, generate_docstring
            )
            self.ask_o3 = ask_o3
            self.analyze_code = analyze_code
            self.explain_error = explain_error
            self.generate_docstring = generate_docstring
        except ImportError:
            pass
        
        # Workflow 매니저 초기화
        self._workflow_manager = None
        
        # 히스토리 관련 메서드 추가
        self.add_history_action = self._add_history_action
        self.get_history = self._get_history
        self.continue_from_last = self._continue_from_last
        self.show_history = self._show_history
        
        # 프로젝트 관리 메서드 추가
        self.list_desktop_projects = self._list_desktop_projects
        self.get_project_info = self._get_project_info
        
    def _add_history_action(self, action, details=None, data=None):
        """히스토리에 액션 추가 (영속적 저장)"""
        if self._history_manager is None:
            self._init_history_manager()
        return self._history_manager.add_action(action, details, data)
    
    def _get_history(self, limit=None):
        """히스토리 조회"""
        if self._history_manager is None:
            self._init_history_manager()
        history = self._history_manager._load_history()
        if limit:
            return history[-limit:] if len(history) > limit else history
        return history
    
    def _continue_from_last(self):
        """마지막 작업에서 이어서 시작"""
        if self._history_manager is None:
            self._init_history_manager()
        return self._history_manager.continue_from_last()
    
    def _show_history(self, limit=10):
        """히스토리 표시"""
        if self._history_manager is None:
            self._init_history_manager()
        self._history_manager.show_history(limit)
    
    def _init_history_manager(self):
        """히스토리 매니저 초기화"""
        from persistent_history import PersistentHistoryManager
        self._history_manager = PersistentHistoryManager()
    
    def _list_desktop_projects(self):
        """바탕화면의 프로젝트 목록 조회"""
        from pathlib import Path
        desktop = Path.home() / "Desktop"
        projects = []
        
        for item in desktop.iterdir():
            if item.is_dir() and (item / "memory").exists():
                # 프로젝트 메타데이터 확인
                project_json = item / "memory" / "project.json"
                if project_json.exists():
                    try:
                        import json
                        with open(project_json, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            projects.append({
                                "name": item.name,
                                "path": str(item),
                                "created": metadata.get("created_at", "Unknown"),
                                "type": metadata.get("type", "unknown")
                            })
                    except:
                        # project.json이 없어도 memory 폴더가 있으면 프로젝트로 간주
                        projects.append({
                            "name": item.name,
                            "path": str(item),
                            "created": "Unknown",
                            "type": "legacy"
                        })
        
        return projects
    
    def _get_project_info(self, project_name=None):
        """프로젝트 정보 조회"""
        from pathlib import Path
        
        if project_name is None:
            # 현재 프로젝트 정보
            project_path = Path.cwd()
            project_name = project_path.name
        else:
            # 특정 프로젝트 정보
            project_path = Path.home() / "Desktop" / project_name
            if not project_path.exists():
                return None
        
        memory_path = project_path / "memory"
        if not memory_path.exists():
            return None
        
        # 메모리 사용량 계산
        total_size = 0
        file_count = 0
        for file in memory_path.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
                file_count += 1
        
        # 워크플로우 상태 확인
        workflow_file = memory_path / "workflow.json"
        has_active_workflow = False
        if workflow_file.exists():
            try:
                import json
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                    has_active_workflow = bool(workflow_data.get("active_plan_id"))
            except:
                pass
        
        return {
            "name": project_name,
            "path": str(project_path),
            "memory_files": file_count,
            "memory_size_kb": total_size / 1024,
            "has_workflow": workflow_file.exists(),
            "has_active_workflow": has_active_workflow,
            "has_history": (memory_path / "workflow_history.json").exists()
        }
        
    def _flow_project(self, project_name, desktop=True):
        """프로젝트 전환 및 컨텍스트 로드 (바탕화면 기반)"""
        import json
        from datetime import datetime
        from pathlib import Path
        
        try:
            # 바탕화면 또는 하위 프로젝트 경로 결정
            if desktop:
                # 바탕화면에 프로젝트 생성 (기본값)
                project_path = Path.home() / "Desktop" / project_name
            else:
                # 기존 방식 (하위 프로젝트)
                projects_dir = Path("projects")
                projects_dir.mkdir(exist_ok=True)
                project_path = projects_dir / project_name
            
            # 현재 프로젝트 백업 (프로젝트별 memory에 저장)
            if hasattr(self, 'get_current_project'):
                current = self.get_current_project()
                if current and current.get('name'):
                    current_memory = Path(current['path']) / "memory"
                    if current_memory.exists():
                        # 현재 워크플로우 백업
                        current_workflow = Path("memory/workflow.json")
                        if current_workflow.exists():
                            backup_path = current_memory / "workflow_backup.json"
                            import shutil
                            shutil.copy2(current_workflow, backup_path)
                            print(f"💾 워크플로우 백업: {backup_path}")
            
            # 프로젝트 디렉토리 생성
            is_new = not project_path.exists()
            if is_new:
                print(f"🆕 새 프로젝트 생성: {project_name}")
                project_path.mkdir(parents=True, exist_ok=True)
                
                # 기본 구조 생성
                (project_path / "src").mkdir(exist_ok=True)
                (project_path / "docs").mkdir(exist_ok=True)
                (project_path / "tests").mkdir(exist_ok=True)
                (project_path / "memory").mkdir(exist_ok=True)
                (project_path / "memory" / "checkpoints").mkdir(exist_ok=True)
                
                # README 생성
                readme_content = f"""# {project_name}

Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Location: {"Desktop" if desktop else "Subproject"}

## Structure
- `src/` - Source code
- `docs/` - Documentation  
- `tests/` - Test files
- `memory/` - Project memory and state
  - `workflow.json` - Current workflow
  - `workflow_history.json` - Action history
  - `checkpoints/` - State snapshots
"""
                (project_path / "README.md").write_text(readme_content, encoding='utf-8')
                
                # 프로젝트 메타데이터
                metadata = {
                    "project_name": project_name,
                    "created_at": datetime.now().isoformat(),
                    "path": str(project_path),
                    "type": "desktop" if desktop else "subproject"
                }
                
                (project_path / "memory" / "project.json").write_text(
                    json.dumps(metadata, indent=2), encoding='utf-8'
                )
            else:
                print(f"📂 기존 프로젝트로 전환: {project_name}")

                # 기존 프로젝트의 경우 project_context.json을 먼저 표시
                context_file = project_path / "memory" / "project_context.json"
                if context_file.exists():
                    try:
                        with open(context_file, 'r', encoding='utf-8') as f:
                            project_context = json.load(f)

                        print(f"\n📊 프로젝트 컨텍스트 정보:")
                        print(f"  - 분석일시: {project_context.get('analyzed_at', 'N/A')}")
                        print(f"  - 프로젝트 타입: {project_context.get('project_type', 'N/A')}")

                        tech_stack = project_context.get('tech_stack', [])
                        if tech_stack:
                            print(f"  - 기술 스택: {', '.join(tech_stack)}")

                        structure = project_context.get('structure', {})
                        if structure:
                            print(f"  - 전체 파일: {structure.get('total_files', 0)}개")
                            print(f"  - 소스 파일: {structure.get('source_files', 0)}개")
                            print(f"  - 테스트 파일: {structure.get('test_files', 0)}개")
                    except Exception as e:
                        print(f"  ⚠️ project_context.json 로드 오류: {e}")
            
            # 작업 디렉토리 변경
            os.chdir(str(project_path))
            
            # 프로젝트별 memory 디렉토리 확인
            memory_dir = Path("memory")
            memory_dir.mkdir(exist_ok=True)
            
            # 프로젝트별 워크플로우 로드
            project_workflow = memory_dir / "workflow.json"
            if project_workflow.exists():
                # 전역 memory 폴더로 복사 (호환성 유지)
                global_memory = Path("memory")
                if not global_memory.samefile(memory_dir):
                    global_memory.mkdir(exist_ok=True)
                    import shutil
                    shutil.copy2(project_workflow, global_memory / "workflow.json")
                print(f"✅ 프로젝트 워크플로우 로드")
            
            # 워크플로우/히스토리 매니저 재초기화
            self._workflow_manager = None
            self._history_manager = None
            
            # 분석 파일 확인 및 제안 (새 프로젝트일 때만)
            if is_new:
                analysis_files = {
                    "file_directory.md": project_path / "file_directory.md",
                    "project_context": project_path / "memory" / "project_context.json"
                }

                missing_files = []
                for name, filepath in analysis_files.items():
                    if not filepath.exists():
                        missing_files.append(name)

                if missing_files:
                    print(f"\n⚠️ 다음 분석 파일이 없습니다:")
                    for file in missing_files:
                        print(f"  - {file}")
                    print(f"\n💡 프로젝트 분석을 실행하시겠습니까?")
                    print(f"   👉 helpers.workflow('/a') 또는 /a 명령어를 실행하세요")
                    print(f"   - file_directory.md 생성/업데이트")
                    print(f"   - project_context.json 생성")
                    print(f"   - 프로젝트 구조 분석")
            
            # project_context.json 로드 및 표시 (새 프로젝트일 때만)
            if is_new and "project_context" in locals() and analysis_files["project_context"].exists():
                try:
                    with open(analysis_files["project_context"], 'r', encoding='utf-8') as f:
                        project_context = json.load(f)

                    print(f"\n📊 프로젝트 컨텍스트 정보:")
                    print(f"  - 분석일시: {project_context.get('analyzed_at', 'N/A')}")
                    print(f"  - 프로젝트 타입: {project_context.get('project_type', 'N/A')}")

                    tech_stack = project_context.get('tech_stack', [])
                    if tech_stack:
                        print(f"  - 기술 스택: {', '.join(tech_stack)}")

                    structure = project_context.get('structure', {})
                    if structure:
                        print(f"  - 전체 파일: {structure.get('total_files', 0)}개")
                        print(f"  - 소스 파일: {structure.get('source_files', 0)}개")
                        print(f"  - 테스트 파일: {structure.get('test_files', 0)}개")

                except Exception as e:
                    print(f"  ⚠️ project_context.json 로드 오류: {e}")

            # 프로젝트 문서 로드
            project_docs = self._load_project_docs(project_path)
            
            print(f"\n✅ 프로젝트 '{project_name}'로 전환 완료!")
            print(f"📁 경로: {project_path.absolute()}")
            print(f"💾 모든 데이터는 {project_path}/memory/에 저장됩니다")
            
            if project_docs['loaded']:
                print(f"📄 프로젝트 문서 로드됨: {', '.join(project_docs['files'])}")

            # 자동 프로젝트 정보 표시
            print("\n" + "="*60)
            print("📊 프로젝트 정보 자동 분석")
            print("="*60)

            # 1. 프로젝트 기본 정보
            try:
                if hasattr(self, 'pi'):
                    info = self.pi()
                    if info:
                        print("\n📋 프로젝트 상태:")
                        print(f"  - 메모리 파일: {info.get('memory_files', 0)}개")
                        print(f"  - 메모리 크기: {info.get('memory_size_kb', 0)/1024:.2f} MB")
                        print(f"  - 활성 워크플로우: {info.get('has_active_workflow', False)}")
            except:
                pass

            # 2. 워크플로우 상태 (간단히)
            try:
                if hasattr(self, '_workflow_manager') and self._workflow_manager:
                    from .workflow.improved_manager import WorkflowStatus
                    status = self._workflow_manager.get_status()
                    if status:
                        print(f"\n📊 워크플로우: {status.get('project_name', 'N/A')}")
                        print(f"  - 작업: {status.get('total_tasks', 0)}개 (완료: {status.get('completed_tasks', 0)}개)")
            except:
                pass

            # 3. 최근 히스토리 (간단히)
            try:
                if hasattr(self, '_history_manager') and self._history_manager:
                    history = self._history_manager.get_history(limit=3)
                    if history:
                        print("\n📜 최근 작업:")
                        for item in history[:3]:
                            print(f"  - {item.get('name', 'N/A')}")
            except:
                pass

            # 4. README 첫 줄
            try:
                readme_path = project_path / "README.md"
                if readme_path.exists():
                    readme = readme_path.read_text(encoding='utf-8')
                    first_line = readme.split('\n')[0].strip()
                    if first_line:
                        print(f"\n📄 {first_line}")
            except:
                pass

            print("\n🚀 프로젝트 준비 완료!")
            print("="*60)

            return {
                "success": True,
                "project_name": project_name,
                "path": str(project_path.absolute()),
                "is_new": is_new,
                "type": "desktop" if desktop else "subproject",
                "docs": project_docs
            }
            
        except Exception as e:
            print(f"❌ flow_project 오류: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def _load_project_docs(self, project_path: Path) -> dict:
        """프로젝트 문서(README.md, file_directory.md) 로드"""
        docs = {
            "loaded": False,
            "files": [],
            "readme": None,
            "file_directory": None,
            "parsed_tree": None,
            "project_context": None
        }
        
        try:
            # README.md 읽기
            readme_path = project_path / "README.md"
            if readme_path.exists():
                docs["readme"] = self.read_file(str(readme_path))
                docs["files"].append("README.md")
            
            # file_directory.md 읽기
            file_dir_path = project_path / "file_directory.md"
            if file_dir_path.exists():
                docs["file_directory"] = self.read_file(str(file_dir_path))
                docs["files"].append("file_directory.md")
                
                # 구조 파싱 시도
                try:
                    from workflow_helper import parse_file_directory_md
                    docs["parsed_tree"] = parse_file_directory_md(docs["file_directory"])
                except Exception as e:
                    print(f"⚠️ 파일 구조 파싱 실패: {e}")
            
            docs["loaded"] = len(docs["files"]) > 0
            
            # 전역 변수에 저장 (쉬운 접근을 위해)
            if docs["loaded"]:
                repl_globals["project_docs"] = docs
                
        except Exception as e:
            print(f"⚠️ 프로젝트 문서 로드 실패: {e}")
        
        return docs
    
    def _update_file_directory(self, project_path: str):
        """file_directory.md 업데이트"""
        from datetime import datetime
        
        content = [
            f"# File Directory - {os.path.basename(project_path)}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # scan_directory_dict 사용하여 재귀적 스캔
        def scan_recursive(path: str, level: int = 0):
            scan_result = self.scan_directory_dict(path)
            indent = "  " * level
            
            # 파일들
            for file in sorted(scan_result.get('files', [])):
                content.append(f"{indent}├── {file}")
            
            # 하위 디렉토리들
            dirs = sorted(scan_result.get('directories', []))
            for i, dir_name in enumerate(dirs):
                if not dir_name.startswith('.'):
                    is_last = (i == len(dirs) - 1)
                    prefix = "└──" if is_last else "├──"
                    content.append(f"{indent}{prefix} {dir_name}/")
                    subdir_path = os.path.join(path, dir_name)
                    scan_recursive(subdir_path, level + 1)
        
        scan_recursive(project_path)
        
        file_path = os.path.join(project_path, 'file_directory.md')
        self.create_file(file_path, "\n".join(content))
    
    def _backup_current_context(self):
        """현재 프로젝트 컨텍스트 백업"""
        try:
            current_project = self.get_current_project()
            if not current_project or not current_project.get('name'):
                return
            
            backup_data = {
                'project': current_project['name'],
                'timestamp': dt.datetime.now().isoformat(),
                'session_data': {
                    'execution_count': execution_count,
                    'variables': len(repl_globals)
                }
            }
            
            backup_dir = os.path.join(os.getcwd(), 'memory', 'backups')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            
            backup_file = os.path.join(backup_dir, f"backup_{current_project['name']}_{int(time.time())}.json")
            self.write_json(backup_file, backup_data)
            print(f"💾 프로젝트 백업 완료: {backup_file}")
        except Exception as e:
            print(f"⚠️ 백업 실패: {e}")
    
    def _execute_workflow_command(self, command: str):
        """워크플로우 명령 실행"""
        try:
            # dispatcher를 통해 명령 실행
            from workflow.dispatcher import execute_workflow_command as dispatch_command
            result_message = dispatch_command(command)
            
            # 성공/실패 판단
            if result_message.startswith("Error:"):
                return result_message
            else:
                # 히스토리에 기록
                if self._history_manager is None:
                    self._init_history_manager()
                
                # 워크플로우 명령을 히스토리에 추가
                action_data = {
                    "command": command,
                    "result": result_message
                }
                self._history_manager.add_action(
                    f"워크플로우 명령: {command.split()[0]}",
                    result_message,
                    action_data
                )
                
                return result_message
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_workflow_status(self):
        """워크플로우 상태 조회"""
        try:
            if self._workflow_manager is None:
                from workflow.improved_manager import ImprovedWorkflowManager
                project_name = self.get_current_project().get('name', 'default')
                self._workflow_manager = ImprovedWorkflowManager(project_name)
            
            return self._workflow_manager.get_status()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _not_implemented(self, *args, **kwargs):
        """구현되지 않은 메서드"""
        return None
    
    def __getattr__(self, name):
        """동적 속성 접근 - 호환성을 위해"""
        if AI_HELPERS_V2_LOADED:
            # v2 모듈에서 찾기
            for module in ['file_ops', 'search_ops', 'code_ops', 'git_ops', 'project_ops', 'llm_ops', 'core']:
                module_name = f'ai_helpers_v2.{module}'
                if module_name in sys.modules:
                    module_obj = sys.modules[module_name]
                    if hasattr(module_obj, name):
                        return getattr(module_obj, name)
        
        # 기본 동작
        def not_implemented(*args, **kwargs):
            print(f"⚠️ {name} 메서드는 아직 구현되지 않았습니다")
            return None
        return not_implemented
    
    def __dir__(self):
        """사용 가능한 메서드 목록"""
        base_attrs = list(self.__dict__.keys())
        if AI_HELPERS_V2_LOADED:
            # v2 모듈의 모든 공개 함수 추가
            for module in ['file_ops', 'search_ops', 'code_ops', 'git_ops', 'project_ops', 'core']:
                module_name = f'ai_helpers_v2.{module}'
                if module_name in sys.modules:
                    module_obj = sys.modules[module_name]
                    base_attrs.extend([
                        attr for attr in dir(module_obj) 
                        if not attr.startswith('_') and callable(getattr(module_obj, attr))
                    ])
        # Workflow 메서드 추가
        base_attrs.extend(['execute_workflow_command', 'get_workflow_status', 'update_file_directory'])
        return sorted(set(base_attrs))


def ensure_helpers_loaded():
    """AI Helpers v2를 안전하게 로드"""
    import sys
    import pathlib
    
    try:
        # 프로젝트 루트를 sys.path에 추가
        project_root = pathlib.Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # AI Helpers v2 사용
        if AI_HELPERS_V2_LOADED:
            helpers = AIHelpersV2()
            print("✅ AI Helpers v2 로드 완료!")
            return helpers
        else:
            print("⚠️ AI Helpers v2 로드 실패 - 기능이 제한될 수 있습니다")
            # 빈 helpers 객체 반환
            return AIHelpersV2()
    
    except Exception as e:
        print(f"❌ helpers 로딩 실패: {e}")
        import traceback
        traceback.print_exc()
        return None
    
def initialize_repl():
    """REPL 환경 초기화"""
    global repl_globals
    
    # 1. helpers 객체 생성
    helpers = ensure_helpers_loaded()
    if helpers:
        repl_globals['helpers'] = helpers
        repl_globals['h'] = helpers
        builtins.helpers = helpers
    else:
        sys.stderr.write('⚠️ helpers 로딩 실패\n')
    
    # 2. 핵심 기능들만 전역에 노출 (q_tools와 중복 제거)
    essential_funcs = {}
    
    # 워크플로우 관리 (최우선 - q_tools에 없음)
    if hasattr(helpers, 'execute_workflow_command'):
        essential_funcs['workflow'] = helpers.execute_workflow_command
        essential_funcs['wf'] = helpers.execute_workflow_command
    
    # 프로젝트 관리 (최우선 - q_tools에 없음)
    if hasattr(helpers, 'flow_project'):
        essential_funcs['flow_project'] = helpers.flow_project
        essential_funcs['fp'] = helpers.flow_project
    
    if hasattr(helpers, 'list_desktop_projects'):
        essential_funcs['list_projects'] = helpers.list_desktop_projects
        essential_funcs['lp'] = helpers.list_desktop_projects
    
    if hasattr(helpers, 'get_project_info'):
        essential_funcs['project_info'] = helpers.get_project_info
        essential_funcs['pi'] = helpers.get_project_info
    
    # 히스토리 관리 (최우선 - q_tools에 없음)
    if hasattr(helpers, 'add_history_action'):
        essential_funcs['add_history_action'] = helpers.add_history_action
        essential_funcs['add_history'] = helpers.add_history_action
        essential_funcs['show_history'] = helpers.show_history
        essential_funcs['continue_from_last'] = helpers.continue_from_last
        essential_funcs['get_history'] = helpers.get_history
    
    # Git 고급 기능 (q_tools에 없는 것들)
    if hasattr(helpers, 'git_add'):
        essential_funcs['git_add'] = helpers.git_add
    if hasattr(helpers, 'git_push'):
        essential_funcs['git_push'] = helpers.git_push
    if hasattr(helpers, 'git_pull'):
        essential_funcs['git_pull'] = helpers.git_pull
    
    # 고급 파일 관리 (q_tools에 없는 것들)
    if hasattr(helpers, 'scan_directory_dict'):
        essential_funcs['scan_directory_dict'] = helpers.scan_directory_dict
    if hasattr(helpers, 'get_file_info'):
        essential_funcs['get_file_info'] = helpers.get_file_info
    if hasattr(helpers, 'create_directory'):
        essential_funcs['create_directory'] = helpers.create_directory
    if hasattr(helpers, 'move_file'):
        essential_funcs['move_file'] = helpers.move_file
    if hasattr(helpers, 'insert_block'):
        essential_funcs['insert_block'] = helpers.insert_block
    
    # 전역에 추가
    for name, func in essential_funcs.items():
        if callable(func):
            repl_globals[name] = func
    
    print(f"✅ 핵심 helpers 기능 로드 완료: {len(essential_funcs)}개 (중복 제거)")
    
    # 3. 기본 모듈들
    import os
    import sys
    import json
    import time
    from pathlib import Path
    import datetime as dt
    import numpy as np
    import pandas as pd
    
    repl_globals.update({
        'os': os,
        'sys': sys,
        'json': json,
        'Path': Path,
        'datetime': dt,
        'np': np,
        'pd': pd,
        'time': time,
    })
    
    # 4. 프로젝트 자동 초기화 (현재 디렉토리)
    try:
        # 기본적으로 ai-coding-brain-mcp 프로젝트로 설정
        default_project = "ai-coding-brain-mcp"
        
        # OS 독립적인 Desktop 경로 찾기
        desktop_paths = [
            Path.home() / "Desktop",  # 영문 Windows/Mac/Linux
            Path.home() / "바탕화면",  # 한글 Windows
            Path.home() / "桌面",      # 중국어
            Path.home() / "デスクトップ"  # 일본어
        ]
        
        project_path = None
        for desktop in desktop_paths:
            if desktop.exists():
                test_path = desktop / default_project
                if test_path.exists():
                    project_path = test_path
                    os.chdir(str(project_path))
                    project_name = default_project
                    break
        
        # 프로젝트를 찾지 못한 경우 현재 디렉토리 사용
        if not project_path:
            project_path = Path.cwd()
            project_name = project_path.name
    except Exception as e:
        pass
    
    # 5. Git Version Manager (제거됨 - 파일이 존재하지 않음)
    # git_version_manager 모듈이 프로젝트에 없어 제거
    git_manager = None

    # 6. q_tools 자동 로드 (추가됨)
    try:
        import sys
        import os
        
        # q_tools 경로 추가
        current_dir = os.getcwd()
        python_path = os.path.join(current_dir, "python")
        if python_path not in sys.path:
            sys.path.insert(0, python_path)
        
        # q_tools 모든 함수 로드
        import q_tools
        q_functions = {}
        for name in dir(q_tools):
            if not name.startswith('_') and callable(getattr(q_tools, name)):
                q_functions[name] = getattr(q_tools, name)
        
        # repl_globals에 q_tools 함수들 추가
        repl_globals.update(q_functions)
        
        # builtins에도 추가 (글로벌 접근 가능)
        for name, func in q_functions.items():
            setattr(builtins, name, func)
        
        print(f"✅ q_tools 로드 완료! {len(q_functions)}개 함수 사용 가능")
        
    except Exception as e:
        pass
    
    # 7. AST 기반 코드 도구 자동 로드 (추가됨)
    try:
        # ai_helpers_v2 경로 추가
        ai_helpers_path = os.path.join(python_path, "ai_helpers_v2")
        if ai_helpers_path not in sys.path:
            sys.path.insert(0, ai_helpers_path)

        # 1. ez_code 개선된 함수들
        try:
            from ez_code import ez_parse, ez_replace, ez_view, ez_replace_safe
            repl_globals.update({
                'ez_parse': ez_parse,
                'ez_replace': ez_replace,
                'ez_view': ez_view,
                'ez_replace_safe': ez_replace_safe,
                # 짧은 별칭 추가
                'ezp': ez_parse,      # 파싱
                'ezr': ez_replace,    # 교체
                'ezv': ez_view,       # 보기
                'ezrs': ez_replace_safe  # 안전한 교체
            })
            print("  ✅ ez_code 함수 로드: ez_parse(ezp), ez_replace(ezr), ez_view(ezv), ez_replace_safe(ezrs)")
        except Exception as e:
            print(f"  ❌ ez_code 로드 실패: {e}")

        # 2. 개선된 AST 파서
        try:
            from improved_ast_parser import ez_parse_advanced, ez_parse_cached, ImprovedASTParser
            repl_globals.update({
                'ez_parse_advanced': ez_parse_advanced,
                'ez_parse_cached': ez_parse_cached,
                'ImprovedASTParser': ImprovedASTParser,
                # 짧은 별칭
                'ezpa': ez_parse_advanced,  # 고급 파싱
                'ezpc': ez_parse_cached     # 캐시된 파싱
            })
            print("  ✅ 개선된 AST 파서 로드: ez_parse_advanced(ezpa), ez_parse_cached(ezpc)")
        except Exception as e:
            print(f"  ❌ improved_ast_parser 로드 실패: {e}")

        # 3. 안전한 코드 수정 도구
        try:
            from safe_code_modifier import SafeCodeModifier
            repl_globals.update({
                'SafeCodeModifier': SafeCodeModifier
            })
            # 간편한 인스턴스 생성
            safe_modifier = SafeCodeModifier()
            repl_globals['safe_modifier'] = safe_modifier
            repl_globals['safe_replace'] = safe_modifier.safe_replace
            repl_globals['sr'] = safe_modifier.safe_replace  # 짧은 별칭
            print("  ✅ 안전한 코드 수정 도구 로드: SafeCodeModifier, safe_replace(sr)")
        except Exception as e:
            print(f"  ❌ safe_code_modifier 로드 실패: {e}")

        print("✅ AST 기반 코드 도구 로드 완료!")

        # 사용 가이드 출력
        print("""
📚 AST 코드 도구 사용법:
  • ezp('file.py') - 파일 구조 파싱
  • ezv('file.py', 'function_name') - 함수 코드 보기
  • ezr('file.py', 'function_name', new_code) - 함수 교체
  • ezrs('file.py', 'function_name', new_code) - 안전한 교체 (문법 검증)
  • ezpa('file.py', include_docstrings=True) - 고급 파싱
  • sr('file.py', 'function_name', new_code) - 안전한 교체 (별칭)
        """)

    except Exception as e:
        print(f"❌ AST 기반 코드 도구 로드 실패: {e}")

    except Exception as e:
        print(f"❌ AST 기반 코드 도구 로드 실패: {e}")



    # 7. AST 기반 코드 도구 자동 로드 (추가됨)
    try:
        # ai_helpers_v2 경로 추가
        ai_helpers_path = os.path.join(python_path, "ai_helpers_v2")
        if ai_helpers_path not in sys.path:
            sys.path.insert(0, ai_helpers_path)

        # 1. ez_code 개선된 함수들
        try:
            from ez_code import ez_parse, ez_replace, ez_view, ez_replace_safe
            repl_globals.update({
                'ez_parse': ez_parse,
                'ez_replace': ez_replace,
                'ez_view': ez_view,
                'ez_replace_safe': ez_replace_safe
            })
            print("  ✅ ez_code 함수 로드: ez_parse, ez_replace, ez_view, ez_replace_safe")
        except Exception as e:
            print(f"  ❌ ez_code 로드 실패: {e}")

        # 2. 개선된 AST 파서
        try:
            from improved_ast_parser import ez_parse_advanced, ez_parse_cached, ImprovedASTParser
            repl_globals.update({
                'ez_parse_advanced': ez_parse_advanced,
                'ez_parse_cached': ez_parse_cached,
                'ImprovedASTParser': ImprovedASTParser
            })
            print("  ✅ 개선된 AST 파서 로드: ez_parse_advanced, ez_parse_cached")
        except Exception as e:
            print(f"  ❌ improved_ast_parser 로드 실패: {e}")

        # 3. 안전한 코드 수정 도구
        try:
            from safe_code_modifier import SafeCodeModifier
            repl_globals.update({
                'SafeCodeModifier': SafeCodeModifier
            })
            # 간편한 인스턴스 생성
            safe_modifier = SafeCodeModifier()
            repl_globals['safe_modifier'] = safe_modifier
            repl_globals['safe_replace'] = safe_modifier.safe_replace
            print("  ✅ 안전한 코드 수정 도구 로드: SafeCodeModifier, safe_replace")
        except Exception as e:
            print(f"  ❌ safe_code_modifier 로드 실패: {e}")

        print("✅ AST 기반 코드 도구 로드 완료!")

    except Exception as e:
        print(f"❌ AST 기반 코드 도구 로드 실패: {e}")


        print(f"❌ q_tools 로드 실패: {e}")

# ============================================================================
# 💻 코드 실행
# ============================================================================

def safe_exec(code: str, globals_dict: dict) -> tuple[bool, str]:
    """
    안전한 코드 실행 - Enhanced v2 통합

    v2가 사용 가능하고 설정이 활성화되어 있으면 v2 사용,
    그렇지 않으면 기존 방식 사용
    """
    # Enhanced Safe Execution v2 사용 (가능한 경우)
    if SAFE_EXEC_V2_AVAILABLE and CONFIG.get('use_safe_exec_v2', True):
        try:
            success, output = safe_exec_v2(code, globals_dict)
            return success, output
        except Exception as e:
            # v2 실패 시 기존 방식으로 폴백
            print(f"⚠️ Safe Execution v2 오류, 기본 모드로 전환: {e}")

    # 기존 방식 (enhanced_safe_exec 또는 기본)
    try:
        return enhanced_safe_exec(code, globals_dict)
    except NameError:
        # enhanced_safe_exec가 import되지 않은 경우 계속 진행
        pass

    # 최종 폴백 - 기본 실행
    from textwrap import dedent

    try:
        # 들여쓰기 정리
        dedented_code = dedent(code).strip()

        # 컴파일 단계 (구문 검사)
        try:
            compiled_code = compile(dedented_code, '<json_repl>', 'exec')
        except SyntaxError as e:
            error_msg = f"❌ 구문 오류: {e.msg}"
            if e.lineno:
                error_msg += f" (라인 {e.lineno})"
            return False, error_msg

        # 실행
        exec(compiled_code, globals_dict)
        return True, ""

    except Exception as e:
        return False, f"❌ 런타임 오류: {type(e).__name__}: {str(e)}"
def execute_code(code: str) -> Dict[str, Any]:
    """Python 코드 실행"""
    global execution_count
    
    start_time = time.time()
    
    try:
        # safe_exec를 사용하여 코드 실행
        # safe_exec는 이미 stdout을 캡처하여 반환함
        success, output_or_error = safe_exec(code, repl_globals)
        
        if success:
            stdout_output = output_or_error
            stderr_output = ""
        else:
            stdout_output = ""
            stderr_output = output_or_error
            
        execution_count += 1
        
        # 자동 저장 (10회마다)
        if execution_count % 10 == 0 and 'save_context' in repl_globals:
            try:
                repl_globals['save_context']()
            except Exception:
                pass
        
        # 변수 개수 계산
        user_vars = [k for k in repl_globals.keys() 
                    if not k.startswith('_') and k not in ['__builtins__']]
        
        return {
            "success": True,
            "stdout": stdout_output,
            "stderr": stderr_output,
            "execution_time": time.time() - start_time,
            "variable_count": len(user_vars),
            "execution_count": execution_count,
            "session_mode": "JSON_REPL",
            "note": "JSON REPL Session - Variables persist between executions",
            "debug_info": {
                "repl_process_active": True,
                "repl_ready": True,
                "execution": "success"
            }
        }
        
    except Exception as e:
        execution_count += 1
        
        return {
            "success": False,
            "stdout": "",
            "stderr": f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
            "execution_time": time.time() - start_time,
            "variable_count": len(repl_globals),
            "execution_count": execution_count,
            "error": str(e),
            "error_type": type(e).__name__,
            "session_mode": "JSON_REPL",
            "debug_info": {
                "repl_process_active": True,
                "repl_ready": True,
                "execution": "error"
            }
        }

# ============================================================================
# 🔌 JSON 통신
# ============================================================================

def read_json_input() -> Optional[str]:
    """EOT 문자로 종료되는 JSON 입력 읽기"""
    try:
        input_data = ""
        while True:
            char = sys.stdin.read(1)
            if not char:  # EOF
                return None
            if char == '\x04':  # EOT
                break
            input_data += char
        
        return input_data.strip()
    except Exception:
        return None

def send_json_response(response: Dict[str, Any]):
    """JSON 응답 전송 (EOT 문자로 종료)"""
    try:
        response['timestamp'] = dt.datetime.now().isoformat()
        response_json = json.dumps(response, ensure_ascii=False)
        # 프로토콜 태그로 감싸서 안전하게 전송
        sys.stdout.write("__JSON_START__" + response_json + "__JSON_END__\x04")
        sys.stdout.flush()
    except Exception as e:
        error_response = {
            "success": False,
            "error": f"Response encoding error: {str(e)}",
            "error_type": "ResponseError"
        }
        sys.stdout.write("__JSON_START__" + json.dumps(error_response) + "__JSON_END__\x04")
        sys.stdout.flush()

# ============================================================================
# 🔄 메인 루프
# ============================================================================

def main():
    """메인 실행 루프"""
    global repl_globals
    
    # 필요한 모듈 import
    import sys
    import platform
    import subprocess
    import os
    
    # Windows UTF-8 설정
    if platform.system() == 'Windows':
        try:
            subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
        except subprocess.SubprocessError:
            pass
    
    # 스트림 인코딩 설정
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    else:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    else:
        import codecs
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')
    
    # 기본 작업 디렉토리 설정
    try:
        from pathlib import Path
        
        # OS 독립적인 Desktop 경로 찾기
        desktop_paths = [
            Path.home() / "Desktop",  # 영문 Windows/Mac/Linux
            Path.home() / "바탕화면",  # 한글 Windows
            Path.home() / "桌面",      # 중국어
            Path.home() / "デスクトップ"  # 일본어
        ]
        
        for desktop in desktop_paths:
            if desktop.exists():
                default_project_path = desktop / "ai-coding-brain-mcp"
                if default_project_path.exists():
                    os.chdir(str(default_project_path))
                    break
    except Exception:
        pass
    
    # 초기화
    initialize_repl()
    
    # ============================================================================
    # 🛡️ Safe Wrapper 자동 로드
    # ============================================================================
    try:
        # safe_wrapper 모듈 import
        import sys
        import os
        
        # 프로젝트 루트의 python 디렉토리를 경로에 추가  
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        python_dir = os.path.join(project_root, 'python')
        if python_dir not in sys.path:
            sys.path.insert(0, python_dir)
        
        from safe_wrapper import register_safe_helpers
        
        # helpers가 repl_globals에 있는지 확인
        if 'helpers' in repl_globals:
            # 안전한 헬퍼 함수들을 전역에 등록
            register_safe_helpers(repl_globals['helpers'], repl_globals)
            print("✅ Safe Helper 함수 로드 완료", file=sys.stderr)
        else:
            print("⚠️ helpers를 찾을 수 없어 Safe Helper 로드 건너뜀", file=sys.stderr)
            
    except Exception as e:
        print(f"❌ Safe Helper 로드 실패: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    
    # 이전 세션 정보 표시
    try:
        from persistent_history import PersistentHistoryManager
        history_manager = PersistentHistoryManager()
        sync_data = history_manager.get_workflow_sync_data()
        
        if sync_data['total_actions'] > 0:
            print("\n📊 이전 세션 정보:")
            print(f"   총 작업: {sync_data['total_actions']}개")
            print(f"   대화 수: {sync_data['conversations']}개")
            if sync_data['last_action']:
                print(f"   마지막 작업: {sync_data['last_action']['action']} ({sync_data['last_action']['timestamp']})")
            print("\n💡 continue_from_last()로 이전 작업을 이어갈 수 있습니다.")
    except Exception:
        pass
    
    # 준비 완료 신호
    print("__READY__", flush=True)
    
    # 메인 루프
    try:
        while True:
            # JSON 입력 읽기
            code_input = read_json_input()
            if code_input is None:
                break
            
            try:
                # 요청 파싱
                request = json.loads(code_input)
                request_id = request.get('id')
                code = request.get('code', '')
                language = request.get('language', 'python')
                
                if language != 'python':
                    response = {
                        "success": False,
                        "error": f"Unsupported language: {language}",
                        "error_type": "LanguageError"
                    }
                else:
                    # 코드 실행
                    response = execute_code(code)
                    response['language'] = language
                
                # 요청 ID 유지
                if request_id:
                    response['id'] = request_id
                    
            except json.JSONDecodeError as e:
                response = {
                    "success": False,
                    "error": f"Invalid JSON: {str(e)}",
                    "error_type": "JSONDecodeError"
                }
            
            # 응답 전송
            send_json_response(response)
    
    except KeyboardInterrupt:
        print("\n👋 JSON REPL Session 종료", file=sys.stderr)
    except Exception as e:
        print(f"\n❌ 치명적 오류: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    finally:
        # 종료 시 컨텍스트 저장
        try:
            if 'save_context' in repl_globals:
                repl_globals['save_context']()
                print("✅ 최종 컨텍스트 저장", file=sys.stderr)
        except Exception:
            pass


# ============================================================================
# 실행
# ============================================================================

if __name__ == "__main__":
    main()
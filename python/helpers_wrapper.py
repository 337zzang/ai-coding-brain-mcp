"""
Helpers 래퍼 - 일관된 반환값 구조를 제공하는 래퍼 클래스
"""
import os
import sys
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from functools import wraps
from contextlib import contextmanager

# HelperResult import
from helper_result import HelperResult


def safe_helper(func):
    """모든 헬퍼 메서드의 반환값을 HelperResult로 통일하는 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # 이미 HelperResult인 경우 그대로 반환
            if isinstance(result, HelperResult):
                return result
            # dict이고 success 키가 있는 경우
            elif isinstance(result, dict) and "success" in result:
                return HelperResult(
                    ok=result.get("success", False),
                    data=result.get("data"),
                    error=result.get("error")
                )
            # 그 외의 경우 성공으로 간주
            else:
                return HelperResult.success(result)
        except Exception as e:
            return HelperResult.failure(str(e))
    return wrapper


class HelpersWrapper:
    """AIHelpers의 메서드들을 래핑하여 일관된 반환값 구조를 제공"""
    
    def __init__(self, helpers):
        self.helpers = helpers
        self._original = helpers  # 원본 접근용
    
    @safe_helper
    def scan_directory_dict(self, path: str) -> HelperResult:
        """디렉토리 스캔"""
        if hasattr(self.helpers, 'scan_directory_dict'):
            return self.helpers.scan_directory_dict(path)
        # Fallback 구현
        return HelperResult.failure("scan_directory_dict not implemented")
    
    @safe_helper
    def read_file(self, path: str, parse_json: bool = False) -> HelperResult:
        """파일 읽기 - parse_json 옵션 지원"""
        try:
            # 기본 파일 읽기
            if hasattr(self.helpers, 'read_file'):
                result = self.helpers.read_file(path)
                
                # 이미 HelperResult인 경우 처리
                if isinstance(result, HelperResult):
                    if result.ok and parse_json and result.data:
                        try:
                            parsed = json.loads(result.data)
                            return HelperResult.success(parsed)
                        except json.JSONDecodeError as e:
                            return HelperResult.failure(f"JSON 파싱 오류: {e}")
                    return result
                
                # dict 형태의 결과 처리
                if isinstance(result, dict) and result.get('success'):
                    content = result.get('data', '')
                    
                    # parse_json이 True면 JSON 파싱 시도
                    if parse_json and content:
                        try:
                            parsed = json.loads(content)
                            return HelperResult.success(parsed)
                        except json.JSONDecodeError as e:
                            return HelperResult.failure(f"JSON 파싱 오류: {e}")
                    
                    return HelperResult.success(content)
                elif isinstance(result, dict):
                    return HelperResult.failure(result.get('error', 'Unknown error'))
                else:
                    return HelperResult.success(result)
            else:
                # Fallback 구현
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if parse_json:
                        return HelperResult.success(json.loads(content))
                    return HelperResult.success(content)
        except Exception as e:
            return HelperResult.failure(str(e))
    
    @safe_helper
    def create_file(self, path: str, content: str) -> HelperResult:
        """파일 생성/수정"""
        if hasattr(self.helpers, 'create_file'):
            return self.helpers.create_file(path, content)
        return HelperResult.failure("create_file not implemented")
    
    @safe_helper
    def replace_block(self, file_path: str, old_code: str, new_code: str) -> HelperResult:
        """코드 블록 교체"""
        if hasattr(self.helpers, 'replace_block'):
            return self.helpers.replace_block(file_path, old_code, new_code)
        return HelperResult.failure("replace_block not implemented")
    
    @safe_helper
    def search_files_advanced(self, path: str, pattern: str) -> HelperResult:
        """파일 검색"""
        if hasattr(self.helpers, 'search_files_advanced'):
            return self.helpers.search_files_advanced(path, pattern)
        return HelperResult.failure("search_files_advanced not implemented")
    
    @safe_helper
    def search_code_content(self, path: str, pattern: str, file_pattern: str = None,
                          max_results: int = 100, case_sensitive: bool = False,
                          whole_word: bool = False) -> HelperResult:
        """코드 내용 검색"""
        if hasattr(self.helpers, 'search_code_content'):
            return self.helpers.search_code_content(
                path, pattern, file_pattern,
                max_results=max_results,
                case_sensitive=case_sensitive,
                whole_word=whole_word
            )
        return HelperResult.failure("search_code_content not implemented")
    
    @safe_helper
    def git_status(self) -> HelperResult:
        """Git 상태 확인"""
        if hasattr(self.helpers, 'git_status'):
            return self.helpers.git_status()
        return HelperResult.failure("git_status not implemented")
    
    @safe_helper
    def get_context(self) -> HelperResult:
        """컨텍스트 가져오기"""
        if hasattr(self.helpers, 'get_context'):
            result = self.helpers.get_context()
            return result
        
        # Fallback 구현 - memory/context.json 직접 읽기
        try:
            # 프로젝트 루트 확인
            if hasattr(self.helpers, 'get_project_root'):
                root_result = self.helpers.get_project_root()
                # get_project_root는 문자열을 반환할 수 있음
                if isinstance(root_result, str):
                    project_root = root_result
                elif isinstance(root_result, HelperResult) and root_result.ok:
                    project_root = root_result.data
                elif isinstance(root_result, dict) and root_result.get('success'):
                    project_root = root_result.get('data')
                else:
                    project_root = os.getcwd()
            else:
                project_root = os.getcwd()
            
            context_path = Path(project_root) / "memory" / "context.json"
            if context_path.exists():
                with open(context_path, 'r', encoding='utf-8') as f:
                    return HelperResult.success(json.load(f))
            else:
                # 빈 컨텍스트 반환
                return HelperResult.success({})
        except Exception as e:
            return HelperResult.failure(f"컨텍스트 로드 오류: {str(e)}")
    
    @safe_helper
    def save_context(self, context: dict) -> HelperResult:
        """컨텍스트 저장"""
        if hasattr(self.helpers, 'save_context'):
            return self.helpers.save_context(context)
        
        # Fallback 구현 - memory/context.json에 직접 저장
        try:
            # 프로젝트 루트 확인
            if hasattr(self.helpers, 'get_project_root'):
                root_result = self.helpers.get_project_root()
                # get_project_root는 문자열을 반환할 수 있음
                if isinstance(root_result, str):
                    project_root = root_result
                elif isinstance(root_result, HelperResult) and root_result.ok:
                    project_root = root_result.data
                elif isinstance(root_result, dict) and root_result.get('success'):
                    project_root = root_result.get('data')
                else:
                    project_root = os.getcwd()
            else:
                project_root = os.getcwd()
            
            # memory 디렉토리 생성
            memory_dir = Path(project_root) / "memory"
            memory_dir.mkdir(exist_ok=True)
            
            # context.json 저장
            context_path = memory_dir / "context.json"
            with open(context_path, 'w', encoding='utf-8') as f:
                json.dump(context, f, ensure_ascii=False, indent=2)
            
            return HelperResult.success({"message": "컨텍스트 저장 완료"})
        except Exception as e:
            return HelperResult.failure(f"컨텍스트 저장 오류: {str(e)}")
    
    @contextmanager
    def context_manager(self):
        """컨텍스트 자동 로드/저장 매니저"""
        # 컨텍스트 로드
        result = self.get_context()
        if result.ok:
            ctx = result.data or {}
        else:
            ctx = {}
        
        try:
            yield ctx
        finally:
            # 컨텍스트 저장
            self.save_context(ctx)
    
    @safe_helper
    def workflow(self, command: str) -> HelperResult:
        """워크플로우 명령 실행"""
        if hasattr(self.helpers, 'workflow'):
            result = self.helpers.workflow(command)
            # workflow가 JSON 문자열을 반환하는 경우 파싱
            if isinstance(result, str):
                try:
                    # JSON 문자열인지 확인
                    if result.strip().startswith('{'):
                        parsed = json.loads(result)
                        return HelperResult.success(parsed)
                except:
                    pass
                # JSON이 아니면 문자열 그대로 반환
                return HelperResult.success(result)
            return result
        # 직접 구현 시도
        try:
            from workflow_commands import handle_workflow_command
            return handle_workflow_command(command)
        except ImportError:
            return HelperResult.failure("workflow not implemented")
    
    @safe_helper
    def cmd_flow_with_context(self, project_name: str) -> HelperResult:
        """프로젝트 컨텍스트 전환"""
        if hasattr(self.helpers, 'cmd_flow_with_context'):
            return self.helpers.cmd_flow_with_context(project_name)
        return HelperResult.failure("cmd_flow_with_context not implemented")
    
    @safe_helper
    def parse_with_snippets(self, file_path: str) -> HelperResult:
        """파일 파싱 (AST 기반)"""
        if hasattr(self.helpers, 'parse_with_snippets'):
            return self.helpers.parse_with_snippets(file_path)
        # 간단한 구현
        try:
            result = self.read_file(file_path)
            if result.ok:
                return HelperResult.success({"content": result.data, "snippets": []})
            return result
        except Exception as e:
            return HelperResult.failure(str(e))
    
    @safe_helper
    def compile_project(self, project_root: Optional[str] = None) -> HelperResult:
        """프로젝트 전체 Python 파일 구문 검사"""
        if hasattr(self.helpers, 'compile_project'):
            return self.helpers.compile_project(project_root)
        return HelperResult.failure("compile_project not implemented")
    
    @safe_helper
    def check_syntax(self) -> HelperResult:
        """프로젝트 구문 검사 (compile_project 별칭)"""
        return self.compile_project()
    
    @safe_helper
    def get_project_root(self) -> HelperResult:
        """프로젝트 루트 경로 가져오기"""
        if hasattr(self.helpers, 'get_project_root'):
            result = self.helpers.get_project_root()
            # 문자열인 경우 그대로 성공으로 반환
            if isinstance(result, str):
                return HelperResult.success(result)
            # 이미 HelperResult인 경우
            elif isinstance(result, HelperResult):
                return result
            # dict 형태인 경우
            elif isinstance(result, dict) and 'data' in result:
                return HelperResult.success(result['data'])
            else:
                return HelperResult.success(result)
        return HelperResult.success(os.getcwd())
    
    def __getattr__(self, name):
        """정의되지 않은 메서드는 원본 helpers로 전달"""
        if hasattr(self.helpers, name):
            attr = getattr(self.helpers, name)
            if callable(attr):
                # 메서드인 경우 safe_helper로 감싸서 반환
                return safe_helper(attr)
            return attr
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

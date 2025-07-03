"""프로젝트 전체 Python 파일 구문 검사 도구"""
import os
import py_compile
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from ..utils.io_helpers import safe_print
from ..helper_result import HelperResult


class ProjectCompiler:
    """프로젝트 전체 Python 파일을 컴파일하여 구문 오류를 검사"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.exclude_dirs = {
            '__pycache__', '.git', 'venv', '.venv', 
            'node_modules', 'dist', 'build', '.pytest_cache'
        }
        
    def find_python_files(self) -> List[Path]:
        """프로젝트의 모든 Python 파일 찾기"""
        python_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # 제외할 디렉토리 필터링
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
                    
        return python_files    
    def compile_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """단일 파일 컴파일 및 구문 검사
        
        Returns:
            (성공 여부, 오류 메시지)
        """
        try:
            py_compile.compile(
                str(file_path), 
                doraise=True,
                quiet=True
            )
            return True, None
        except py_compile.PyCompileError as e:
            # 구문 오류 상세 정보 추출
            error_msg = str(e)
            if hasattr(e, 'exc_value'):
                error_msg = str(e.exc_value)
            return False, error_msg
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"    
    def compile_project(self) -> Dict:
        """프로젝트 전체 컴파일 실행"""
        results = {
            'total_files': 0,
            'success': 0,
            'failed': 0,
            'errors': [],
            'summary': ''
        }
        
        python_files = self.find_python_files()
        results['total_files'] = len(python_files)
        
        safe_print(f"🔍 {len(python_files)}개의 Python 파일 검사 중...")
        
        for file_path in python_files:
            relative_path = file_path.relative_to(self.project_root)
            success, error = self.compile_file(file_path)
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'file': str(relative_path),
                    'error': error
                })
                
        # 요약 생성
        if results['failed'] == 0:
            results['summary'] = f"✅ 모든 파일 ({results['total_files']}개) 구문 검사 통과!"
        else:
            results['summary'] = (
                f"⚠️ {results['failed']}개 파일에서 구문 오류 발견\n"
                f"✅ {results['success']}개 파일 정상"
            )
            
        return results

def compile_project(project_root: Optional[str] = None) -> HelperResult:
    """프로젝트 전체 Python 파일 구문 검사 (헬퍼 함수)"""
    try:
        compiler = ProjectCompiler(project_root)
        results = compiler.compile_project()
        
        # 에러가 있는 경우 상세 정보 출력
        if results['errors']:
            safe_print("\n📋 구문 오류 상세:")
            for error_info in results['errors'][:10]:  # 처음 10개만 표시
                safe_print(f"\n❌ {error_info['file']}")
                safe_print(f"   {error_info['error']}")
                
            if len(results['errors']) > 10:
                safe_print(f"\n... 외 {len(results['errors']) - 10}개 오류")
        
        safe_print(f"\n{results['summary']}")
        
        return HelperResult(
            ok=results['failed'] == 0,
            data=results,
            error=None if results['failed'] == 0 else f"{results['failed']} files with syntax errors"
        )
        
    except Exception as e:
        return HelperResult(
            ok=False,
            data=None,
            error=f"Compilation check failed: {str(e)}"
        )


# 빠른 접근을 위한 별칭
def check_syntax() -> HelperResult:
    """compile_project의 별칭"""
    return compile_project()

"""
Jupyter Notebook 연동 헬퍼 함수
Jupyter 노트북 관리, 실행, 변환 등을 지원
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from .util import ok, err, resolve_project_path

def create_notebook(path: Union[str, Path], cells: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    새로운 Jupyter 노트북 생성
    
    Args:
        path: 노트북 파일 경로 (.ipynb)
        cells: 초기 셀 목록 (선택사항)
    
    Returns:
        Dict[str, Any]: 작업 결과
    """
    try:
        notebook_path = resolve_project_path(path)
        
        # 기본 노트북 구조
        notebook = {
            "cells": cells or [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# 새 노트북\n", "AI Coding Brain MCP로 생성됨"]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["# 코드를 여기에 작성하세요\n", "import ai_helpers_new as h"]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.8.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5
        }
        
        # 노트북 저장
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)
        
        return ok({
            'path': str(notebook_path),
            'cells': len(notebook['cells']),
            'message': f"노트북 생성: {notebook_path.name}"
        })
    except Exception as e:
        return err(f"노트북 생성 실패: {e}")

def read_notebook(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Jupyter 노트북 읽기
    
    Args:
        path: 노트북 파일 경로
    
    Returns:
        Dict[str, Any]: 노트북 내용
    """
    try:
        notebook_path = resolve_project_path(path)
        
        if not notebook_path.exists():
            return err(f"노트북 없음: {notebook_path}")
        
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        return ok({
            'path': str(notebook_path),
            'cells': notebook.get('cells', []),
            'metadata': notebook.get('metadata', {}),
            'nbformat': notebook.get('nbformat', 4),
            'cell_count': len(notebook.get('cells', []))
        })
    except Exception as e:
        return err(f"노트북 읽기 실패: {e}")

def add_cell(path: Union[str, Path], cell_type: str = "code", 
             content: Union[str, List[str]] = "", position: int = -1) -> Dict[str, Any]:
    """
    노트북에 셀 추가
    
    Args:
        path: 노트북 파일 경로
        cell_type: 'code' 또는 'markdown'
        content: 셀 내용
        position: 삽입 위치 (-1이면 끝에 추가)
    
    Returns:
        Dict[str, Any]: 작업 결과
    """
    try:
        # 노트북 읽기
        result = read_notebook(path)
        if not result['ok']:
            return result
        
        notebook_path = resolve_project_path(path)
        
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # 셀 생성
        if isinstance(content, str):
            content = content.split('\n')
        
        # 각 줄 끝에 개행 문자 추가 (Jupyter 형식)
        content = [line + '\n' if not line.endswith('\n') else line for line in content]
        
        new_cell = {
            "cell_type": cell_type,
            "metadata": {},
            "source": content
        }
        
        if cell_type == "code":
            new_cell["execution_count"] = None
            new_cell["outputs"] = []
        
        # 셀 삽입
        cells = notebook.get('cells', [])
        if position == -1:
            cells.append(new_cell)
        else:
            cells.insert(position, new_cell)
        
        notebook['cells'] = cells
        
        # 저장
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)
        
        return ok({
            'path': str(notebook_path),
            'cell_count': len(cells),
            'added_at': position if position != -1 else len(cells) - 1,
            'cell_type': cell_type
        })
    except Exception as e:
        return err(f"셀 추가 실패: {e}")

def execute_notebook(path: Union[str, Path], timeout: int = 600) -> Dict[str, Any]:
    """
    Jupyter 노트북 실행 (nbconvert 사용)
    
    Args:
        path: 노트북 파일 경로
        timeout: 실행 제한 시간 (초)
    
    Returns:
        Dict[str, Any]: 실행 결과
    """
    try:
        notebook_path = resolve_project_path(path)
        
        if not notebook_path.exists():
            return err(f"노트북 없음: {notebook_path}")
        
        # nbconvert로 실행
        cmd = [
            'jupyter', 'nbconvert',
            '--to', 'notebook',
            '--execute',
            '--inplace',
            '--ExecutePreprocessor.timeout=' + str(timeout),
            str(notebook_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return err(f"실행 실패: {result.stderr}")
        
        return ok({
            'path': str(notebook_path),
            'message': '노트북 실행 완료',
            'stdout': result.stdout,
            'execution_time': f"최대 {timeout}초"
        })
    except subprocess.CalledProcessError as e:
        return err(f"실행 오류: {e}")
    except FileNotFoundError:
        return err("jupyter가 설치되지 않음. 'pip install jupyter' 실행 필요")
    except Exception as e:
        return err(f"노트북 실행 실패: {e}")

def convert_to_python(path: Union[str, Path], output: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Jupyter 노트북을 Python 스크립트로 변환
    
    Args:
        path: 노트북 파일 경로
        output: 출력 파일 경로 (선택사항)
    
    Returns:
        Dict[str, Any]: 변환 결과
    """
    try:
        notebook_path = resolve_project_path(path)
        
        if not notebook_path.exists():
            return err(f"노트북 없음: {notebook_path}")
        
        # 출력 경로 설정
        if output:
            output_path = resolve_project_path(output)
        else:
            output_path = notebook_path.with_suffix('.py')
        
        # nbconvert로 변환
        cmd = [
            'jupyter', 'nbconvert',
            '--to', 'python',
            '--output', str(output_path.stem),
            '--output-dir', str(output_path.parent),
            str(notebook_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return err(f"변환 실패: {result.stderr}")
        
        return ok({
            'input': str(notebook_path),
            'output': str(output_path),
            'message': f"Python 스크립트로 변환: {output_path.name}"
        })
    except FileNotFoundError:
        return err("jupyter가 설치되지 않음. 'pip install jupyter' 실행 필요")
    except Exception as e:
        return err(f"변환 실패: {e}")

def start_notebook_server(port: int = 8888, directory: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Jupyter 노트북 서버 시작
    
    Args:
        port: 서버 포트 (기본: 8888)
        directory: 작업 디렉토리 (선택사항)
    
    Returns:
        Dict[str, Any]: 서버 정보
    """
    try:
        # 작업 디렉토리 설정
        if directory:
            work_dir = resolve_project_path(directory)
        else:
            work_dir = Path.cwd()
        
        # 서버 시작 명령
        cmd = [
            'jupyter', 'notebook',
            '--port', str(port),
            '--no-browser',
            '--notebook-dir', str(work_dir)
        ]
        
        # 백그라운드로 실행
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        return ok({
            'url': f"http://localhost:{port}",
            'port': port,
            'directory': str(work_dir),
            'pid': process.pid,
            'message': f"Jupyter 서버 시작됨: http://localhost:{port}"
        })
    except FileNotFoundError:
        return err("jupyter가 설치되지 않음. 'pip install jupyter' 실행 필요")
    except Exception as e:
        return err(f"서버 시작 실패: {e}")

def list_kernels() -> Dict[str, Any]:
    """
    사용 가능한 Jupyter 커널 목록
    
    Returns:
        Dict[str, Any]: 커널 목록
    """
    try:
        cmd = ['jupyter', 'kernelspec', 'list', '--json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return err(f"커널 목록 조회 실패: {result.stderr}")
        
        kernels = json.loads(result.stdout)
        
        return ok({
            'kernels': kernels.get('kernelspecs', {}),
            'count': len(kernels.get('kernelspecs', {})),
            'default': 'python3'
        })
    except FileNotFoundError:
        return err("jupyter가 설치되지 않음. 'pip install jupyter' 실행 필요")
    except Exception as e:
        return err(f"커널 목록 조회 실패: {e}")

def install_kernel(name: str = "ai_brain", display_name: str = "AI Brain Python") -> Dict[str, Any]:
    """
    현재 Python 환경을 Jupyter 커널로 설치
    
    Args:
        name: 커널 이름
        display_name: 표시 이름
    
    Returns:
        Dict[str, Any]: 설치 결과
    """
    try:
        # ipykernel 설치 확인
        cmd_check = ['python', '-m', 'pip', 'show', 'ipykernel']
        result = subprocess.run(cmd_check, capture_output=True, text=True)
        
        if result.returncode != 0:
            # ipykernel 설치
            cmd_install = ['python', '-m', 'pip', 'install', 'ipykernel']
            subprocess.run(cmd_install, check=True)
        
        # 커널 설치
        cmd = [
            'python', '-m', 'ipykernel', 'install',
            '--user',
            '--name', name,
            '--display-name', display_name
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return err(f"커널 설치 실패: {result.stderr}")
        
        return ok({
            'kernel_name': name,
            'display_name': display_name,
            'message': f"커널 설치 완료: {display_name}"
        })
    except Exception as e:
        return err(f"커널 설치 실패: {e}")

# 노트북 셀 관련 유틸리티
def extract_code_cells(path: Union[str, Path]) -> Dict[str, Any]:
    """
    노트북에서 코드 셀만 추출
    
    Args:
        path: 노트북 파일 경로
    
    Returns:
        Dict[str, Any]: 코드 셀 목록
    """
    try:
        result = read_notebook(path)
        if not result['ok']:
            return result
        
        cells = result['data']['cells']
        code_cells = [cell for cell in cells if cell.get('cell_type') == 'code']
        
        # 코드 텍스트 추출
        codes = []
        for i, cell in enumerate(code_cells):
            source = ''.join(cell.get('source', []))
            codes.append({
                'index': i,
                'code': source,
                'outputs': cell.get('outputs', [])
            })
        
        return ok({
            'path': str(path),
            'code_cells': codes,
            'count': len(codes)
        })
    except Exception as e:
        return err(f"코드 셀 추출 실패: {e}")

def clear_outputs(path: Union[str, Path]) -> Dict[str, Any]:
    """
    노트북의 모든 출력 지우기
    
    Args:
        path: 노트북 파일 경로
    
    Returns:
        Dict[str, Any]: 작업 결과
    """
    try:
        notebook_path = resolve_project_path(path)
        
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # 모든 코드 셀의 출력 지우기
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'code':
                cell['outputs'] = []
                cell['execution_count'] = None
        
        # 저장
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)
        
        return ok({
            'path': str(notebook_path),
            'message': '모든 출력 지움'
        })
    except Exception as e:
        return err(f"출력 지우기 실패: {e}")
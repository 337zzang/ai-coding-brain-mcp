"""
UV 패키지 매니저 헬퍼 함수
초고속 Python 패키지 관리를 위한 UV 도구 지원
"""

import os
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from .util import ok, err, resolve_project_path

def install_uv() -> Dict[str, Any]:
    """
    UV 패키지 매니저 설치
    
    Returns:
        Dict[str, Any]: 설치 결과
    """
    try:
        # UV 설치 확인
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            return ok({
                'installed': True,
                'version': version,
                'message': f"UV 이미 설치됨: {version}"
            })
        
        # OS별 설치 명령
        system = platform.system().lower()
        
        if system == "windows":
            # Windows: PowerShell 사용
            cmd = ['powershell', '-Command', 
                   'irm https://astral.sh/uv/install.ps1 | iex']
        else:
            # Unix/Linux/Mac: curl 사용
            cmd = ['sh', '-c', 
                   'curl -LsSf https://astral.sh/uv/install.sh | sh']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # pip fallback
            pip_cmd = ['pip', 'install', 'uv']
            pip_result = subprocess.run(pip_cmd, capture_output=True, text=True)
            
            if pip_result.returncode != 0:
                return err(f"UV 설치 실패: {pip_result.stderr}")
        
        # 설치 확인
        verify = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if verify.returncode == 0:
            return ok({
                'installed': True,
                'version': verify.stdout.strip(),
                'message': "UV 설치 완료"
            })
        else:
            return err("UV 설치 실패")
            
    except Exception as e:
        return err(f"UV 설치 오류: {e}")

def init_project(name: Optional[str] = None, python_version: str = "3.11") -> Dict[str, Any]:
    """
    UV로 새 Python 프로젝트 초기화
    
    Args:
        name: 프로젝트 이름 (선택사항)
        python_version: Python 버전
    
    Returns:
        Dict[str, Any]: 초기화 결과
    """
    try:
        # pyproject.toml 생성
        project_name = name or Path.cwd().name
        
        pyproject_content = f"""[project]
name = "{project_name}"
version = "0.1.0"
description = "AI Coding Brain MCP 프로젝트"
readme = "README.md"
requires-python = ">={python_version}"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "ipykernel>=6.0.0",
    "jupyter>=1.0.0",
]
"""
        
        # pyproject.toml 저장
        pyproject_path = Path.cwd() / "pyproject.toml"
        
        # 기존 파일 백업
        if pyproject_path.exists():
            backup_path = pyproject_path.with_suffix('.toml.backup')
            pyproject_path.rename(backup_path)
        
        with open(pyproject_path, 'w', encoding='utf-8') as f:
            f.write(pyproject_content)
        
        # UV venv 생성
        cmd = ['uv', 'venv', '--python', python_version]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return err(f"프로젝트 초기화 실패: {result.stderr}")
        
        return ok({
            'project_name': project_name,
            'python_version': python_version,
            'pyproject': str(pyproject_path),
            'venv': '.venv',
            'message': f"UV 프로젝트 초기화 완료: {project_name}"
        })
    except FileNotFoundError:
        return err("UV가 설치되지 않음. 먼저 install_uv() 실행 필요")
    except Exception as e:
        return err(f"프로젝트 초기화 실패: {e}")

def create_venv(python_version: Optional[str] = None, name: str = ".venv") -> Dict[str, Any]:
    """
    UV로 가상환경 생성
    
    Args:
        python_version: Python 버전 (예: "3.11")
        name: 가상환경 디렉토리 이름
    
    Returns:
        Dict[str, Any]: 생성 결과
    """
    try:
        cmd = ['uv', 'venv', name]
        
        if python_version:
            cmd.extend(['--python', python_version])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return err(f"가상환경 생성 실패: {result.stderr}")
        
        # 활성화 스크립트 경로
        venv_path = Path.cwd() / name
        
        if platform.system() == "Windows":
            activate_cmd = f"{name}\\Scripts\\activate"
        else:
            activate_cmd = f"source {name}/bin/activate"
        
        return ok({
            'venv_path': str(venv_path),
            'activate_command': activate_cmd,
            'python_version': python_version or "시스템 기본값",
            'message': f"가상환경 생성 완료: {name}"
        })
    except FileNotFoundError:
        return err("UV가 설치되지 않음. 먼저 install_uv() 실행 필요")
    except Exception as e:
        return err(f"가상환경 생성 실패: {e}")

def pip_install(packages: Union[str, List[str]], dev: bool = False) -> Dict[str, Any]:
    """
    UV로 패키지 설치 (pip 호환)
    
    Args:
        packages: 패키지 이름 또는 목록
        dev: 개발 의존성으로 설치
    
    Returns:
        Dict[str, Any]: 설치 결과
    """
    try:
        if isinstance(packages, str):
            packages = [packages]
        
        cmd = ['uv', 'pip', 'install']
        cmd.extend(packages)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return err(f"패키지 설치 실패: {result.stderr}")
        
        # pyproject.toml 업데이트 (선택사항)
        if Path("pyproject.toml").exists():
            try:
                # UV add 명령으로 pyproject.toml 업데이트
                add_cmd = ['uv', 'add']
                if dev:
                    add_cmd.append('--dev')
                add_cmd.extend(packages)
                subprocess.run(add_cmd, capture_output=True, text=True)
            except:
                pass  # pyproject.toml 업데이트는 선택사항
        
        return ok({
            'packages': packages,
            'dev': dev,
            'message': f"패키지 설치 완료: {', '.join(packages)}"
        })
    except FileNotFoundError:
        return err("UV가 설치되지 않음. 먼저 install_uv() 실행 필요")
    except Exception as e:
        return err(f"패키지 설치 실패: {e}")

def pip_sync(requirements_file: str = "requirements.txt") -> Dict[str, Any]:
    """
    requirements 파일과 동기화
    
    Args:
        requirements_file: requirements 파일 경로
    
    Returns:
        Dict[str, Any]: 동기화 결과
    """
    try:
        req_path = resolve_project_path(requirements_file)
        
        if not req_path.exists():
            return err(f"파일 없음: {req_path}")
        
        cmd = ['uv', 'pip', 'sync', str(req_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # UV pip sync 실패시 install로 대체
            cmd = ['uv', 'pip', 'install', '-r', str(req_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return err(f"동기화 실패: {result.stderr}")
        
        return ok({
            'requirements_file': str(req_path),
            'message': "패키지 동기화 완료"
        })
    except FileNotFoundError:
        return err("UV가 설치되지 않음. 먼저 install_uv() 실행 필요")
    except Exception as e:
        return err(f"동기화 실패: {e}")

def pip_compile(requirements_in: str = "requirements.in", 
                requirements_out: str = "requirements.txt") -> Dict[str, Any]:
    """
    requirements.in을 requirements.txt로 컴파일
    
    Args:
        requirements_in: 입력 파일
        requirements_out: 출력 파일
    
    Returns:
        Dict[str, Any]: 컴파일 결과
    """
    try:
        in_path = resolve_project_path(requirements_in)
        out_path = resolve_project_path(requirements_out)
        
        if not in_path.exists():
            # requirements.in 생성
            with open(in_path, 'w', encoding='utf-8') as f:
                f.write("# 프로젝트 의존성\n")
                f.write("# 예: pandas>=2.0.0\n")
        
        cmd = ['uv', 'pip', 'compile', str(in_path), '-o', str(out_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return err(f"컴파일 실패: {result.stderr}")
        
        return ok({
            'input': str(in_path),
            'output': str(out_path),
            'message': f"requirements 컴파일 완료: {out_path.name}"
        })
    except FileNotFoundError:
        return err("UV가 설치되지 않음. 먼저 install_uv() 실행 필요")
    except Exception as e:
        return err(f"컴파일 실패: {e}")

def list_packages() -> Dict[str, Any]:
    """
    설치된 패키지 목록
    
    Returns:
        Dict[str, Any]: 패키지 목록
    """
    try:
        cmd = ['uv', 'pip', 'list', '--format', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # 일반 형식으로 재시도
            cmd = ['uv', 'pip', 'list']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return err(f"패키지 목록 조회 실패: {result.stderr}")
            
            # 텍스트 파싱
            lines = result.stdout.strip().split('\n')[2:]  # 헤더 제거
            packages = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    packages.append({
                        'name': parts[0],
                        'version': parts[1]
                    })
            
            return ok({
                'packages': packages,
                'count': len(packages)
            })
        
        packages = json.loads(result.stdout)
        
        return ok({
            'packages': packages,
            'count': len(packages)
        })
    except FileNotFoundError:
        return err("UV가 설치되지 않음. 먼저 install_uv() 실행 필요")
    except Exception as e:
        return err(f"패키지 목록 조회 실패: {e}")

def run_script(script: str, *args) -> Dict[str, Any]:
    """
    UV로 Python 스크립트 실행
    
    Args:
        script: 스크립트 파일 경로
        args: 추가 인자
    
    Returns:
        Dict[str, Any]: 실행 결과
    """
    try:
        script_path = resolve_project_path(script)
        
        if not script_path.exists():
            return err(f"스크립트 없음: {script_path}")
        
        cmd = ['uv', 'run', 'python', str(script_path)]
        cmd.extend(args)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return err(f"스크립트 실행 실패: {result.stderr}")
        
        return ok({
            'script': str(script_path),
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'message': "스크립트 실행 완료"
        })
    except FileNotFoundError:
        return err("UV가 설치되지 않음. 먼저 install_uv() 실행 필요")
    except Exception as e:
        return err(f"스크립트 실행 실패: {e}")

def cache_clean() -> Dict[str, Any]:
    """
    UV 캐시 정리
    
    Returns:
        Dict[str, Any]: 정리 결과
    """
    try:
        cmd = ['uv', 'cache', 'clean']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return err(f"캐시 정리 실패: {result.stderr}")
        
        return ok({
            'message': "UV 캐시 정리 완료",
            'output': result.stdout
        })
    except FileNotFoundError:
        return err("UV가 설치되지 않음. 먼저 install_uv() 실행 필요")
    except Exception as e:
        return err(f"캐시 정리 실패: {e}")

def tool_install(tool: str) -> Dict[str, Any]:
    """
    UV로 Python 도구 설치 (pipx 대체)
    
    Args:
        tool: 도구 이름 (예: "black", "ruff")
    
    Returns:
        Dict[str, Any]: 설치 결과
    """
    try:
        cmd = ['uv', 'tool', 'install', tool]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # pip install로 대체
            pip_cmd = ['uv', 'pip', 'install', tool]
            pip_result = subprocess.run(pip_cmd, capture_output=True, text=True)
            
            if pip_result.returncode != 0:
                return err(f"도구 설치 실패: {pip_result.stderr}")
            
            return ok({
                'tool': tool,
                'method': 'pip',
                'message': f"도구 설치 완료 (pip): {tool}"
            })
        
        return ok({
            'tool': tool,
            'method': 'uv tool',
            'message': f"도구 설치 완료: {tool}"
        })
    except FileNotFoundError:
        return err("UV가 설치되지 않음. 먼저 install_uv() 실행 필요")
    except Exception as e:
        return err(f"도구 설치 실패: {e}")

def quick_setup() -> Dict[str, Any]:
    """
    UV 빠른 프로젝트 설정 (한 번에 모든 설정)
    
    Returns:
        Dict[str, Any]: 설정 결과
    """
    try:
        results = []
        
        # 1. UV 설치
        uv_result = install_uv()
        results.append(("UV 설치", uv_result['ok']))
        
        if not uv_result['ok']:
            return err("UV 설치 실패")
        
        # 2. 프로젝트 초기화
        init_result = init_project()
        results.append(("프로젝트 초기화", init_result['ok']))
        
        # 3. 기본 패키지 설치
        packages = ['jupyter', 'ipykernel', 'pandas', 'numpy']
        install_result = pip_install(packages)
        results.append(("기본 패키지 설치", install_result['ok']))
        
        # 4. 개발 도구 설치
        dev_tools = ['pytest', 'black', 'ruff']
        dev_result = pip_install(dev_tools, dev=True)
        results.append(("개발 도구 설치", dev_result['ok']))
        
        # 5. Jupyter 커널 설치
        kernel_cmd = ['python', '-m', 'ipykernel', 'install', '--user', '--name', 'uv_project']
        kernel_result = subprocess.run(kernel_cmd, capture_output=True, text=True)
        results.append(("Jupyter 커널", kernel_result.returncode == 0))
        
        # 결과 요약
        success_count = sum(1 for _, success in results if success)
        total_count = len(results)
        
        return ok({
            'results': results,
            'success_rate': f"{success_count}/{total_count}",
            'message': f"UV 프로젝트 설정 완료 ({success_count}/{total_count} 성공)"
        })
    except Exception as e:
        return err(f"빠른 설정 실패: {e}")
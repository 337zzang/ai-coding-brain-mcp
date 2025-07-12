"""빌드 및 프로젝트 관리 함수들"""

import os
import json
import platform
import subprocess
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from .decorators import track_operation


@track_operation('build', 'find_executable')
def find_executable(names: Union[str, List[str]]) -> Optional[str]:
    """환경변수 PATH에서 실행 파일 찾기
    
    Args:
        names: 찾을 실행파일 이름(들)
    
    Returns:
        str: 실행파일 경로 또는 None
    """
    # 플랫폼별 실행 파일 확장자
    if platform.system() == 'Windows':
        extensions = ['.exe', '.cmd', '.bat', '']
    else:
        extensions = ['']
    
    # names가 문자열이면 리스트로 변환
    if isinstance(names, str):
        names = [names]
    
    # PATH 환경변수 검색
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    
    # 추가 환경변수 확인
    extra_paths = []
    for env_var in ['NODE_HOME', 'NPM_HOME', 'PROGRAMFILES', 'PROGRAMFILES(X86)']:
        if env_var in os.environ:
            extra_paths.append(os.environ[env_var])
            # node_modules/.bin 경로도 추가
            if 'NODE' in env_var or 'NPM' in env_var:
                extra_paths.append(os.path.join(os.environ[env_var], 'node_modules', '.bin'))
    
    # 모든 경로에서 검색
    all_paths = path_dirs + extra_paths
    
    for name in names:
        for path_dir in all_paths:
            if not path_dir:
                continue
            for ext in extensions:
                executable = os.path.join(path_dir, name + ext)
                if os.path.isfile(executable) and os.access(executable, os.X_OK):
                    return executable
    
    return None


@track_operation('build', 'detect')
def detect_project_type(project_path: str = '.') -> List[str]:
    """프로젝트 타입 자동 감지
    
    Args:
        project_path: 프로젝트 경로
    
    Returns:
        list: 감지된 프로젝트 타입 목록
    """
    project_types = []
    
    # package.json 확인 (Node.js/TypeScript)
    if os.path.exists(os.path.join(project_path, 'package.json')):
        project_types.append('node')
        
        # TypeScript 확인
        if os.path.exists(os.path.join(project_path, 'tsconfig.json')):
            project_types.append('typescript')
        
        # 빌드 도구 확인
        try:
            with open(os.path.join(project_path, 'package.json'), 'r') as f:
                content = f.read()
                if 'yarn' in content:
                    project_types.append('yarn')
                elif 'pnpm' in content:
                    project_types.append('pnpm')
                else:
                    project_types.append('npm')
        except:
            project_types.append('npm')
    
    # Python 프로젝트 확인
    if (os.path.exists(os.path.join(project_path, 'setup.py')) or 
        os.path.exists(os.path.join(project_path, 'pyproject.toml')) or 
        os.path.exists(os.path.join(project_path, 'requirements.txt'))):
        project_types.append('python')
    
    # Cargo.toml 확인 (Rust)
    if os.path.exists(os.path.join(project_path, 'Cargo.toml')):
        project_types.append('rust')
    
    return project_types


@track_operation('build', 'run_command')
def run_command(command: str, args: Optional[Union[str, List[str]]] = None, 
                cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """명령어 실행 (환경변수 포함)
    
    Args:
        command: 실행할 명령어
        args: 명령어 인자
        cwd: 작업 디렉토리
        env: 환경변수
    
    Returns:
        dict: 실행 결과
    """
    # 명령어 경로 찾기
    executable = find_executable(command)
    if not executable:
        return {
            'success': False,
            'error': f'실행 파일을 찾을 수 없습니다: {command}',
            'command': command
        }
    
    # 전체 명령어 구성
    full_command = [executable]
    if args:
        if isinstance(args, str):
            full_command.extend(args.split())
        else:
            full_command.extend(args)
    
    # 환경변수 설정
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)
    
    try:
        # 명령어 실행
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            cwd=cwd or os.getcwd(),
            env=cmd_env
        )
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'command': ' '.join(full_command)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'command': ' '.join(full_command)
        }


@track_operation('build', 'build')
def build_project(project_path: str = '.', script: Optional[str] = None) -> Dict[str, Any]:
    """프로젝트 자동 빌드
    
    Args:
        project_path: 프로젝트 경로
        script: 빌드 스크립트 (None이면 자동 감지)
    
    Returns:
        dict: 빌드 결과
    """
    # 프로젝트 타입 감지
    project_types = detect_project_type(project_path)
    
    if not project_types:
        return {
            'success': False,
            'error': '프로젝트 타입을 감지할 수 없습니다'
        }
    
    # Node.js/TypeScript 프로젝트
    if 'node' in project_types or 'typescript' in project_types:
        # 빌드 도구 선택
        if 'yarn' in project_types:
            tool = 'yarn'
        elif 'pnpm' in project_types:
            tool = 'pnpm'
        else:
            tool = 'npm'
        
        # 빌드 스크립트 결정
        if script:
            build_script = script
        else:
            # package.json에서 빌드 스크립트 확인
            try:
                with open(os.path.join(project_path, 'package.json'), 'r') as f:
                    pkg = json.load(f)
                    scripts = pkg.get('scripts', {})
                    
                    # 우선순위: build > compile > tsc
                    if 'build' in scripts:
                        build_script = 'build'
                    elif 'compile' in scripts:
                        build_script = 'compile'
                    elif 'tsc' in scripts:
                        build_script = 'tsc'
                    else:
                        # TypeScript 직접 실행
                        if 'typescript' in project_types:
                            return run_command('npx', ['tsc'], cwd=project_path)
                        else:
                            return {
                                'success': False,
                                'error': '빌드 스크립트를 찾을 수 없습니다'
                            }
            except:
                build_script = 'build'
        
        # 빌드 실행
        return run_command(tool, ['run', build_script], cwd=project_path)
    
    # Python 프로젝트
    elif 'python' in project_types:
        # Python은 일반적으로 빌드가 필요 없지만, setup.py가 있으면 실행
        if os.path.exists(os.path.join(project_path, 'setup.py')):
            python_exe = find_executable(['python3', 'python'])
            if python_exe:
                return run_command(python_exe, ['setup.py', 'build'], cwd=project_path)
        
        return {
            'success': True,
            'message': 'Python 프로젝트는 빌드가 필요하지 않습니다'
        }
    
    # Rust 프로젝트
    elif 'rust' in project_types:
        return run_command('cargo', ['build'], cwd=project_path)
    
    else:
        return {
            'success': False,
            'error': f'지원하지 않는 프로젝트 타입: {project_types}'
        }


@track_operation('build', 'install_deps')
def install_dependencies(project_path: str = '.') -> Dict[str, Any]:
    """프로젝트 의존성 설치
    
    Args:
        project_path: 프로젝트 경로
    
    Returns:
        dict: 설치 결과
    """
    project_types = detect_project_type(project_path)
    
    if not project_types:
        return {
            'success': False,
            'error': '프로젝트 타입을 감지할 수 없습니다'
        }
    
    results = []
    
    # Node.js 의존성
    if 'node' in project_types:
        if 'yarn' in project_types:
            result = run_command('yarn', ['install'], cwd=project_path)
        elif 'pnpm' in project_types:
            result = run_command('pnpm', ['install'], cwd=project_path)
        else:
            result = run_command('npm', ['install'], cwd=project_path)
        results.append(('Node.js', result))
    
    # Python 의존성
    if 'python' in project_types:
        if os.path.exists(os.path.join(project_path, 'requirements.txt')):
            python_exe = find_executable(['python3', 'python'])
            if python_exe:
                result = run_command(
                    python_exe, 
                    ['-m', 'pip', 'install', '-r', 'requirements.txt'],
                    cwd=project_path
                )
                results.append(('Python', result))
    
    # Rust 의존성
    if 'rust' in project_types:
        result = run_command('cargo', ['fetch'], cwd=project_path)
        results.append(('Rust', result))
    
    # 결과 정리
    success = all(r[1]['success'] for r in results if r)
    return {
        'success': success,
        'results': results,
        'project_types': project_types
    }
"""
NPM Builder Helper Functions for AI Coding Brain MCP
Windows 환경에서 Python REPL을 통해 npm 명령을 실행하는 헬퍼 함수들
"""

import subprocess
import os
import json
import sys
import time
import threading
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

class NpmBuilder:
    """NPM 명령 실행을 위한 헬퍼 클래스"""

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.encoding = 'cp949' if sys.platform == 'win32' else 'utf-8'

    def _stream_output(self, process: subprocess.Popen, prefix: str = "") -> List[str]:
        """실시간 출력 스트리밍"""
        output_lines = []

        def read_stream(stream, is_stderr=False):
            for line in iter(stream.readline, ''):
                if line:
                    try:
                        decoded_line = line.decode(self.encoding, errors='replace').rstrip()
                        if decoded_line:
                            print(f"{prefix}{decoded_line}")
                            output_lines.append(decoded_line)
                    except:
                        pass

        # stdout과 stderr를 별도 스레드에서 읽기
        stdout_thread = threading.Thread(target=read_stream, args=(process.stdout,))
        stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, True))

        stdout_thread.start()
        stderr_thread.start()

        stdout_thread.join()
        stderr_thread.join()

        return output_lines

    def run_npm_command(self, args: List[str], timeout: int = 300) -> Dict[str, Any]:
        """NPM 명령 실행 (실시간 출력)"""

        # Windows에서 npm 실행
        if sys.platform == 'win32':
            # cmd를 통해 실행
            cmd = ['cmd', '/c', 'npm'] + args
        else:
            cmd = ['npm'] + args

        print(f"\n🚀 실행: {' '.join(cmd[2:] if sys.platform == 'win32' else cmd)}")
        print("-" * 50)

        start_time = time.time()

        try:
            # 프로세스 시작
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_path),
                shell=False
            )

            # 실시간 출력 스트리밍
            output_lines = self._stream_output(process, "  ")

            # 프로세스 종료 대기
            process.wait(timeout=timeout)

            elapsed_time = time.time() - start_time

            return {
                'success': process.returncode == 0,
                'returncode': process.returncode,
                'output': '\n'.join(output_lines),
                'elapsed_time': f"{elapsed_time:.2f}초",
                'command': ' '.join(args)
            }

        except subprocess.TimeoutExpired:
            process.kill()
            return {
                'success': False,
                'error': f'타임아웃 ({timeout}초 초과)',
                'command': ' '.join(args)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': ' '.join(args)
            }

# 전역 헬퍼 함수들
def npm_build(project_path: str = ".") -> Dict[str, Any]:
    """npm run build 실행"""
    builder = NpmBuilder(project_path)
    return builder.run_npm_command(['run', 'build'])

def npm_install(packages: Optional[List[str]] = None, save_dev: bool = False, project_path: str = ".") -> Dict[str, Any]:
    """npm install 실행"""
    builder = NpmBuilder(project_path)
    args = ['install']

    if packages:
        args.extend(packages)
        if save_dev:
            args.append('--save-dev')

    return builder.run_npm_command(args)

def npm_run(script: str, project_path: str = ".") -> Dict[str, Any]:
    """npm run [script] 실행"""
    builder = NpmBuilder(project_path)
    return builder.run_npm_command(['run', script])

def npm_test(project_path: str = ".") -> Dict[str, Any]:
    """npm test 실행"""
    builder = NpmBuilder(project_path)
    return builder.run_npm_command(['test'])

def npm_scripts(project_path: str = ".") -> Dict[str, Any]:
    """package.json의 스크립트 목록 반환"""
    try:
        package_path = Path(project_path) / 'package.json'
        if package_path.exists():
            with open(package_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
                scripts = package_data.get('scripts', {})

                return {
                    'success': True,
                    'scripts': scripts,
                    'count': len(scripts),
                    'list': list(scripts.keys())
                }
        else:
            return {
                'success': False,
                'error': 'package.json 파일을 찾을 수 없습니다.'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def npm_version(project_path: str = ".") -> Dict[str, Any]:
    """npm 및 node 버전 확인"""
    builder = NpmBuilder(project_path)
    npm_ver = builder.run_npm_command(['--version'])

    # node 버전도 확인
    try:
        node_result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            cwd=project_path
        )
        node_version = node_result.stdout.strip()
    except:
        node_version = "확인 실패"

    return {
        'npm_version': npm_ver.get('output', '').strip(),
        'node_version': node_version,
        'success': npm_ver.get('success', False)
    }

def npm_clean(project_path: str = ".") -> Dict[str, Any]:
    """node_modules 및 package-lock.json 삭제"""
    import shutil

    results = []
    project_path = Path(project_path)

    # node_modules 삭제
    node_modules = project_path / 'node_modules'
    if node_modules.exists():
        try:
            shutil.rmtree(node_modules)
            results.append("✅ node_modules 삭제 완료")
        except Exception as e:
            results.append(f"❌ node_modules 삭제 실패: {e}")
    else:
        results.append("ℹ️ node_modules가 없습니다")

    # package-lock.json 삭제
    package_lock = project_path / 'package-lock.json'
    if package_lock.exists():
        try:
            package_lock.unlink()
            results.append("✅ package-lock.json 삭제 완료")
        except Exception as e:
            results.append(f"❌ package-lock.json 삭제 실패: {e}")
    else:
        results.append("ℹ️ package-lock.json이 없습니다")

    return {
        'success': True,
        'results': results
    }

# 사용 예시
if __name__ == "__main__":
    print("NPM Builder Helper Functions 로드됨!")
    print("\n사용 가능한 함수:")
    print("  - npm_build()       : 프로젝트 빌드")
    print("  - npm_install()     : 패키지 설치")
    print("  - npm_run(script)   : 스크립트 실행")
    print("  - npm_scripts()     : 스크립트 목록")
    print("  - npm_version()     : 버전 확인")
    print("  - npm_clean()       : 정리 작업")

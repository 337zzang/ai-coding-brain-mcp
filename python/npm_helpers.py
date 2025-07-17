"""
안전한 NPM 빌드 실행 헬퍼 함수들
AI Coding Brain MCP 프로젝트용
"""

import subprocess
import sys
import os
import time
from pathlib import Path
from typing import Union, Dict, Optional, Tuple

class NpmBuildError(Exception):
    """NPM 빌드 실행 중 발생하는 에러"""
    def __init__(self, message: str, stdout: str = "", stderr: str = "", returncode: int = -1):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

def get_project_path():
    """프로젝트 경로 반환"""
    # 환경변수 또는 기본값
    return os.environ.get('PROJECT_PATH', os.getcwd())

def safe_npm_run(
    script: str = "build",
    project_root: Union[str, Path] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: int = 600,
    capture_output: bool = True
) -> Dict[str, Union[bool, str, int]]:
    """
    안전한 npm 스크립트 실행

    Parameters
    ----------
    script : str
        실행할 npm 스크립트 (예: "build", "test", "lint")
    project_root : str | Path
        package.json이 있는 디렉토리
    env : dict
        추가 환경변수
    timeout : int
        타임아웃 (초 단위, 기본 10분)
    capture_output : bool
        출력 캡처 여부

    Returns
    -------
    dict
        {
            'success': bool,
            'stdout': str,
            'stderr': str,
            'returncode': int,
            'duration': float
        }

    Raises
    ------
    FileNotFoundError
        package.json이 없을 때
    NpmBuildError
        빌드 실패 또는 타임아웃
    """
    # 프로젝트 경로 설정
    if project_root is None:
        project_root = get_project_path()

    root = Path(project_root).expanduser().resolve()

    # package.json 확인
    pkg_path = root / "package.json"
    if not pkg_path.exists():
        raise FileNotFoundError(f"package.json not found in {root}")

    # 명령어 구성
    cmd = ["npm", "run", script]

    # 환경변수 설정
    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    # 시작 시간
    start_time = time.time()

    print(f"\n🔄 실행: npm run {script}")
    print(f"📍 디렉토리: {root}")
    if env:
        print(f"🔧 환경변수: {env}")
    print("-" * 50)

    try:
        # subprocess 실행
        if sys.platform == "win32":
            # Windows: shell=True 필요
            result = subprocess.run(
                cmd,
                cwd=root,
                env=process_env,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                shell=True,
                encoding='cp949',  # Windows 한글 인코딩
                errors='replace'
            )
        else:
            # Unix/Linux
            result = subprocess.run(
                cmd,
                cwd=root,
                env=process_env,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )

        duration = time.time() - start_time

        # 결과 딕셔너리
        output = {
            'success': result.returncode == 0,
            'stdout': result.stdout if capture_output else '',
            'stderr': result.stderr if capture_output else '',
            'returncode': result.returncode,
            'duration': duration
        }

        # 성공/실패 메시지
        if output['success']:
            print(f"\n✅ 성공! (소요시간: {duration:.1f}초)")
        else:
            print(f"\n❌ 실패! (exit code: {result.returncode})")
            if capture_output and result.stderr:
                print("\n에러 출력:")
                print(result.stderr[:500])
                if len(result.stderr) > 500:
                    print(f"... ({len(result.stderr) - 500}자 더)")

        # 실패 시 예외 발생
        if not output['success']:
            raise NpmBuildError(
                f"npm run {script} failed with exit code {result.returncode}",
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode
            )

        return output

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        raise NpmBuildError(
            f"npm run {script} timed out after {timeout} seconds",
            returncode=-1
        )
    except Exception as e:
        raise NpmBuildError(f"Failed to run npm script: {e}")

# 편의 함수들
def npm_build(project_root=None, **kwargs):
    """npm run build 실행"""
    return safe_npm_run("build", project_root=project_root, **kwargs)

def npm_test(project_root=None, **kwargs):
    """npm run test 실행"""
    return safe_npm_run("test", project_root=project_root, **kwargs)

def npm_lint(project_root=None, **kwargs):
    """npm run lint 실행"""
    return safe_npm_run("lint", project_root=project_root, **kwargs)

def npm_dev(project_root=None, **kwargs):
    """npm run dev 실행 (주의: 지속 실행)"""
    return safe_npm_run("dev", project_root=project_root, timeout=30, **kwargs)

def npm_type_check(project_root=None, **kwargs):
    """TypeScript 타입 체크 (npx tsc --noEmit)"""
    if project_root is None:
        project_root = get_project_path()

    root = Path(project_root).expanduser().resolve()

    # 직접 tsc 실행
    cmd = ["npx", "tsc", "--noEmit"]

    print(f"\n⚡ 타입 체크 실행")
    print(f"📍 디렉토리: {root}")
    print("-" * 50)

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=kwargs.get('timeout', 300),
            shell=True if sys.platform == "win32" else False,
            encoding='cp949' if sys.platform == "win32" else 'utf-8',
            errors='replace'
        )

        duration = time.time() - start_time

        if result.returncode == 0:
            print(f"\n✅ 타입 체크 통과! (소요시간: {duration:.1f}초)")
            return {
                'success': True,
                'duration': duration
            }
        else:
            print(f"\n❌ 타입 에러 발견! (소요시간: {duration:.1f}초)")

            # 에러 개수 파싱
            error_count = result.stdout.count('error TS') + result.stderr.count('error TS')
            print(f"\n총 {error_count}개의 타입 에러")

            # 처음 몇 개 에러만 출력
            output = result.stdout + result.stderr
            lines = output.split('\n')
            error_lines = [l for l in lines if 'error TS' in l or '.ts(' in l]

            print("\n주요 에러:")
            for line in error_lines[:10]:
                if line.strip():
                    print(f"  {line.strip()}")

            if len(error_lines) > 10:
                print(f"  ... ({len(error_lines) - 10}개 더)")

            raise NpmBuildError(
                f"Type check failed with {error_count} errors",
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode
            )

    except subprocess.TimeoutExpired:
        raise NpmBuildError("Type check timed out")

def install_dependencies(project_root=None):
    """npm install 실행"""
    if project_root is None:
        project_root = get_project_path()

    print("\n📦 의존성 설치 시작...")
    print("이 작업은 몇 분 정도 걸릴 수 있습니다.")

    original_dir = os.getcwd()

    try:
        os.chdir(project_root)

        print(f"\n실행: npm install")
        print(f"디렉토리: {project_root}")
        print("-" * 50)

        exit_code = os.system("npm install")

        if exit_code == 0:
            print("\n✅ 의존성 설치 완료!")
            return True
        else:
            print(f"\n❌ 설치 실패! (exit code: {exit_code})")
            return False

    finally:
        os.chdir(original_dir)

def quick_build_test(project_root=None):
    """빠른 빌드 테스트 (타입체크 + 빌드)"""
    print("\n⚡ 빠른 빌드 테스트")
    print("=" * 60)

    try:
        # 타입 체크
        print("\n[1/2] 타입 체크")
        npm_type_check(project_root)

        # 빌드
        print("\n[2/2] 빌드")
        result = npm_build(project_root)

        print("\n✅ 빌드 테스트 통과!")
        return True

    except NpmBuildError as e:
        print(f"\n❌ 빌드 테스트 실패: {e}")
        return False

def full_build_pipeline(project_root=None, skip_tests=False):
    """
    전체 빌드 파이프라인 실행

    순서:
    1. 타입 체크
    2. ESLint
    3. 빌드
    4. 테스트 (선택적)
    """
    if project_root is None:
        project_root = get_project_path()

    print("\n🚀 전체 빌드 파이프라인 시작")
    print("=" * 60)

    results = {}
    total_duration = 0

    steps = [
        ("타입 체크", lambda: npm_type_check(project_root)),
        ("ESLint", lambda: npm_lint(project_root)),
        ("빌드", lambda: npm_build(project_root))
    ]

    if not skip_tests:
        steps.append(("테스트", lambda: npm_test(project_root)))

    for step_name, step_func in steps:
        print(f"\n[{len(results) + 1}/{len(steps)}] {step_name}")

        try:
            result = step_func()
            results[step_name] = True
            total_duration += result.get('duration', 0)
        except NpmBuildError as e:
            results[step_name] = False
            print(f"\n💥 {step_name} 단계에서 실패!")

            # 실패 시 나머지 단계 건너뛰기
            for remaining_step, _ in steps[len(results):]:
                results[remaining_step] = False
                print(f"\n[스킵] {remaining_step}")

            break
        except Exception as e:
            results[step_name] = False
            print(f"\n💥 예외 발생: {e}")
            break

    # 결과 요약
    print("\n\n📊 빌드 파이프라인 결과")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for step, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {step}")

    print(f"\n전체: {passed}/{total} 통과")
    print(f"총 소요시간: {total_duration:.1f}초")

    if passed == total:
        print("\n🎉 모든 단계를 통과했습니다!")
    else:
        print("\n⚠️  일부 단계에서 실패했습니다.")

    return passed == total

# __all__ 정의로 공개 API 명시
__all__ = [
    'NpmBuildError',
    'safe_npm_run',
    'npm_build',
    'npm_test',
    'npm_lint',
    'npm_dev',
    'npm_type_check',
    'install_dependencies',
    'quick_build_test',
    'full_build_pipeline'
]

if __name__ == "__main__":
    print("NPM 헬퍼 모듈 로드됨")
    print(f"사용 가능한 함수: {', '.join(__all__)}")

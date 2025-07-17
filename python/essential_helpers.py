"""
Essential Helpers - q_tools를 보완하는 필수 헬퍼 함수들
q_tools로 커버되지 않는 핵심 기능들만 포함
"""

import json
import yaml
import os
from pathlib import Path

# === JSON/YAML 처리 ===
def qjr(file_path):
    """Quick JSON Read - JSON 파일 읽기"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"📄 {file_path}: {len(data)} keys" if isinstance(data, dict) else f"{len(data)} items")
    return data

def qjw(file_path, data):
    """Quick JSON Write - JSON 파일 쓰기"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 {file_path} 저장 완료")
    return True

# === 파일 작업 확장 ===
def qcf(file_path, content=""):
    """Quick Create File - 새 파일 생성"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {file_path} 생성 완료")
    return True

def qa(file_path, content):
    """Quick Append - 파일에 내용 추가"""
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(content)
    lines = content.count('\n') + 1
    print(f"➕ {file_path}에 {lines}줄 추가")
    return True

# === 고급 검색 ===
def qgrep(pattern, path=".", context=2):
    """Quick Grep - 정규식 검색"""
    import re
    import glob

    results = []
    files = glob.glob(f"{path}/**/*.py", recursive=True)

    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    results.append({
                        'file': file,
                        'line': i + 1,
                        'text': line.strip(),
                        'context': lines[max(0, i-context):i+context+1]
                    })
        except:
            pass

    print(f"🔍 '{pattern}' 검색: {len(results)}개 발견")
    for r in results[:5]:
        print(f"  {r['file']}:{r['line']} - {r['text']}")

    return results

# === 프로젝트 관리 (간소화) ===
def qproj_info():
    """Quick Project Info - 현재 프로젝트 정보"""
    cwd = os.getcwd()
    project_name = os.path.basename(cwd)

    # 파일 통계
    py_files = len(list(Path('.').rglob('*.py')))
    total_size = sum(f.stat().st_size for f in Path('.').rglob('*') if f.is_file())

    print(f"📊 프로젝트: {project_name}")
    print(f"  경로: {cwd}")
    print(f"  Python 파일: {py_files}개")
    print(f"  전체 크기: {total_size / 1024 / 1024:.1f} MB")

    return {
        'name': project_name,
        'path': cwd,
        'py_files': py_files,
        'size_mb': total_size / 1024 / 1024
    }

# === 간단한 히스토리 ===
_command_history = []

def qhist(n=10):
    """Quick History - 최근 명령 히스토리"""
    print(f"📜 최근 {n}개 명령:")
    for i, cmd in enumerate(_command_history[-n:], 1):
        print(f"  {i}. {cmd}")
    return _command_history[-n:]

def record_command(cmd):
    """명령 기록 (내부용)"""
    _command_history.append(cmd)
    if len(_command_history) > 100:
        _command_history.pop(0)

# === NPM 기본 명령 (간소화) ===
def qnpm(command="install"):
    """Quick NPM - NPM 명령 실행"""
    import subprocess

    cmd_map = {
        "install": "npm install",
        "build": "npm run build",
        "test": "npm test",
        "start": "npm start"
    }

    cmd = cmd_map.get(command, f"npm {command}")
    print(f"🚀 실행: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ 성공")
    else:
        print(f"❌ 실패: {result.stderr}")

    return result

# 모든 함수 export
__all__ = ['qjr', 'qjw', 'qcf', 'qa', 'qgrep', 'qproj_info', 'qhist', 'qnpm']

"""
REPL 친화적 code_ops 도구 모음
빠른 코드 작업을 위한 2글자 약어 함수들

사용법:
  from q_tools import *


# REPL 환경의 helpers 가져오기
try:
    # JSON REPL 환경에서 helpers 가져오기
    import sys
    if hasattr(sys.modules.get('__main__', None), 'helpers'):
        helpers = sys.modules['__main__'].helpers
    else:
        helpers = None
except:
    helpers = None

  qp("file.py")              # 파일 구조 분석
  qv("file.py", "func_name") # 함수 코드 보기
  qr("file.py", "func", new_code) # 함수 교체
"""

# 필요한 import들은 실행 시점에 동적으로 처리
def get_helpers():
    """helpers 객체를 동적으로 가져오기"""
    import sys
    if 'helpers' in sys.modules['__main__'].__dict__:
        return sys.modules['__main__'].__dict__['helpers']
    return None

def qp(file_path):
    """Quick Parse - 파일을 빠르게 파싱하고 요약 출력"""
    helpers = get_helpers()
    if not helpers:
        print("❌ helpers를 찾을 수 없습니다")
        return None

    # safe_parse_file 사용
    if hasattr(helpers, 'safe_parse_file'):
        result = helpers.safe_parse_file(file_path)
    else:
        # 전역에서 찾기
        import sys
        result = sys.modules['__main__'].__dict__['safe_parse_file'](file_path)

    if result['success']:
        print(f"📄 {file_path}")
        print(f"  함수: {len(result.get('functions', []))}개")
        print(f"  클래스: {len(result.get('classes', []))}개")
        print(f"  전체 라인: {result.get('total_lines', 0)}")

        if result.get('functions'):
            print("\n  함수 목록:")
            for func in result['functions']:
                name = func.get('name', 'Unknown')
                print(f"    - {name}()")

        if result.get('classes'):
            print("\n  클래스 목록:")
            for cls in result['classes']:
                name = cls.get('name', 'Unknown')
                print(f"    - {name}")
        return result
    else:
        print(f"❌ 파싱 실패: {result.get('error', 'Unknown')}")
        return None

def ql(file_path):
    """Quick List - 함수/클래스 목록만 빠르게 보기"""
    helpers = get_helpers()
    if helpers and hasattr(helpers, 'list_functions'):
        funcs = helpers.list_functions(file_path)
    else:
        # 대체: qp 사용
        result = qp(file_path)
        if result and result['success']:
            funcs = [f['name'] for f in result.get('functions', [])]
        else:
            funcs = []

    if funcs:
        print(f"📄 {file_path} 함수들:")
        for i, func in enumerate(funcs, 1):
            print(f"  {i}. {func}")
    return funcs

def qv(file_path, func_name):
    """Quick View - 함수 코드를 빠르게 보기"""
    helpers = get_helpers()
    if not helpers:
        print("❌ helpers를 찾을 수 없습니다")
        return None

    # get_function_code 시도
    if hasattr(helpers, 'get_function_code'):
        code = helpers.get_function_code(file_path, func_name)
        if code:
            print(f"\n📄 {file_path} - {func_name}():")
            print("=" * 60)
            print(code)
            print("=" * 60)
            return code

    # 대체: safe_parse_file 사용
    import sys
    safe_parse_file = sys.modules['__main__'].__dict__.get('safe_parse_file')
    if safe_parse_file:
        result = safe_parse_file(file_path)
        if result['success']:
            for func in result.get('functions', []):
                if func['name'] == func_name:
                    content = helpers.read_file(file_path)
                    lines = content.split('\n')
                    start = func.get('start', 0)
                    end = func.get('end', len(lines))
                    code = '\n'.join(lines[start:end])

                    print(f"\n📄 {file_path} - {func_name}():")
                    print("=" * 60)
                    print(code)
                    print("=" * 60)
                    return code

    print(f"❌ 함수를 찾을 수 없음: {func_name}")
    return None

def qr(file_path, func_name, new_code):
    """Quick Replace - 함수를 빠르게 교체"""
    helpers = get_helpers()
    if not helpers:
        print("❌ helpers를 찾을 수 없습니다")
        return None

    # 현재 함수 코드 가져오기
    import sys
    safe_parse_file = sys.modules['__main__'].__dict__.get('safe_parse_file')
    if safe_parse_file:
        result = safe_parse_file(file_path)
        if result['success']:
            for func in result.get('functions', []):
                if func['name'] == func_name:
                    content = helpers.read_file(file_path)
                    lines = content.split('\n')
                    old_code = '\n'.join(lines[func['start']:func['end']])

                    # 교체 실행
                    replace_result = helpers.replace_block(file_path, old_code, new_code)
                    if replace_result['success']:
                        print(f"✅ {func_name} 함수 교체 완료!")
                        print(f"   변경된 라인: {replace_result.get('lines_changed', 'Unknown')}")
                        return replace_result
                    else:
                        print(f"❌ 교체 실패")
                        return None

    print(f"❌ 함수를 찾을 수 없음: {func_name}")
    return None

def qi(file_path, target, code, pos="after"):
    """Quick Insert - 특정 위치에 코드 삽입"""
    helpers = get_helpers()
    if not helpers:
        print("❌ helpers를 찾을 수 없습니다")
        return None

    result = helpers.insert_block(file_path, target, code, position=pos)
    if result['success']:
        print(f"✅ 코드 삽입 완료!")
        print(f"   위치: {target} {pos}")
        print(f"   삽입된 라인: {result.get('lines_inserted', 'Unknown')}")
    else:
        print(f"❌ 삽입 실패")
    return result

def qs(pattern, file_pattern="*.py"):
    """Quick Search - 코드에서 패턴 검색"""
    helpers = get_helpers()
    if not helpers:
        print("❌ helpers를 찾을 수 없습니다")
        return []

    results = helpers.search_code(".", pattern, file_pattern)

    print(f"🔍 '{pattern}' 검색 결과: {len(results)}개")

    # 파일별로 그룹화
    by_file = {}
    for r in results:
        if r['file'] not in by_file:
            by_file[r['file']] = []
        by_file[r['file']].append(r)

    # 출력
    for file, matches in list(by_file.items())[:5]:  # 처음 5개 파일만
        print(f"\n📄 {file} ({len(matches)}개):")
        for match in matches[:3]:  # 각 파일당 처음 3개만
            print(f"  라인 {match['line_number']}: {match['line'].strip()}")

    return results

def qm(file_path, class_name, method_name):
    """Quick Method - 클래스의 메서드 코드 보기"""
    import sys
    safe_parse_file = sys.modules['__main__'].__dict__.get('safe_parse_file')
    helpers = get_helpers()

    if not safe_parse_file or not helpers:
        print("❌ 필요한 함수를 찾을 수 없습니다")
        return None

    result = safe_parse_file(file_path)
    if result['success']:
        for cls in result.get('classes', []):
            if cls['name'] == class_name:
                for method in cls.get('methods', []):
                    if method['name'] == method_name:
                        content = helpers.read_file(file_path)
                        lines = content.split('\n')
                        # 메서드 코드 추출 로직
                        start = method.get('start', method.get('line', 0))

                        # 메서드 끝 찾기
                        end = start + 1
                        if start < len(lines):
                            base_indent = len(lines[start]) - len(lines[start].lstrip())
                            for i in range(start + 1, len(lines)):
                                line = lines[i]
                                if line.strip() and len(line) - len(line.lstrip()) <= base_indent:
                                    end = i
                                    break
                            else:
                                end = len(lines)

                        code = '\n'.join(lines[start:end])
                        print(f"\n📄 {file_path} - {class_name}.{method_name}():")
                        print("=" * 60)
                        print(code)
                        print("=" * 60)
                        return code

    print(f"❌ 메서드를 찾을 수 없음: {class_name}.{method_name}")
    return None

def qd(file_path):
    """Quick Diff - 파일의 최근 변경사항 확인"""
    try:
        import subprocess
        result = subprocess.run(['git', 'diff', file_path], 
                              capture_output=True, text=True)
        if result.stdout:
            print(f"📄 {file_path} 변경사항:")
            print("=" * 60)
            print(result.stdout)
            print("=" * 60)
        else:
            print(f"✅ {file_path}: 변경사항 없음")
    except Exception as e:
        print(f"❌ Git diff 실행 실패: {e}")

# 모든 q* 함수를 __all__에 추가
# === 파일 작업 확장 ===
def qf(file_path):
    """Quick File - 파일 내용 빠르게 읽기"""
    helpers = get_helpers()
    if helpers:
        content = helpers.read_file(file_path)
        print(f"📄 {file_path} ({len(content.split(''))} lines)")
        print("=" * 60)
        print(content[:1000] + "..." if len(content) > 1000 else content)
        print("=" * 60)
        return content
    return None

def qw(file_path, content):
    """Quick Write - 파일 빠르게 쓰기"""
    helpers = get_helpers()
    if helpers:
        result = helpers.write_file(file_path, content)
        if result:
            print(f"✅ {file_path} 저장 완료 ({len(content.split(''))} lines)")
        return result
    return False

def qe(file_path):
    """Quick Exists - 파일 존재 확인"""
    helpers = get_helpers()
    if helpers and hasattr(helpers, 'file_exists'):
        exists = helpers.file_exists(file_path)
    else:
        import os
        exists = os.path.exists(file_path)

    print(f"{'✅' if exists else '❌'} {file_path}: {'존재함' if exists else '없음'}")
    return exists

# === Git 작업 확장 ===
def qg():
    """Quick Git - Git 상태 확인"""
    helpers = get_helpers()
    if helpers:
        status = helpers.git_status()
        if status['success']:
            print("📊 Git Status:")
            print(f"  수정됨: {len(status.get('modified', []))}개")
            print(f"  새파일: {len(status.get('untracked', []))}개")
            print(f"  스테이지: {len(status.get('staged', []))}개")

            if status.get('modified'):
                print("수정된 파일:")
                for f in status['modified'][:5]:
                    print(f"  M {f}")

            if status.get('untracked'):
                print("추적안됨:")
                for f in status['untracked'][:5]:
                    print(f"  ? {f}")
        return status
    return None

def qc(message):
    """Quick Commit - 빠른 Git 커밋"""
    helpers = get_helpers()
    if helpers:
        # 모든 변경사항 추가
        helpers.git_add(".")
        # 커밋
        result = helpers.git_commit(message)
        if result['success']:
            print(f"✅ 커밋 완료: {message}")
        else:
            print(f"❌ 커밋 실패: {result.get('stderr', 'Unknown error')}")
        return result
    return None

def qb(file_path, old_text, new_text):
    """Quick Block replace - 부분 텍스트 교체"""
    helpers = get_helpers()
    if helpers:
        result = helpers.replace_block(file_path, old_text, new_text)
        if result['success']:
            print(f"✅ 교체 완료: {result.get('lines_changed', 0)}줄 변경")
        else:
            print("❌ 교체 실패")
        return result
    return None

# === 디렉토리 작업 확장 ===
def qls(path="."):
    """Quick List - 디렉토리 내용 보기"""
    helpers = get_helpers()
    if helpers:
        items = helpers.list_directory(path)
        print(f"📁 {path}:")

        dirs = [i for i in items if "[DIR]" in i]
        files = [i for i in items if "[FILE]" in i]

        if dirs:
            print("디렉토리:")
            for d in sorted(dirs)[:10]:
                print(f"  {d}")

        if files:
            print("파일:")
            for f in sorted(files)[:10]:
                print(f"  {f}")

        print(f"총: {len(dirs)}개 디렉토리, {len(files)}개 파일")

        return items
    return []

def qfind(pattern, path="."):
    """Quick Find - 파일 찾기"""
    helpers = get_helpers()
    if helpers:
        results = helpers.search_files(path, pattern)
        print(f"🔍 '{pattern}' 검색 결과: {len(results)}개")

        for i, file in enumerate(results[:10], 1):
            print(f"  {i}. {file}")

        if len(results) > 10:
            print(f"  ... 외 {len(results) - 10}개")

        return results
    return []

# === 프로젝트 작업 ===
def qproj(name=None):
    """Quick Project - 프로젝트 전환 또는 정보"""
    import sys  # 함수 시작에서 무조건 import
    if name:
        if 'fp' in sys.modules['__main__'].__dict__:
            return sys.modules['__main__'].__dict__['fp'](name)
    else:
        if 'pi' in sys.modules['__main__'].__dict__:
            info = sys.modules['__main__'].__dict__['pi']()
            print("📊 현재 프로젝트 정보:")
            if info:
                for k, v in info.items():
                    print(f"  {k}: {v}")
            return info
    return None

# 기존 __all__에 추가

# === Git 고급 작업 ===
def qpush(message=None):
    """Quick Push - Git add, commit, push를 한번에"""
    helpers = get_helpers()
    if not helpers:
        print("❌ helpers를 찾을 수 없습니다")
        return None

    try:
        # 1. 변경사항 확인
        status = helpers.git_status()
        if not status['success']:
            print("❌ Git 상태 확인 실패")
            return None

        modified_count = len(status.get('modified', []))
        untracked_count = len(status.get('untracked', []))

        if modified_count == 0 and untracked_count == 0:
            print("ℹ️ 변경사항이 없습니다")
            return None

        print(f"📊 변경사항: {modified_count}개 수정, {untracked_count}개 새파일")

        # 2. 모두 추가
        add_result = helpers.git_add(".")
        if add_result['success']:
            print("✅ 파일 추가 완료")

        # 3. 커밋 (메시지가 없으면 자동 생성)
        if not message:
            message = f"Update: {modified_count} files modified, {untracked_count} new files"

        commit_result = helpers.git_commit(message)
        if commit_result['success']:
            print(f"✅ 커밋 완료: {message}")
        else:
            print(f"❌ 커밋 실패: {commit_result.get('stderr', 'Unknown error')}")
            return commit_result

        # 4. Push
        push_result = helpers.git_push()
        if push_result['success']:
            print("✅ Push 완료!")
        else:
            err = push_result.get('stderr', 'Unknown error')
            print(f"❌ Push 실패: {err}")

        return push_result

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

def qpull():
    """Quick Pull - Git pull 실행"""
    helpers = get_helpers()
    if not helpers:
        print("❌ helpers를 찾을 수 없습니다")
        return None

    try:
        result = helpers.git_pull()
        if result['success']:
            print("✅ Pull 완료!")
            if result.get('stdout'):
                print(result['stdout'])
        else:
            err = result.get('stderr', 'Unknown error')
            print(f"❌ Pull 실패: {err}")
        return result
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

def qlog(n=5):
    """Quick Log - 최근 커밋 로그 보기"""
    try:
        import subprocess
        result = subprocess.run(['git', 'log', f'-{n}', '--oneline'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"📜 최근 {n}개 커밋:")
            lines = result.stdout.strip().split('\n')
            for i, line in enumerate(lines, 1):
                print(f"  {i}. {line}")
        else:
            print("❌ Git log 실행 실패")
            # 대체 방법
            import os
            os.system(f'git log -{n} --oneline')
        return result
    except Exception as e:
        print(f"❌ 오류: {e}")
        print("Git이 설치되지 않았거나 PATH에 없습니다")
        return None


__all__ = ['qp', 'ql', 'qv', 'qr', 'qi', 'qs', 'qm', 'qd',
           'qf', 'qw', 'qe', 'qg', 'qc', 'qb', 'qls', 'qfind', 'qproj',
           'qpush', 'qpull', 'qlog']

# HelperResult 실용 예제

## 1. 파일 읽고 처리하기
```python
# JSON 설정 파일 읽기
config_result = helpers.read_json("config.json")
if config_result.ok:
    config = config_result.get_data({})
    api_key = config.get('api_key', '')
else:
    print(f"설정 파일 읽기 실패: {config_result.error}")
    config = {}

# 텍스트 파일 읽기
file_result = helpers.read_file("data.txt")
if file_result.ok:
    # ⚠️ 주의: content는 dict 안에 있음!
    content = file_result.data['content']
    lines = content.split('\n')
    print(f"파일에 {len(lines)}줄이 있습니다.")
```

## 2. 디렉토리 탐색
```python
# 프로젝트 구조 스캔
scan_result = helpers.scan_directory_dict(".")
if scan_result.ok:
    data = scan_result.get_data({})

    # Python 파일만 필터링
    py_files = [f for f in data['files'] if f['name'].endswith('.py')]
    print(f"Python 파일: {len(py_files)}개")

    # 크기별 정렬
    large_files = sorted(data['files'], key=lambda x: x['size'], reverse=True)[:5]
    print("가장 큰 파일 5개:")
    for f in large_files:
        print(f"  - {f['name']}: {f['size']:,} bytes")
```

## 3. 코드 검색
```python
# 특정 패턴 검색
search_result = helpers.search_code_content(".", "TODO|FIXME", "*.py")
if search_result.ok:
    results = search_result.get_data({}).get('results', [])

    todo_count = 0
    for file_result in results:
        matches = file_result.get('matches', [])
        todo_count += len(matches)

        if matches:
            print(f"\n{file_result['file_path']}:")
            for match in matches[:3]:  # 처음 3개만
                print(f"  L{match['line']}: {match['content'].strip()}")

    print(f"\n총 {todo_count}개의 TODO/FIXME 발견")
```

## 4. Git 작업
```python
# Git 상태 확인 후 커밋
status_result = helpers.git_status()
if status_result.ok:
    status = status_result.get_data({})

    if not status['clean']:
        print(f"브랜치: {status['branch']}")
        print(f"수정된 파일: {len(status['modified'])}개")

        # 변경사항이 있으면 커밋
        if status['modified']:
            # 모든 파일 추가
            helpers.git_add(".")

            # 커밋 메시지 생성
            files = status['modified'][:3]  # 처음 3개 파일
            message = f"Update {', '.join(files)}"
            if len(status['modified']) > 3:
                message += f" and {len(status['modified']) - 3} more files"

            # 커밋
            commit_result = helpers.git_commit(message)
            if commit_result.ok:
                print(f"✅ 커밋 완료: {message}")
```

## 5. 워크플로우 관리
```python
# 현재 상태 확인
status_result = helpers.workflow("/status")
if status_result.ok:
    data = status_result.get_data({})

    if data['status'] == 'active':
        print(f"📋 현재 플랜: {data['plan_name']}")
        print(f"📊 진행률: {data['progress_percent']}%")

        # 현재 태스크 정보
        current = data.get('current_task')
        if current:
            print(f"🎯 작업 중: {current['title']}")

            # 작업 완료 처리
            if input("완료하셨나요? (y/n): ").lower() == 'y':
                next_result = helpers.workflow("/next 작업 완료!")
                if next_result.ok:
                    next_data = next_result.get_data({})
                    if next_data.get('next_task'):
                        print(f"➡️ 다음: {next_data['next_task']['title']}")
                    else:
                        print("✅ 모든 태스크 완료!")
```

## 6. 에러 처리 패턴
```python
def safe_file_operation(filename):
    """안전한 파일 작업 예제"""
    try:
        # 파일 읽기 시도
        result = helpers.read_file(filename)

        if not result.ok:
            # 에러 타입에 따른 처리
            if "FileNotFoundError" in str(result.error):
                print(f"파일이 없습니다. 새로 생성합니다: {filename}")
                helpers.create_file(filename, "# 새 파일\n")
                return None
            else:
                print(f"파일 읽기 오류: {result.error}")
                return None

        # 성공한 경우
        content = result.data['content']
        return content

    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return None
```

## 7. 통합 예제: 프로젝트 분석
```python
def analyze_project():
    """프로젝트 전체 분석"""
    results = {
        'total_files': 0,
        'total_lines': 0,
        'languages': {},
        'todos': 0
    }

    # 1. 디렉토리 스캔
    scan = helpers.scan_directory_dict(".")
    if scan.ok:
        files = scan.get_data({}).get('files', [])
        results['total_files'] = len(files)

        # 2. 파일별 분석
        for file_info in files:
            ext = file_info['name'].split('.')[-1] if '.' in file_info['name'] else 'no_ext'
            results['languages'][ext] = results['languages'].get(ext, 0) + 1

            # Python 파일 라인 수 계산
            if ext == 'py':
                read_result = helpers.read_file(file_info['path'])
                if read_result.ok:
                    content = read_result.data['content']
                    lines = content.split('\n')
                    results['total_lines'] += len(lines)

    # 3. TODO 검색
    todo_search = helpers.search_code_content(".", "TODO", "*.py")
    if todo_search.ok:
        for file_result in todo_search.get_data({}).get('results', []):
            results['todos'] += len(file_result.get('matches', []))

    # 4. Git 정보
    git_status = helpers.git_status()
    if git_status.ok:
        git_data = git_status.get_data({})
        results['git_branch'] = git_data.get('branch', 'unknown')
        results['uncommitted_changes'] = len(git_data.get('modified', []))

    return results

# 실행
analysis = analyze_project()
print(f"📊 프로젝트 분석 결과:")
print(f"  - 총 파일: {analysis['total_files']}개")
print(f"  - Python 코드: {analysis['total_lines']:,}줄")
print(f"  - TODO 항목: {analysis['todos']}개")
print(f"  - Git 브랜치: {analysis.get('git_branch', 'N/A')}")
```

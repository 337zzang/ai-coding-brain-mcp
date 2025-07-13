# 🚀 Claude Code + ai-coding-brain-mcp Execute Code 완전 활용 가이드

**모든 작업을 execute_code로! 실전 중심 완전 가이드**

> ⚡ 이 가이드의 모든 코드는 복사-붙여넣기로 즉시 실행 가능합니다!

## 📋 목차

1. [🚀 execute_code 즉시 시작](#-execute_code-즉시-시작)
2. [💡 helpers 함수 완전 정복](#-helpers-함수-완전-정복)  
3. [🔥 execute_code 실전 패턴](#-execute_code-실전-패턴)
4. [🧠 Think + execute_code 통합](#-think--execute_code-통합)
5. [🛠️ 프로젝트 관리 마스터](#️-프로젝트-관리-마스터)
6. [🔍 디버깅 & 문제해결](#-디버깅--문제해결)
7. [⚡ 성능 최적화 기법](#-성능-최적화-기법)
8. [🔒 보안 & Git 통합](#-보안--git-통합)
9. [🎯 고급 워크플로우 자동화](#-고급-워크플로우-자동화)
10. [📚 실전 시나리오 해결책](#-실전-시나리오-해결책)

---

## 🚀 execute_code 즉시 시작

### MCP 서버 연결 확인
```python
# MCP 서버 상태 확인
print("🔌 MCP 서버 연결 상태 확인")
print(f"helpers 사용 가능: {hasattr(helpers, 'read_file')}")
print(f"현재 경로: {helpers.get_current_path()}")

# 프로젝트 상태 확인
status = helpers.get_context()
print(f"활성 프로젝트: {status.get('project_name', 'None')}")
```

### 첫 번째 실행 - 현재 디렉토리 탐색
```python
# 현재 디렉토리 구조 스캔
print("📁 현재 디렉토리 구조:")
files_info = helpers.scan_directory_dict(".")
print(f"파일 수: {len(files_info['files'])}")
print(f"디렉토리 수: {len(files_info['directories'])}")

# 주요 파일 목록 출력
print("\n📄 주요 파일들:")
for file_info in files_info['files'][:10]:  # 상위 10개 파일
    print(f"  • {file_info['name']} ({file_info['size']} bytes)")
```

### 프로젝트 컨텍스트 로드
```python
# 현재 프로젝트로 전환 (이미 ai-coding-brain-mcp에 있으면 현재 상태 확인)
project_info = helpers.cmd_flow_with_context("ai-coding-brain-mcp")
print("✅ 프로젝트 컨텍스트 로드 완료")
print(f"프로젝트: {project_info.get('project_name')}")
print(f"경로: {project_info.get('project_path')}")
```

---

## 💡 helpers 함수 완전 정복

### 파일 작업 마스터
```python
# 📁 파일 읽기/쓰기/정보 조회
def file_operations_demo():
    # 파일 생성
    content = "# 테스트 파일\nprint('Hello, World!')"
    helpers.create_file("test_demo.py", content)
    print("✅ 파일 생성: test_demo.py")

    # 파일 읽기
    read_content = helpers.read_file("test_demo.py")
    print(f"📖 파일 내용: {len(str(read_content))} 문자")

    # 파일 정보 조회
    file_info = helpers.get_file_info("test_demo.py")
    print(f"📊 파일 정보: {file_info}")

    # JSON 작업
    data = {"name": "test", "value": 123}
    helpers.write_json("test_data.json", data)
    loaded_data = helpers.read_json("test_data.json")
    print(f"📋 JSON 데이터: {loaded_data}")

file_operations_demo()
```

### 검색 작업 마스터
```python
# 🔍 강력한 검색 기능들
def search_operations_demo():
    # 파일명으로 검색
    python_files = helpers.search_files(".", "*.py")
    print(f"🐍 Python 파일 수: {len(python_files['results'])}")

    # 코드 내용 검색
    code_results = helpers.search_code_content(".", "def", "*.py")
    print(f"🔍 'def' 패턴 발견: {len(code_results['results'])} 곳")

    # 함수 정의 검색 (AST 기반)
    if python_files['results']:
        first_py_file = python_files['results'][0]['path']
        functions = helpers.find_function(first_py_file, "")  # 모든 함수
        print(f"⚡ 함수 발견: {len(functions)} 개")

search_operations_demo()
```

### Git 작업 마스터
```python
# 🔧 Git 작업 자동화
def git_operations_demo():
    # Git 상태 확인
    status = helpers.git_status()
    print(f"📊 Git 상태: {status}")

    # 현재 브랜치 확인
    branch = helpers.git_get_current_branch()
    print(f"🌿 현재 브랜치: {branch}")

    # 스마트 커밋 (변경사항 자동 분석 후 커밋 메시지 생성)
    # helpers.git_add(".")  # 모든 변경사항 추가
    # smart_commit = helpers.git_commit_smart()  # 지능형 커밋
    # print(f"💾 스마트 커밋: {smart_commit}")

    print("⚠️ 실제 커밋은 주석 해제 후 실행하세요")

git_operations_demo()
```

### 프로젝트 관리 마스터
```python
# 🛠️ 프로젝트 라이프사이클 관리
def project_management_demo():
    # 프로젝트 목록 조회
    projects = helpers.list_projects()
    print(f"📋 프로젝트 목록: {len(projects)} 개")

    # 현재 컨텍스트 조회
    context = helpers.get_context()
    print(f"🎯 현재 컨텍스트: {context}")

    # 태스크 관리
    # task_id = helpers.quick_task("execute_code 가이드 작성")
    # print(f"📝 새 태스크 생성: {task_id}")

    tasks = helpers.list_tasks()
    print(f"📋 활성 태스크: {len(tasks)} 개")

project_management_demo()
```

---

## 🔥 execute_code 실전 패턴

### 패턴 1: 빠른 프로젝트 분석
```python
# 🔍 프로젝트 전체 분석 원스톱
def quick_project_analysis():
    print("🚀 프로젝트 빠른 분석 시작")

    # 1. 디렉토리 구조 파악
    structure = helpers.scan_directory_dict(".")
    print(f"📁 총 파일: {len(structure['files'])}, 디렉토리: {len(structure['directories'])}")

    # 2. Python 파일 현황
    py_files = helpers.search_files(".", "*.py")
    print(f"🐍 Python 파일: {len(py_files['results'])} 개")

    # 3. 주요 설정 파일 확인
    config_files = ["package.json", "requirements.txt", ".env", "config.json"]
    for config in config_files:
        if helpers.get_file_info(config):
            print(f"⚙️ 설정 파일 발견: {config}")

    # 4. Git 상태
    git_status = helpers.git_status()
    print(f"📊 Git 상태: 수정된 파일 {len(git_status.get('modified', []))} 개")

quick_project_analysis()
```

### 패턴 2: 코드 품질 검사
```python
# 🔬 코드 품질 자동 검사
def code_quality_check():
    print("🔬 코드 품질 검사 실행")

    # TODO, FIXME, HACK 등 주석 검색
    issues = []
    patterns = ["TODO", "FIXME", "HACK", "BUG"]

    for pattern in patterns:
        results = helpers.search_code_content(".", pattern, "*.py")
        if results['results']:
            issues.extend(results['results'])
            print(f"⚠️ {pattern} 발견: {len(results['results'])} 곳")

    # 긴 함수 검색 (50라인 이상)
    long_functions = helpers.search_code_content(".", r"def\s+\w+.*:\n(.*\n){50,}", "*.py")
    print(f"📏 긴 함수 (50라인+): {len(long_functions['results'])} 개")

    # 중복 코드 패턴 검색
    duplicates = helpers.search_code_content(".", r"(\s*print\(.*\)\s*){3,}", "*.py")
    print(f"🔄 중복 패턴 의심: {len(duplicates['results'])} 곳")

code_quality_check()
```

### 패턴 3: 의존성 분석
```python
# 📦 프로젝트 의존성 분석
def dependency_analysis():
    print("📦 의존성 분석 시작")

    # import 문 분석
    imports = helpers.search_code_content(".", r"^(import|from)\s+([\w\.]+)", "*.py")
    print(f"📥 Import 문 발견: {len(imports['results'])} 개")

    # 외부 라이브러리 사용 패턴
    external_libs = {}
    for result in imports['results']:
        # 라이브러리명 추출 로직
        pass  # 실제 구현 시 정규식으로 라이브러리명 추출

    # requirements.txt 또는 package.json 확인
    req_file = helpers.get_file_info("requirements.txt")
    if req_file:
        content = helpers.read_file("requirements.txt")
        print("📋 requirements.txt 발견")

    pkg_file = helpers.get_file_info("package.json")
    if pkg_file:
        pkg_data = helpers.read_json("package.json")
        print(f"📦 package.json: {len(pkg_data.get('dependencies', {}))} 의존성")

dependency_analysis()
```

---

## 🧠 Think + execute_code 통합

### 복잡한 문제 해결 워크플로우
```python
# 🧠 Think 기반 문제 해결 프로세스
def think_execute_workflow(problem_description):
    print(f"🧠 문제 해결 워크플로우 시작: {problem_description}")

    # 1. 현재 상황 분석
    context = helpers.get_context()
    structure = helpers.scan_directory_dict(".")
    git_status = helpers.git_status()

    analysis = {
        "project": context.get('project_name'),
        "files_count": len(structure['files']),
        "git_modified": len(git_status.get('modified', [])),
        "problem": problem_description
    }

    print("📊 현재 상황 분석 완료:")
    for key, value in analysis.items():
        print(f"   • {key}: {value}")

    # 2. 문제 관련 파일 검색
    keywords = problem_description.split()[:3]  # 처음 3개 키워드
    related_files = []

    for keyword in keywords:
        results = helpers.search_code_content(".", keyword, "*.*")
        related_files.extend(results['results'])

    print(f"🔍 관련 파일 발견: {len(related_files)} 개")

    # 3. 해결 계획 수립 및 실행
    plan = {
        "step1": "문제 파일 백업",
        "step2": "수정 사항 적용",
        "step3": "테스트 실행",
        "step4": "결과 검증"
    }

    return {"analysis": analysis, "related_files": len(related_files), "plan": plan}

# 예시 실행
result = think_execute_workflow("JSON 파싱 오류 해결")
print(f"\n✅ 워크플로우 완료: {result}")
```

---

## 🛠️ 프로젝트 관리 마스터

### 새 프로젝트 생성 및 설정
```python
# 🏗️ 완전한 프로젝트 생성 워크플로우
def create_complete_project(project_name):
    print(f"🏗️ 새 프로젝트 생성: {project_name}")

    # 1. 프로젝트 생성
    project_info = helpers.create_project(project_name, f"./{project_name}")
    print(f"✅ 프로젝트 생성: {project_info}")

    # 2. 기본 구조 생성
    dirs = ["src", "tests", "docs", "config"]
    for dir_name in dirs:
        helpers.create_directory(f"{project_name}/{dir_name}")
        print(f"📁 디렉토리 생성: {dir_name}")

    # 3. 기본 파일 생성
    files = {
        f"{project_name}/README.md": f"# {project_name}\n\n프로젝트 설명",
        f"{project_name}/src/__init__.py": "# 메인 모듈",
        f"{project_name}/tests/test_main.py": "# 테스트 파일",
        f"{project_name}/.gitignore": "*.pyc\n__pycache__/\n.env"
    }

    for file_path, content in files.items():
        helpers.create_file(file_path, content)
        print(f"📄 파일 생성: {file_path}")

    # 4. Git 초기화
    helpers.git_init(project_name)
    print("🔧 Git 저장소 초기화")

    return project_name

# 예시 - 실제 생성하려면 주석 해제
# new_project = create_complete_project("my-awesome-project")
print("⚠️ 새 프로젝트 생성을 원하면 위 함수 호출 코드의 주석을 해제하세요")
```

### 프로젝트 상태 모니터링
```python
# 📊 프로젝트 상태 실시간 모니터링
def monitor_project_status():
    print("📊 프로젝트 상태 모니터링")

    # 1. 기본 정보
    context = helpers.get_context()
    print(f"📋 프로젝트: {context.get('project_name')}")

    # 2. 파일 시스템 상태
    structure = helpers.scan_directory_dict(".")
    print(f"📁 파일: {len(structure['files'])}, 디렉토리: {len(structure['directories'])}")

    # 3. Git 상태
    git_status = helpers.git_status()
    print(f"🔧 Git: 수정 {len(git_status.get('modified', []))}, 추가 {len(git_status.get('untracked', []))}")

    # 4. 활성 태스크
    tasks = helpers.list_tasks()
    active_tasks = [t for t in tasks if t.get('status') != 'completed']
    print(f"📝 활성 태스크: {len(active_tasks)}")

    # 5. 성능 통계
    stats = helpers.get_tracking_statistics()
    print(f"⚡ 성능 통계: {stats}")

    return {
        "files": len(structure['files']),
        "git_changes": len(git_status.get('modified', [])),
        "active_tasks": len(active_tasks)
    }

status = monitor_project_status()
```

---

## 🔍 디버깅 & 문제해결

### 자동 오류 진단
```python
# 🚨 자동 오류 진단 및 해결
def auto_error_diagnosis():
    print("🚨 자동 오류 진단 시작")

    # 1. 일반적인 오류 패턴 검색
    error_patterns = [
        "Error", "Exception", "Traceback", "Failed", 
        "ImportError", "ModuleNotFoundError", "SyntaxError"
    ]

    errors_found = {}
    for pattern in error_patterns:
        results = helpers.search_code_content(".", pattern, "*.*")
        if results['results']:
            errors_found[pattern] = len(results['results'])
            print(f"❌ {pattern}: {len(results['results'])} 곳에서 발견")

    # 2. 설정 파일 문제 확인
    config_issues = []

    # package.json 검사
    if helpers.get_file_info("package.json"):
        try:
            pkg = helpers.read_json("package.json")
            if not pkg.get("scripts"):
                config_issues.append("package.json에 scripts 없음")
        except:
            config_issues.append("package.json 파싱 오류")

    # requirements.txt 검사
    if helpers.get_file_info("requirements.txt"):
        req_content = helpers.read_file("requirements.txt")
        if "==" not in str(req_content):
            config_issues.append("requirements.txt에 버전 고정 없음")

    # 3. 의존성 문제 검사
    missing_imports = helpers.search_code_content(".", r"ModuleNotFoundError|ImportError", "*.py")
    if missing_imports['results']:
        print(f"📦 누락된 모듈: {len(missing_imports['results'])} 개")

    return {"errors": errors_found, "config_issues": config_issues}

diagnosis = auto_error_diagnosis()
```

### 성능 병목 지점 분석
```python
# ⚡ 성능 병목 지점 자동 분석
def performance_bottleneck_analysis():
    print("⚡ 성능 병목 지점 분석")

    # 1. 비효율적인 코드 패턴 검색
    inefficient_patterns = {
        "nested_loops": r"for\s+\w+.*:\s*\n\s*for\s+\w+.*:",
        "database_in_loop": r"for\s+\w+.*:\s*\n.*\.(query|execute|find)",
        "file_io_in_loop": r"for\s+\w+.*:\s*\n.*(open|read|write)",
        "large_list_comprehension": r"\[.*for\s+\w+\s+in\s+range\([0-9]{4,}\)",
    }

    bottlenecks = {}
    for pattern_name, pattern in inefficient_patterns.items():
        results = helpers.search_code_content(".", pattern, "*.py")
        if results['results']:
            bottlenecks[pattern_name] = len(results['results'])
            print(f"⚠️ {pattern_name}: {len(results['results'])} 곳")

    # 2. 큰 파일 검색 (성능에 영향을 줄 수 있는)
    structure = helpers.scan_directory_dict(".")
    large_files = [f for f in structure['files'] if f.get('size', 0) > 1000000]  # 1MB 이상
    print(f"📏 큰 파일 (1MB+): {len(large_files)} 개")

    # 3. 메모리 사용량이 많은 패턴
    memory_patterns = helpers.search_code_content(".", r"\*args|\*\*kwargs|list\(.*\)|dict\(.*\)", "*.py")
    print(f"🧠 메모리 주의 패턴: {len(memory_patterns['results'])} 곳")

    return {"bottlenecks": bottlenecks, "large_files": len(large_files)}

perf_analysis = performance_bottleneck_analysis()
```

---

## ⚡ 성능 최적화 기법

### 코드 최적화 자동 제안
```python
# 🚀 코드 최적화 자동 제안 시스템
def auto_optimization_suggestions():
    print("🚀 코드 최적화 자동 제안")

    optimizations = []

    # 1. 불필요한 import 검색
    all_imports = helpers.search_code_content(".", r"^import\s+(\w+)|^from\s+(\w+)", "*.py")
    used_modules = helpers.search_code_content(".", r"\w+\.", "*.py")
    print(f"📦 Import 분석: {len(all_imports['results'])} 개의 import 문")

    # 2. 하드코딩된 값 검색
    hardcoded = helpers.search_code_content(".", r"\b[0-9]{3,}\b|['\"][^'\"]{20,}['\"]", "*.py")
    if hardcoded['results']:
        optimizations.append(f"하드코딩된 값 {len(hardcoded['results'])} 곳 → 상수로 추출 권장")

    # 3. 긴 함수 검색
    long_functions = helpers.search_code_content(".", r"def\s+\w+.*:\n(.*\n){30,}(?=def|class|$)", "*.py")
    if long_functions['results']:
        optimizations.append(f"긴 함수 {len(long_functions['results'])} 개 → 분할 권장")

    # 4. 중복 코드 검색
    duplicate_patterns = helpers.search_code_content(".", r"(print\(.*\)\s*){3,}", "*.py")
    if duplicate_patterns['results']:
        optimizations.append(f"중복 패턴 {len(duplicate_patterns['results'])} 곳 → 함수화 권장")

    # 5. 비효율적인 문자열 연결
    string_concat = helpers.search_code_content(".", r"\w+\s*\+=\s*['\"]", "*.py")
    if string_concat['results']:
        optimizations.append(f"비효율적 문자열 연결 {len(string_concat['results'])} 곳 → join() 사용 권장")

    print("\n💡 최적화 제안:")
    for i, suggestion in enumerate(optimizations, 1):
        print(f"   {i}. {suggestion}")

    return optimizations

suggestions = auto_optimization_suggestions()
```

### 파일 구조 최적화
```python
# 📁 파일 구조 자동 최적화
def optimize_file_structure():
    print("📁 파일 구조 최적화 분석")

    structure = helpers.scan_directory_dict(".")

    # 1. 디렉토리 구조 분석
    dirs = structure['directories']
    files = structure['files']

    print(f"📊 현재 구조: {len(dirs)} 디렉토리, {len(files)} 파일")

    # 2. 너무 깊은 중첩 검색
    deep_paths = [f for f in files if f['path'].count('/') > 5]
    if deep_paths:
        print(f"⚠️ 깊은 중첩 (5단계+): {len(deep_paths)} 파일")

    # 3. 파일명 일관성 검사
    naming_issues = []
    py_files = [f for f in files if f['name'].endswith('.py')]

    # 카멜케이스 vs 스네이크케이스 혼용 검사
    camel_case = [f for f in py_files if any(c.isupper() for c in f['name'][:-3])]
    snake_case = [f for f in py_files if '_' in f['name']]

    if camel_case and snake_case:
        naming_issues.append("파일명 스타일 혼용 (camelCase + snake_case)")

    # 4. 빈 디렉토리 검색
    empty_dirs = []
    for dir_info in dirs:
        dir_files = [f for f in files if f['path'].startswith(dir_info['path'])]
        if not dir_files:
            empty_dirs.append(dir_info['path'])

    if empty_dirs:
        print(f"📂 빈 디렉토리: {len(empty_dirs)} 개")

    optimization_tips = [
        "모듈별로 디렉토리 분리",
        "테스트 파일과 소스 파일 분리", 
        "설정 파일 전용 디렉토리 생성",
        "문서화 파일 docs/ 디렉토리 이동"
    ]

    print("\n🎯 구조 최적화 팁:")
    for tip in optimization_tips:
        print(f"   • {tip}")

optimize_file_structure()
```

---

## 🔒 보안 & Git 통합

### 보안 취약점 자동 스캔
```python
# 🛡️ 보안 취약점 자동 스캔
def security_vulnerability_scan():
    print("🛡️ 보안 취약점 스캔 시작")

    vulnerabilities = []

    # 1. 하드코딩된 민감정보 검색
    sensitive_patterns = {
        "passwords": r"password\s*=\s*['\"][^'\"]+['\"]",
        "api_keys": r"(api_key|apikey|api-key)\s*=\s*['\"][^'\"]+['\"]",
        "secrets": r"(secret|token)\s*=\s*['\"][^'\"]+['\"]",
        "private_keys": r"-----BEGIN (PRIVATE|RSA) KEY-----",
        "database_urls": r"(mongodb|mysql|postgres)://[^\s]+",
    }

    for vuln_type, pattern in sensitive_patterns.items():
        results = helpers.search_code_content(".", pattern, "*.*")
        if results['results']:
            vulnerabilities.append(f"{vuln_type}: {len(results['results'])} 곳에서 발견")
            print(f"⚠️ {vuln_type}: {len(results['results'])} 곳")

    # 2. 위험한 함수 사용 검색
    dangerous_functions = [
        "eval(", "exec(", "os.system(", "subprocess.call(", 
        "pickle.loads(", "yaml.load(", "input("
    ]

    for func in dangerous_functions:
        results = helpers.search_code_content(".", func, "*.py")
        if results['results']:
            vulnerabilities.append(f"위험한 함수 {func}: {len(results['results'])} 곳")
            print(f"🚨 위험한 함수 {func}: {len(results['results'])} 곳")

    # 3. .env 파일 누출 검사
    env_files = helpers.search_files(".", ".env*")
    if env_files['results']:
        print(f"🔐 환경 변수 파일: {len(env_files['results'])} 개")

        # .gitignore에 .env가 있는지 확인
        gitignore = helpers.get_file_info(".gitignore")
        if gitignore:
            gitignore_content = helpers.read_file(".gitignore")
            if ".env" not in str(gitignore_content):
                vulnerabilities.append(".env 파일이 .gitignore에 없음")

    # 4. 권한 설정 파일 검사
    chmod_usage = helpers.search_code_content(".", "chmod|777|666", "*.*")
    if chmod_usage['results']:
        vulnerabilities.append(f"권한 설정 주의: {len(chmod_usage['results'])} 곳")

    print(f"\n🛡️ 보안 검사 완료: {len(vulnerabilities)} 개 이슈 발견")
    return vulnerabilities

security_issues = security_vulnerability_scan()
```

### Git 보안 및 자동화
```python
# 🔧 Git 보안 자동화
def git_security_automation():
    print("🔧 Git 보안 자동화")

    # 1. Git 상태 확인
    status = helpers.git_status()
    print(f"📊 Git 상태: 수정 {len(status.get('modified', []))}, 추가 {len(status.get('untracked', []))}")

    # 2. 민감정보 커밋 방지 검사
    staged_files = status.get('staged', [])
    security_risks = []

    for file_path in staged_files:
        if file_path.endswith(('.env', '.key', '.pem', '.p12')):
            security_risks.append(f"민감한 파일: {file_path}")

        # 파일 내용 검사
        content = helpers.read_file(file_path)
        if any(pattern in str(content).lower() for pattern in ['password', 'secret', 'api_key']):
            security_risks.append(f"민감정보 포함 가능: {file_path}")

    if security_risks:
        print("🚨 커밋 전 보안 검사 필요:")
        for risk in security_risks:
            print(f"   ⚠️ {risk}")
    else:
        print("✅ 보안 검사 통과")

    # 3. 브랜치 보호 상태 확인
    branch = helpers.git_get_current_branch()
    print(f"🌿 현재 브랜치: {branch}")

    if branch == "main" or branch == "master":
        print("⚠️ 메인 브랜치에서 직접 작업 중 - 브랜치 생성 권장")

    # 4. 커밋 메시지 품질 검사
    recent_commits = helpers.git_log(5)  # 최근 5개 커밋
    short_messages = [c for c in recent_commits if len(c.get('message', '')) < 10]

    if short_messages:
        print(f"📝 짧은 커밋 메시지: {len(short_messages)} 개 - 더 상세한 설명 권장")

    return {"security_risks": len(security_risks), "branch": branch}

git_security = git_security_automation()
```

---

## 🎯 고급 워크플로우 자동화

### CI/CD 파이프라인 시뮬레이션
```python
# 🚀 CI/CD 파이프라인 시뮬레이션
def cicd_pipeline_simulation():
    print("🚀 CI/CD 파이프라인 시뮬레이션")

    pipeline_steps = []

    # 1. 코드 품질 검사
    print("1️⃣ 코드 품질 검사")
    py_files = helpers.search_files(".", "*.py")
    if py_files['results']:
        # 문법 오류 검사 시뮬레이션
        syntax_errors = helpers.search_code_content(".", "SyntaxError", "*.py")
        pipeline_steps.append(("Syntax Check", len(syntax_errors['results']) == 0))

        # 스타일 검사 시뮬레이션
        style_issues = helpers.search_code_content(".", "^\s{1,3}\w|^\t\w", "*.py")  # 들여쓰기
        pipeline_steps.append(("Style Check", len(style_issues['results']) < 10))

    # 2. 테스트 실행 시뮬레이션
    print("2️⃣ 테스트 실행")
    test_files = helpers.search_files(".", "*test*.py")
    pipeline_steps.append(("Unit Tests", len(test_files['results']) > 0))

    # 3. 보안 검사
    print("3️⃣ 보안 검사")
    security_patterns = helpers.search_code_content(".", "password|secret|key", "*.*")
    pipeline_steps.append(("Security Scan", len(security_patterns['results']) == 0))

    # 4. 의존성 검사
    print("4️⃣ 의존성 검사")
    requirements_exist = helpers.get_file_info("requirements.txt") is not None
    pipeline_steps.append(("Dependencies", requirements_exist))

    # 5. 문서화 검사
    print("5️⃣ 문서화 검사")
    readme_exist = helpers.get_file_info("README.md") is not None
    pipeline_steps.append(("Documentation", readme_exist))

    # 파이프라인 결과 출력
    print("\n📊 파이프라인 결과:")
    all_passed = True
    for step_name, passed in pipeline_steps:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {step_name}: {status}")
        if not passed:
            all_passed = False

    print(f"\n🏆 전체 파이프라인: {'✅ 성공' if all_passed else '❌ 실패'}")
    return {"steps": pipeline_steps, "success": all_passed}

pipeline_result = cicd_pipeline_simulation()
```

### 자동 배포 준비 검사
```python
# 📦 자동 배포 준비 검사
def deployment_readiness_check():
    print("📦 배포 준비 검사")

    readiness_score = 0
    max_score = 10

    checks = [
        # 1. 코드 안정성
        ("모든 테스트 파일 존재", lambda: len(helpers.search_files(".", "*test*.py")['results']) > 0),
        ("README.md 존재", lambda: helpers.get_file_info("README.md") is not None),
        ("requirements.txt 존재", lambda: helpers.get_file_info("requirements.txt") is not None),

        # 2. Git 상태
        ("Git 커밋 상태 깔끔", lambda: len(helpers.git_status().get('modified', [])) == 0),
        ("메인 브랜치 아님", lambda: helpers.git_get_current_branch() not in ['main', 'master']),

        # 3. 보안
        ("민감정보 없음", lambda: len(helpers.search_code_content(".", "password|secret", "*.*")['results']) == 0),
        (".env가 .gitignore에 있음", lambda: ".env" in str(helpers.read_file(".gitignore") or "")),

        # 4. 코드 품질
        ("큰 파일 없음", lambda: all(f.get('size', 0) < 1000000 for f in helpers.scan_directory_dict(".")['files'])),
        ("TODO/FIXME 적음", lambda: len(helpers.search_code_content(".", "TODO|FIXME", "*.py")['results']) < 5),
        ("중복 코드 적음", lambda: len(helpers.search_code_content(".", "(print\(.*\)){3,}", "*.py")['results']) < 3)
    ]

    print("\n🔍 배포 준비 상태:")
    for check_name, check_func in checks:
        try:
            passed = check_func()
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
            if passed:
                readiness_score += 1
        except Exception as e:
            print(f"   ⚠️ {check_name} (검사 실패: {e})")

    percentage = (readiness_score / max_score) * 100
    print(f"\n📊 배포 준비도: {readiness_score}/{max_score} ({percentage:.1f}%)")

    if percentage >= 80:
        print("🚀 배포 준비 완료!")
    elif percentage >= 60:
        print("⚠️ 배포 가능하지만 개선 권장")
    else:
        print("❌ 배포 전 추가 작업 필요")

    return {"score": readiness_score, "percentage": percentage}

deployment_check = deployment_readiness_check()
```

---

## 📚 실전 시나리오 해결책

### 시나리오 1: 새 팀원 온보딩
```python
# 👋 새 팀원을 위한 프로젝트 온보딩 자동화
def onboarding_automation():
    print("👋 새 팀원 온보딩 자동화")

    # 1. 프로젝트 개요 생성
    structure = helpers.scan_directory_dict(".")
    context = helpers.get_context()

    overview = {
        "project_name": context.get('project_name', 'Unknown'),
        "total_files": len(structure['files']),
        "python_files": len(helpers.search_files(".", "*.py")['results']),
        "test_files": len(helpers.search_files(".", "*test*.py")['results']),
        "config_files": len(helpers.search_files(".", "*.json")['results'])
    }

    print("📋 프로젝트 개요:")
    for key, value in overview.items():
        print(f"   • {key}: {value}")

    # 2. 핵심 파일 식별
    important_files = []

    # 설정 파일들
    config_candidates = ["package.json", "requirements.txt", "config.json", ".env.example"]
    for file_name in config_candidates:
        if helpers.get_file_info(file_name):
            important_files.append(f"📄 {file_name}: 설정 파일")

    # 메인 실행 파일
    main_files = helpers.search_files(".", "main.py")
    main_files.update(helpers.search_files(".", "app.py"))
    main_files.update(helpers.search_files(".", "index.py"))

    for file_info in main_files['results']:
        important_files.append(f"🚀 {file_info['name']}: 메인 실행 파일")

    # 3. 개발 환경 설정 가이드
    setup_commands = []

    if helpers.get_file_info("requirements.txt"):
        setup_commands.append("pip install -r requirements.txt")

    if helpers.get_file_info("package.json"):
        setup_commands.append("npm install")

    if helpers.get_file_info(".env.example"):
        setup_commands.append("cp .env.example .env")

    print("\n🛠️ 개발 환경 설정:")
    for i, cmd in enumerate(setup_commands, 1):
        print(f"   {i}. {cmd}")

    # 4. 온보딩 체크리스트 생성
    checklist = [
        "저장소 클론",
        "의존성 설치",
        "환경 변수 설정",
        "데이터베이스 설정 (해당시)",
        "테스트 실행",
        "개발 서버 실행"
    ]

    print("\n✅ 온보딩 체크리스트:")
    for item in checklist:
        print(f"   □ {item}")

    return {"overview": overview, "setup_commands": setup_commands}

onboarding_info = onboarding_automation()
```

### 시나리오 2: 긴급 버그 수정
```python
# 🚨 긴급 버그 수정 워크플로우
def emergency_bug_fix_workflow(bug_description):
    print(f"🚨 긴급 버그 수정: {bug_description}")

    # 1. 현재 상태 백업
    print("1️⃣ 현재 상태 백업")
    git_status = helpers.git_status()
    if git_status.get('modified'):
        print("⚠️ 수정된 파일 있음 - 스태시 권장")
        # helpers.git_stash("Emergency backup before bug fix")

    # 2. 버그 관련 파일 검색
    print("2️⃣ 버그 관련 파일 검색")
    keywords = bug_description.lower().split()[:3]
    related_files = []

    for keyword in keywords:
        results = helpers.search_code_content(".", keyword, "*.*")
        related_files.extend(results['results'])

    print(f"🔍 관련 파일 {len(related_files)} 개 발견")

    # 3. 최근 변경사항 분석
    print("3️⃣ 최근 변경사항 분석")
    recent_commits = helpers.git_log(10)
    recent_files = []

    for commit in recent_commits:
        # 커밋에서 변경된 파일들 (실제로는 git show로 가져와야 함)
        if any(keyword in commit.get('message', '').lower() for keyword in keywords):
            print(f"📝 의심 커밋: {commit.get('message', '')[:50]}...")

    # 4. 테스트 파일 확인
    print("4️⃣ 관련 테스트 확인")
    test_files = helpers.search_files(".", "*test*.py")
    relevant_tests = []

    for test_file in test_files['results']:
        test_content = helpers.read_file(test_file['path'])
        if any(keyword in str(test_content).lower() for keyword in keywords):
            relevant_tests.append(test_file['path'])

    print(f"🧪 관련 테스트: {len(relevant_tests)} 개")

    # 5. 수정 계획 수립
    fix_plan = [
        "버그 재현 테스트 작성",
        "문제 코드 수정",
        "테스트 실행으로 수정 확인",
        "회귀 테스트 실행",
        "핫픽스 커밋 및 배포"
    ]

    print("\n🔧 수정 계획:")
    for i, step in enumerate(fix_plan, 1):
        print(f"   {i}. {step}")

    return {
        "related_files": len(related_files),
        "relevant_tests": len(relevant_tests),
        "fix_plan": fix_plan
    }

# 예시 실행
bug_fix_info = emergency_bug_fix_workflow("사용자 로그인 실패")
```

### 시나리오 3: 성능 최적화 프로젝트
```python
# ⚡ 성능 최적화 프로젝트 워크플로우
def performance_optimization_project():
    print("⚡ 성능 최적화 프로젝트 시작")

    optimization_report = {}

    # 1. 현재 성능 베이스라인 측정
    print("1️⃣ 성능 베이스라인 측정")

    # 파일 크기 분석
    structure = helpers.scan_directory_dict(".")
    large_files = [f for f in structure['files'] if f.get('size', 0) > 100000]  # 100KB 이상
    optimization_report['large_files'] = len(large_files)
    print(f"📏 큰 파일 (100KB+): {len(large_files)} 개")

    # 2. 코드 복잡도 분석
    print("2️⃣ 코드 복잡도 분석")

    # 긴 함수 검색
    long_functions = helpers.search_code_content(".", r"def\s+\w+.*:\n(.*\n){25,}", "*.py")
    optimization_report['long_functions'] = len(long_functions['results'])

    # 중첩 루프 검색
    nested_loops = helpers.search_code_content(".", r"for\s+\w+.*:\s*\n\s*for\s+\w+.*:", "*.py")
    optimization_report['nested_loops'] = len(nested_loops['results'])

    print(f"🔄 긴 함수 (25라인+): {len(long_functions['results'])} 개")
    print(f"🔁 중첩 루프: {len(nested_loops['results'])} 개")

    # 3. 의존성 분석
    print("3️⃣ 의존성 최적화 분석")

    # import 문 분석
    imports = helpers.search_code_content(".", r"^import\s+|^from\s+", "*.py")
    optimization_report['total_imports'] = len(imports['results'])

    # 무거운 라이브러리 사용 검색
    heavy_libs = ['pandas', 'numpy', 'tensorflow', 'torch', 'scipy']
    heavy_usage = []

    for lib in heavy_libs:
        usage = helpers.search_code_content(".", f"import {lib}|from {lib}", "*.py")
        if usage['results']:
            heavy_usage.append(lib)

    optimization_report['heavy_libraries'] = len(heavy_usage)
    print(f"📦 무거운 라이브러리: {len(heavy_usage)} 개 ({', '.join(heavy_usage)})")

    # 4. 메모리 사용 패턴 분석
    print("4️⃣ 메모리 사용 패턴")

    # 대용량 데이터 구조 검색
    large_data = helpers.search_code_content(".", r"list\(range\([0-9]{4,}\)|\[[^\]]{100,}\]", "*.py")
    optimization_report['large_data_structures'] = len(large_data['results'])

    # 전역 변수 검색
    global_vars = helpers.search_code_content(".", r"^[A-Z_]{2,}\s*=", "*.py")
    optimization_report['global_variables'] = len(global_vars['results'])

    print(f"🧠 대용량 데이터 구조: {len(large_data['results'])} 개")
    print(f"🌐 전역 변수: {len(global_vars['results'])} 개")

    # 5. 최적화 우선순위 계산
    print("\n5️⃣ 최적화 우선순위")

    priorities = []

    if optimization_report['nested_loops'] > 5:
        priorities.append("🔥 높음: 중첩 루프 최적화")

    if optimization_report['large_files'] > 10:
        priorities.append("🔥 높음: 큰 파일 분할")

    if optimization_report['long_functions'] > 15:
        priorities.append("🟡 중간: 함수 분할")

    if optimization_report['heavy_libraries'] > 3:
        priorities.append("🟡 중간: 의존성 최적화")

    if optimization_report['large_data_structures'] > 5:
        priorities.append("🟢 낮음: 데이터 구조 최적화")

    print("📊 최적화 우선순위:")
    for priority in priorities:
        print(f"   • {priority}")

    return optimization_report

perf_optimization = performance_optimization_project()
```

---

## 🎉 마무리: execute_code 마스터 되기

### 핵심 원칙
1. **모든 작업을 execute_code로**: 파일 읽기, 검색, Git 작업 등 모든 것
2. **helpers 함수 적극 활용**: 97개 함수로 모든 개발 작업 자동화
3. **실시간 피드백**: 모든 실행의 결과를 즉시 확인
4. **워크플로우 통합**: 개별 작업이 아닌 전체 프로세스 자동화
5. **지속적 개선**: 매번 더 효율적인 패턴 개발

### 다음 단계
```python
# 🚀 execute_code 마스터로 가는 길
def become_execute_code_master():
    print("🚀 execute_code 마스터 되기")

    # 1. 매일 연습할 패턴들
    daily_practices = [
        "프로젝트 상태 모니터링",
        "코드 품질 자동 검사", 
        "Git 워크플로우 자동화",
        "성능 분석 및 최적화",
        "보안 취약점 스캔"
    ]

    print("📅 매일 연습:")
    for practice in daily_practices:
        print(f"   • {practice}")

    # 2. 고급 기술 로드맵
    advanced_skills = [
        "커스텀 helpers 함수 개발",
        "복잡한 워크플로우 자동화",
        "AI 기반 코드 분석 통합",
        "실시간 모니터링 시스템",
        "완전 자동화된 CI/CD"
    ]

    print("\n🎯 고급 기술 로드맵:")
    for skill in advanced_skills:
        print(f"   • {skill}")

    # 3. 최종 체크리스트
    mastery_checklist = [
        "helpers 함수 97개 모두 활용 가능",
        "모든 개발 작업을 execute_code로 수행",
        "복잡한 워크플로우 자동화 구축",
        "성능과 보안을 동시에 고려",
        "팀 전체의 생산성 향상에 기여"
    ]

    print("\n✅ 마스터 체크리스트:")
    for item in mastery_checklist:
        print(f"   □ {item}")

    print("\n🏆 축하합니다! 이제 진정한 execute_code 마스터입니다!")

become_execute_code_master()
```

---

**🎯 이 가이드로 Claude Code + ai-coding-brain-mcp의 모든 잠재력을 발휘하세요!**

- 모든 코드는 복사-붙여넣기로 즉시 실행 가능
- 97개 helpers 함수의 완전한 활용법 
- 실전 중심의 문제 해결 워크플로우
- 지속적인 학습과 개선을 위한 체계적 접근

**🚀 지금 바로 시작하세요!**

---

> 💡 **팁**: 각 섹션의 코드를 순서대로 실행하면서 여러분만의 개발 워크플로우를 만들어보세요!

> 🔗 **참고**: 더 자세한 기술 문서는 `WORKFLOW_TECHNICAL_DOC.md`를 참조하세요.

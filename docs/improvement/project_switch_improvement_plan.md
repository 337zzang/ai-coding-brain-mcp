# 📋 프로젝트 전환 시스템 개선 방안

## 🔴 현재 시스템의 문제점

### 1. 불완전한 정보 표시
- `/flow project-name` 명령 시 프로젝트 경로와 이름만 간단히 표시
- `/a` 명령으로 생성된 `readme.md`, `file_directory.md` 파일을 자동으로 읽지 않음
- 프로젝트의 핵심 정보(기술 스택, 주요 기능, 구조)가 stdout으로 출력되지 않음

### 2. 정보 파편화
- 프로젝트 정보가 여러 곳에 분산되어 있음
  - 기본 정보: flow_project_with_workflow() 반환값
  - 프로젝트 설명: readme.md
  - 구조 정보: file_directory.md
  - Git 상태: git_status()
  - Flow 상태: flow("/status")

### 3. 사용자 경험 저하
- 프로젝트 전환 후 추가 명령어를 여러 번 실행해야 전체 상황 파악 가능
- 중요한 정보를 놓치기 쉬움
- 컨텍스트 전환 시 필요한 정보가 즉시 제공되지 않음

## 🟢 개선 방안

### 1. 통합 정보 표시 함수 구현
```python
def enhanced_project_switch(project_name):
    """향상된 프로젝트 전환 함수"""

    # 1단계: 기본 프로젝트 전환
    result = h.flow_project_with_workflow(project_name)
    if not result['ok']:
        return result

    # 2단계: 프로젝트 문서 자동 읽기 및 출력
    project_path = result['data']['project']['path']

    # README.md 출력 (프로젝트 개요)
    readme_path = os.path.join(project_path, "readme.md")
    if h.exists(readme_path)['data']:
        readme_content = h.read(readme_path, length=50)
        if readme_content['ok']:
            print("\n📖 README.md 내용:")
            print("=" * 70)
            print(readme_content['data'])

    # FILE_DIRECTORY.md 출력 (구조)
    file_dir_path = os.path.join(project_path, "file_directory.md")
    if h.exists(file_dir_path)['data']:
        file_dir_content = h.read(file_dir_path, length=100)
        if file_dir_content['ok']:
            print("\n📁 프로젝트 구조:")
            print("=" * 70)
            print(file_dir_content['data'])

    # 3단계: 추가 컨텍스트 정보
    # Git 상태
    git_status = h.git_status()
    if git_status['ok']:
        print("\n🔀 Git 상태:")
        print(f"브랜치: {git_status['data']['branch']}")
        print(f"변경 파일: {git_status['data']['count']}개")

    # Flow 상태
    flow_status = h.flow("/status")

    # 4단계: 의존성 정보 (package.json, requirements.txt)
    package_json = os.path.join(project_path, "package.json")
    if h.exists(package_json)['data']:
        pkg_data = h.read_json(package_json)
        if pkg_data['ok']:
            print("\n📦 Node.js 프로젝트 정보:")
            print(f"버전: {pkg_data['data'].get('version')}")
            print(f"설명: {pkg_data['data'].get('description')}")

    return result
```

### 2. 자동화된 프로젝트 분석
- 프로젝트 전환 시 `/a` 명령 자동 실행 옵션
- 문서가 오래된 경우 자동 재생성
- 변경사항 감지 및 알림

### 3. 표준화된 출력 형식
```
================================================================================
🚀 프로젝트 전환: [프로젝트명]
================================================================================

📌 기본 정보:
- 경로: /path/to/project
- 타입: Node.js/Python/Hybrid
- Git: 활성화됨
- 최종 수정: 2025-08-02

📖 프로젝트 개요: (from readme.md)
[프로젝트 설명 요약]
[주요 기능 목록]
[기술 스택]

📁 프로젝트 구조: (from file_directory.md)
[주요 디렉토리 트리]
[파일 통계]

🔀 Git 상태:
- 브랜치: master
- 변경 파일: 2개
- 최근 커밋: "feat: 새 기능 추가"

📊 Flow 시스템:
- 활성 Plan: 1개
- 진행 중 Task: 5개
- 다음 작업: "Task 3: 스마트 대기 기능"

💡 권장 작업:
- [ ] 변경된 파일 커밋
- [ ] Task 3 시작
- [ ] 문서 업데이트
================================================================================
```

### 4. 구현 위치 및 방법
1. **ai_helpers_new/project.py** 수정
   - `flow_project_with_workflow()` 함수 확장
   - 문서 읽기 로직 추가

2. **simple_flow_commands.py** 수정
   - `/project` 명령 처리 부분 개선
   - stdout 출력 로직 추가

3. **새로운 헬퍼 함수 추가**
   - `show_project_context()`: 전체 컨텍스트 표시
   - `auto_analyze_project()`: 자동 분석 실행

### 5. 설정 옵션
```python
PROJECT_SWITCH_OPTIONS = {
    "auto_read_docs": True,      # 문서 자동 읽기
    "max_readme_lines": 50,      # README 최대 출력 줄 수
    "max_structure_lines": 100,  # 구조 문서 최대 출력 줄 수
    "show_git_status": True,     # Git 상태 표시
    "show_flow_status": True,    # Flow 상태 표시
    "show_dependencies": True,   # 의존성 정보 표시
    "auto_analyze": False        # /a 자동 실행
}
```

## 📈 기대 효과

1. **즉각적인 컨텍스트 파악**
   - 프로젝트 전환 즉시 모든 필요 정보 확인
   - 추가 명령어 실행 불필요

2. **작업 효율성 향상**
   - 중요 정보를 놓치지 않음
   - 빠른 의사결정 가능

3. **일관된 사용자 경험**
   - 모든 프로젝트에서 동일한 형식으로 정보 제공
   - 예측 가능한 동작

## 🔧 구현 우선순위

1. **Phase 1** (즉시 구현 가능)
   - readme.md, file_directory.md 자동 읽기
   - Git 상태 통합 표시

2. **Phase 2** (중기)
   - Flow 상태 통합
   - 의존성 정보 표시

3. **Phase 3** (장기)
   - 자동 분석 옵션
   - 사용자 설정 지원

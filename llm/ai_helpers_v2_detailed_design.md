
# AI Helpers v2.0 개선 상세 설계 문서

## 📋 개요
본 문서는 o3 AI의 심층 분석을 바탕으로 작성된 AI Helpers v2.0의 개선 설계입니다.

## 1. search_code max_results 개선

### 1.1 문제 분석 (o3 분석 기반)
- **근본 원인**: 중첩 루프에서 break가 내부 루프만 종료
- **증상**: max_results=3 설정 시 4개 반환 등 부정확한 제한
- **영향**: API 신뢰성 저하

### 1.2 해결 방안
```python
def search_code(pattern: str, path: str = ".", file_pattern: str = "*", 
                max_results: int = 100) -> Dict[str, Any]:
    try:
        regex = re.compile(pattern, re.IGNORECASE)
        matches = []
        files_searched = 0

        files_result = search_files(file_pattern, path, recursive=True)
        if not files_result['ok']:
            return files_result

        for file_path in files_result['data']:
            # 조기 종료 체크 (파일 열기 전)
            if len(matches) >= max_results:
                break

            full_path = os.path.join(path, file_path)

            # 바이너리 파일 스킵
            if full_path.endswith(('.pyc', '.pyo', '.so', '.dll', '.exe')):
                continue

            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    files_searched += 1

                    for line_num, line in enumerate(f, 1):
                        match = regex.search(line)
                        if match:
                            matches.append({
                                'file': file_path,
                                'line': line_num,
                                'text': line.rstrip(),
                                'match': match.group(0)
                            })

                            # 정확한 수에 도달하면 즉시 반환
                            if len(matches) == max_results:
                                return ok(
                                    matches,
                                    count=len(matches),
                                    files_searched=files_searched,
                                    truncated=True
                                )
            except:
                continue

        return ok(
            matches,
            count=len(matches),
            files_searched=files_searched,
            truncated=False
        )
    except Exception as e:
        return err(f"Search failed: {str(e)}")
```

### 1.3 테스트 케이스
```python
def test_search_max_results_exact():
    # 정확히 max_results 개수만 반환하는지 테스트
    result = search_code("def", "test_data/", max_results=5)
    assert result['ok']
    assert len(result['data']) == 5
    assert result['truncated'] == True

def test_search_max_results_boundary():
    # 경계값 테스트
    for max_val in [0, 1, 100, 1000]:
        result = search_code("def", ".", max_results=max_val)
        assert len(result['data']) <= max_val

def test_search_max_results_file_boundary():
    # 파일 경계에서도 정확한 제한
    # 여러 파일에 걸쳐 있을 때도 정확히 제한
    pass
```

## 2. WorkflowManager Dict 반환 리팩토링

### 2.1 설계 원칙 (o3 분석 기반)
1. **통일성**: 모든 메서드가 `Dict[str, Any]` 반환
2. **하위호환성**: verbose 옵션으로 기존 출력 유지
3. **확장성**: 향후 기능 추가를 위한 구조화된 데이터

### 2.2 구현 전략
```python
class WorkflowManager:
    def __init__(self, project_path: str = ".", verbose: bool = True):
        # 기존 초기화 코드...
        self.verbose = verbose

    def _format_for_display(self, data: Dict[str, Any], template: str) -> str:
        """데이터를 표시용 문자열로 포맷"""
        return template.format(**data)

    def _print_if_verbose(self, message: str):
        """verbose 모드일 때만 출력"""
        if self.verbose:
            print(message)

    def _show_status(self) -> Dict[str, Any]:
        """워크플로우 상태 표시"""
        self._ensure_workflow_exists()

        # 데이터 수집
        tasks = self.workflow.get("tasks", {})
        completed_tasks = [t for t in tasks.values() if t.get("status") == "completed"]
        active_tasks = [t for t in tasks.values() if t.get("status") == "active"]

        data = {
            "project": self.workflow.get('project_name', self.project_path.name),
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "active_tasks": len(active_tasks),
            "progress_percentage": (len(completed_tasks) / len(tasks) * 100) if tasks else 0,
            "current_task": active_tasks[0] if active_tasks else None,
            "tasks": tasks
        }

        # 선택적 출력
        if self.verbose:
            display = f"""📊 워크플로우 상태
프로젝트: {data['project']}
진행률: {data['completed_tasks']}/{data['total_tasks']} ({data['progress_percentage']:.0f}%)
현재 태스크: {data['current_task']['name'] if data['current_task'] else '없음'}"""
            print(display)

        return ok(data)
```

### 2.3 영향받는 메서드 목록 및 변환 계획
| 메서드 | 현재 반환 | 목표 반환 | 우선순위 |
|--------|----------|----------|----------|
| _show_status | str | Dict[str, Any] | 높음 |
| _show_help | str | Dict[str, Any] | 중간 |
| _list_tasks | str | Dict[str, Any] | 높음 |
| _show_report | str | Dict[str, Any] | 중간 |
| _handle_task_command | str | Dict[str, Any] | 높음 |

## 3. 포괄적 테스트 전략

### 3.1 테스트 구조 (o3 권장사항 반영)
```
test/
├── __init__.py
├── conftest.py              # pytest fixtures
├── unit/                    # 단위 테스트
│   ├── __init__.py
│   ├── test_file_ops.py     # file.py 테스트
│   ├── test_search.py       # search.py 테스트
│   ├── test_workflow.py     # workflow_manager.py 테스트
│   ├── test_llm.py          # llm.py 테스트
│   └── test_helpers.py      # 기타 헬퍼 함수
├── integration/             # 통합 테스트
│   ├── __init__.py
│   ├── test_ai_flow.py      # 전체 플로우 테스트
│   └── test_error_cases.py  # 에러 시나리오
└── performance/             # 성능 테스트
    ├── __init__.py
    └── test_large_files.py  # 대용량 파일 처리
```

### 3.2 테스트 작성 가이드라인
```python
# conftest.py
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_project():
    """임시 프로젝트 디렉토리 생성"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        # 기본 구조 생성
        (project_path / "src").mkdir()
        (project_path / "test").mkdir()
        yield project_path

@pytest.fixture
def sample_files(temp_project):
    """테스트용 샘플 파일 생성"""
    files = {
        "src/main.py": "def main():\n    pass\n",
        "src/utils.py": "def helper():\n    return True\n",
        "test/test_main.py": "def test_main():\n    assert True\n"
    }

    for path, content in files.items():
        file_path = temp_project / path
        file_path.parent.mkdir(exist_ok=True)
        file_path.write_text(content)

    return temp_project
```

## 4. API 일관성 개선 (o3 종합 분석)

### 4.1 표준 반환 형식
```python
# 성공
{
    "ok": True,
    "data": Any,  # 실제 데이터
    **metadata   # 추가 메타데이터 (count, truncated 등)
}

# 실패
{
    "ok": False,
    "error": str,  # 에러 메시지
    "error_type": str  # 에러 타입 (optional)
}
```

### 4.2 명명 규칙
- 함수명: snake_case (동사_명사 형태)
- 파라미터: snake_case
- 반환값 키: snake_case
- 클래스명: PascalCase

### 4.3 에러 처리 표준
```python
def standard_function(param: str) -> Dict[str, Any]:
    """표준 함수 템플릿

    Args:
        param: 파라미터 설명

    Returns:
        성공: {'ok': True, 'data': 결과}
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        # 파라미터 검증
        if not param:
            return err("param is required")

        # 실제 로직
        result = do_something(param)

        # 성공 반환
        return ok(result, extra_info="추가정보")

    except SpecificError as e:
        return err(f"Specific error: {e}", error_type="specific")
    except Exception as e:
        return err(f"Unexpected error: {e}", error_type="unknown")
```

## 5. 구현 로드맵

### Phase 1: 긴급 수정 (1일)
- [ ] search_code max_results 수정
- [ ] 기본 테스트 케이스 작성
- [ ] WorkflowManager._show_status dict 반환

### Phase 2: 핵심 개선 (3일)
- [ ] WorkflowManager 모든 메서드 dict 반환
- [ ] 단위 테스트 구조 구축
- [ ] 주요 함수 단위 테스트 작성

### Phase 3: 전체 리팩토링 (1주)
- [ ] 모든 함수 API 일관성 검토
- [ ] 통합 테스트 작성
- [ ] 성능 테스트 및 최적화
- [ ] 문서화 업데이트

## 6. 위험 요소 및 대응 방안

### 6.1 하위 호환성
- **위험**: 기존 코드가 문자열 반환 기대
- **대응**: verbose 모드 기본값 True로 유지

### 6.2 성능 영향
- **위험**: dict 생성 오버헤드
- **대응**: 필요시 캐싱 적용

### 6.3 테스트 커버리지
- **위험**: 모든 엣지 케이스 커버 어려움
- **대응**: 점진적 테스트 추가, CI/CD 통합

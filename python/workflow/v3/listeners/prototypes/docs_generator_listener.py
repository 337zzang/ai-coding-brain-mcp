
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from python.workflow.v3.listeners.base import BaseEventListener
from python.workflow.v3.models import EventType, WorkflowEvent

class DocsGeneratorListener(BaseEventListener):
    """태스크 완료 시 자동 문서 생성 리스너"""

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.docs_dir = Path("docs/tasks")
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def handle_event(self, event: WorkflowEvent) -> None:
        """이벤트 처리"""
        if event.type == EventType.TASK_COMPLETED:
            self._generate_task_docs(event)

    def _generate_task_docs(self, event: WorkflowEvent) -> None:
        """태스크 문서 생성"""
        task_id = event.task_id
        details = event.details or {}

        # 문서 내용 구성
        doc_content = f"""# Task Documentation: {details.get('title', 'Untitled')}

## 기본 정보
- **Task ID**: {task_id}
- **완료 시간**: {event.timestamp}
- **소요 시간**: {details.get('duration', 'N/A')}

## 작업 내용
{details.get('notes', '작업 내용이 기록되지 않았습니다.')}

## 변경 사항
### 생성된 파일
{self._format_file_list(details.get('files_created', []))}

### 수정된 파일  
{self._format_file_list(details.get('files_modified', []))}

## 코드 스니펫
```python
# 주요 코드 변경사항
{details.get('code_snippet', '# 코드 스니펫이 없습니다.')}
```

## 테스트 결과
{self._format_test_results(details.get('test_results', {}))}

---
*자동 생성됨: {datetime.now().isoformat()}*
"""

        # 파일 저장
        doc_path = self.docs_dir / f"{task_id}.md"
        doc_path.write_text(doc_content, encoding='utf-8')
        print(f"📄 문서 생성됨: {doc_path}")

    def _format_file_list(self, files: list) -> str:
        if not files:
            return "- 없음"
        return "\n".join(f"- {file}" for file in files)

    def _format_test_results(self, results: dict) -> str:
        if not results:
            return "테스트 결과가 없습니다."
        return f"""
- **통과**: {results.get('passed', 0)}
- **실패**: {results.get('failed', 0)}  
- **커버리지**: {results.get('coverage', 'N/A')}
"""

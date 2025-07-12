"""
DocsGeneratorListener - 태스크 완료 시 자동 문서 생성
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import json
import logging

from ..models import EventType, WorkflowEvent
from .base import BaseEventListener

logger = logging.getLogger(__name__)


class DocsGeneratorListener(BaseEventListener):
    """태스크 완료 시 자동 문서 생성 리스너"""

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.docs_dir = Path("docs/tasks")
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.generated_docs = []  # 생성된 문서 추적

    def get_subscribed_events(self) -> List[EventType]:
        """구독할 이벤트 타입"""
        return [
            EventType.TASK_COMPLETED,
            EventType.PLAN_COMPLETED
        ]

    def handle_event(self, event: WorkflowEvent) -> None:
        """이벤트 처리"""
        if not self.enabled:
            return

        try:
            if event.type == EventType.TASK_COMPLETED:
                self._generate_task_docs(event)
            elif event.type == EventType.PLAN_COMPLETED:
                self._generate_plan_summary(event)
        except Exception as e:
            logger.error(f"DocsGeneratorListener 오류: {e}")

    def _generate_task_docs(self, event: WorkflowEvent) -> None:
        """태스크 문서 생성"""
        task_id = event.task_id
        details = event.details or {}

        # task_context.json에서 추가 정보 가져오기
        task_context_path = Path("memory/task_context.json")
        task_context = {}

        if task_context_path.exists():
            try:
                with open(task_context_path, 'r', encoding='utf-8') as f:
                    all_contexts = json.load(f)
                    task_context = all_contexts.get('tasks', {}).get(task_id, {})
            except Exception as e:
                logger.debug(f"task_context 로드 실패: {e}")

        # 문서 내용 구성
        doc_content = f"""# Task Documentation: {details.get('title', task_context.get('task_title', 'Untitled'))}

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Task ID**: {task_id}
**Status**: Completed ✅

## 📋 작업 내용

{details.get('notes', details.get('note', '작업 내용이 기록되지 않았습니다.'))}

## 🕐 시간 정보

- **시작**: {task_context.get('started_at', event.timestamp)}
- **완료**: {event.timestamp}
- **소요 시간**: {details.get('duration', 'N/A')}

## 📁 변경 사항

### 생성된 파일
{self._format_file_list(task_context.get('files_created', []))}

### 수정된 파일
{self._format_file_list(task_context.get('files_modified', []))}

## 💻 코드 변경사항

{self._format_code_changes(task_context)}

## 🧪 테스트 결과

{self._format_test_results(task_context.get('test_results', {}))}

## 📝 추가 정보

{self._format_additional_info(task_context, details)}

---
*이 문서는 DocsGeneratorListener에 의해 자동 생성되었습니다.*
"""

        # 파일명 생성 (날짜_태스크제목)
        safe_title = details.get('title', 'task').lower()
        safe_title = ''.join(c if c.isalnum() or c in '-_' else '_' for c in safe_title)
        date_str = datetime.now().strftime('%Y%m%d')
        doc_filename = f"{date_str}_{safe_title}_{task_id[:8]}.md"

        # 파일 저장
        doc_path = self.docs_dir / doc_filename
        doc_path.write_text(doc_content, encoding='utf-8')

        # 생성된 문서 추적
        self.generated_docs.append(str(doc_path))

        logger.info(f"📄 태스크 문서 생성: {doc_path}")
        print(f"\n📄 태스크 문서 생성됨: {doc_path}")

    def _generate_plan_summary(self, event: WorkflowEvent) -> None:
        """플랜 완료 시 요약 문서 생성"""
        plan_id = event.plan_id
        details = event.details or {}

        summary_content = f"""# Plan Summary: {details.get('name', 'Untitled Plan')}

**Plan ID**: {plan_id}
**Completed**: {event.timestamp}

## 📊 통계

- **총 태스크**: {details.get('total_tasks', 0)}
- **완료된 태스크**: {details.get('completed_tasks', 0)}
- **성공률**: {details.get('success_rate', 100)}%

## 📄 생성된 문서

{self._format_generated_docs()}

## 🔍 주요 성과

{details.get('achievements', '- 플랜이 성공적으로 완료되었습니다.')}

---
*플랜 요약 문서 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        # 요약 문서 저장
        summary_path = self.docs_dir.parent / f"plan_summary_{plan_id[:8]}.md"
        summary_path.write_text(summary_content, encoding='utf-8')

        print(f"\n📊 플랜 요약 문서 생성됨: {summary_path}")

    def _format_file_list(self, files: list) -> str:
        """파일 목록 포맷팅"""
        if not files:
            return "- 없음"
        return "\n".join(f"- `{file}`" for file in files)

    def _format_code_changes(self, context: dict) -> str:
        """코드 변경사항 포맷팅"""
        code_snippet = context.get('code_snippet', '')
        if code_snippet:
            return f"```python\n{code_snippet}\n```"

        # 코드 변경 요약
        changes = context.get('code_changes', [])
        if changes:
            return "\n".join(f"- {change}" for change in changes)

        return "코드 변경사항이 기록되지 않았습니다."

    def _format_test_results(self, results: dict) -> str:
        """테스트 결과 포맷팅"""
        if not results:
            return "테스트 결과가 없습니다."

        output = []
        if 'passed' in results:
            output.append(f"- ✅ 통과: {results['passed']}")
        if 'failed' in results:
            output.append(f"- ❌ 실패: {results['failed']}")
        if 'coverage' in results:
            output.append(f"- 📊 커버리지: {results['coverage']}")

        return "\n".join(output) if output else "테스트 정보 없음"

    def _format_additional_info(self, context: dict, details: dict) -> str:
        """추가 정보 포맷팅"""
        info = []

        # 오류 정보
        if context.get('errors'):
            info.append("### ⚠️ 발생한 오류")
            for error in context['errors']:
                info.append(f"- {error}")

        # 성능 메트릭
        if context.get('performance_metrics'):
            info.append("\n### 📈 성능 메트릭")
            for key, value in context['performance_metrics'].items():
                info.append(f"- {key}: {value}")

        # 기타 노트
        if details.get('additional_notes'):
            info.append("\n### 📌 추가 노트")
            info.append(details['additional_notes'])

        return "\n".join(info) if info else "추가 정보 없음"

    def _format_generated_docs(self) -> str:
        """생성된 문서 목록"""
        if not self.generated_docs:
            return "- 생성된 문서가 없습니다."

        return "\n".join(f"- {Path(doc).name}" for doc in self.generated_docs[-10:])

    def get_generated_docs_count(self) -> int:
        """생성된 문서 수 반환"""
        return len(self.generated_docs)

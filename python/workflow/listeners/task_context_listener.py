"""
TaskContextListener - 태스크 시작 시 관련 문서 및 컨텍스트 제공
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from ..models import EventType, WorkflowEvent
from .base import BaseEventListener

logger = logging.getLogger(__name__)


class TaskContextListener(BaseEventListener):
    """태스크 시작 시 관련 문서와 컨텍스트를 제공하는 리스너"""

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.task_contexts = {}  # 태스크별 컨텍스트 캐시
        self.docs_dir = Path("docs/tasks")
        self.similar_task_threshold = 0.6  # 유사도 임계값

    def get_subscribed_events(self) -> List[EventType]:
        """구독할 이벤트 타입"""
        return [
            EventType.TASK_STARTED,
            EventType.TASK_ADDED
        ]

    def handle_event(self, event: WorkflowEvent) -> None:
        """이벤트 처리"""
        if not self.enabled:
            return

        try:
            if event.type == EventType.TASK_STARTED:
                self._provide_task_context(event)
            elif event.type == EventType.TASK_ADDED:
                self._prepare_task_context(event)
        except Exception as e:
            logger.error(f"TaskContextListener 오류: {e}")

    def _prepare_task_context(self, event: WorkflowEvent) -> None:
        """태스크 추가 시 컨텍스트 준비"""
        task_id = event.task_id
        details = event.details or {}
        task_title = details.get('title', '')

        # 유사한 이전 태스크 찾기
        similar_tasks = self._find_similar_tasks(task_title)

        # 컨텍스트 준비
        context = {
            'task_id': task_id,
            'title': task_title,
            'similar_tasks': similar_tasks,
            'prepared_at': datetime.now().isoformat()
        }

        self.task_contexts[task_id] = context
        logger.debug(f"태스크 컨텍스트 준비됨: {task_title}")

    def _provide_task_context(self, event: WorkflowEvent) -> None:
        """태스크 시작 시 컨텍스트 제공"""
        task_id = event.task_id
        details = event.details or {}
        task_title = details.get('title', '')

        # 준비된 컨텍스트 확인
        context = self.task_contexts.get(task_id, {})

        # 관련 문서 로드
        related_docs = self._load_related_docs(task_title, context.get('similar_tasks', []))

        # 이전 태스크 정보 로드
        previous_tasks = self._load_previous_tasks(task_title)

        # 프로젝트 컨텍스트 로드
        project_context = self._load_project_context()

        # 컨텍스트 정보 출력
        self._display_context(task_title, related_docs, previous_tasks, project_context)

        # task_context.json 업데이트
        self._update_task_context(task_id, {
            'started_at': event.timestamp,
            'related_docs': [str(doc) for doc in related_docs],
            'similar_tasks': context.get('similar_tasks', []),
            'project_context': project_context
        })

    def _find_similar_tasks(self, task_title: str) -> List[Dict[str, Any]]:
        """유사한 이전 태스크 찾기"""
        similar_tasks = []

        # task_context.json에서 검색
        task_context_path = Path("memory/task_context.json")
        if task_context_path.exists():
            try:
                with open(task_context_path, 'r', encoding='utf-8') as f:
                    all_contexts = json.load(f)

                for task_id, context in all_contexts.get('tasks', {}).items():
                    other_title = context.get('task_title', '')
                    similarity = self._calculate_similarity(task_title, other_title)

                    if similarity > self.similar_task_threshold:
                        similar_tasks.append({
                            'task_id': task_id,
                            'title': other_title,
                            'similarity': similarity,
                            'completed_at': context.get('completed_at'),
                            'files': context.get('files_created', [])
                        })
            except Exception as e:
                logger.debug(f"유사 태스크 검색 실패: {e}")

        # 유사도 순으로 정렬
        similar_tasks.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_tasks[:5]  # 상위 5개만

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """간단한 텍스트 유사도 계산"""
        if not text1 or not text2:
            return 0.0

        # 소문자 변환 및 단어 분리
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Jaccard 유사도
        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _load_related_docs(self, task_title: str, similar_tasks: List[Dict]) -> List[Path]:
        """관련 문서 로드"""
        related_docs = []

        if not self.docs_dir.exists():
            return related_docs

        # 유사 태스크의 문서 찾기
        for task in similar_tasks[:3]:  # 상위 3개
            task_id = task['task_id']
            # 해당 태스크 ID가 포함된 문서 찾기
            for doc in self.docs_dir.glob(f"*{task_id[:8]}*.md"):
                if doc.exists():
                    related_docs.append(doc)

        # 키워드 기반 문서 검색
        keywords = task_title.lower().split()
        for doc in self.docs_dir.glob("*.md"):
            doc_name = doc.stem.lower()
            if any(keyword in doc_name for keyword in keywords):
                if doc not in related_docs:
                    related_docs.append(doc)

        return related_docs[:5]  # 최대 5개

    def _load_previous_tasks(self, task_title: str) -> List[Dict[str, Any]]:
        """이전 태스크 정보 로드"""
        previous_tasks = []

        # workflow.json에서 이전 완료 태스크 검색
        workflow_path = Path("memory/workflow.json")
        if workflow_path.exists():
            try:
                with open(workflow_path, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)

                for plan in workflow_data.get('plans', []):
                    for task in plan.get('tasks', []):
                        if task.get('status') == 'completed':
                            # 키워드 매칭
                            if any(word in task.get('title', '').lower() 
                                   for word in task_title.lower().split()):
                                previous_tasks.append({
                                    'title': task['title'],
                                    'completed_at': task.get('completed_at'),
                                    'duration': task.get('duration'),
                                    'notes': task.get('notes', [])
                                })
            except Exception as e:
                logger.debug(f"이전 태스크 로드 실패: {e}")

        return previous_tasks[:3]  # 최근 3개

    def _load_project_context(self) -> Dict[str, Any]:
        """프로젝트 전체 컨텍스트 로드"""
        context = {}

        # context.json 로드
        context_path = Path("memory/context.json")
        if context_path.exists():
            try:
                with open(context_path, 'r', encoding='utf-8') as f:
                    context = json.load(f)
            except Exception as e:
                logger.debug(f"프로젝트 컨텍스트 로드 실패: {e}")

        return {
            'project_name': context.get('project_name', 'Unknown'),
            'last_updated': context.get('last_updated'),
            'git_branch': context.get('git', {}).get('branch', 'main')
        }

    def _display_context(self, task_title: str, related_docs: List[Path], 
                        previous_tasks: List[Dict], project_context: Dict) -> None:
        """컨텍스트 정보 표시"""
        print(f"""
📚 태스크 컨텍스트: {task_title}
{'='*60}

🔗 관련 문서 ({len(related_docs)}개):""")

        for doc in related_docs:
            print(f"   - {doc.name}")

        if previous_tasks:
            print(f"\n📋 유사한 이전 태스크 ({len(previous_tasks)}개):")
            for task in previous_tasks:
                print(f"   - {task['title']}")
                if task.get('duration'):
                    print(f"     소요 시간: {task['duration']}")

        print(f"""
📁 프로젝트 정보:
   - 프로젝트: {project_context.get('project_name')}
   - 브랜치: {project_context.get('git_branch')}

{'='*60}
""")

    def _update_task_context(self, task_id: str, context_data: Dict[str, Any]) -> None:
        """task_context.json 업데이트"""
        task_context_path = Path("memory/task_context.json")

        # 기존 데이터 로드
        if task_context_path.exists():
            with open(task_context_path, 'r', encoding='utf-8') as f:
                all_contexts = json.load(f)
        else:
            all_contexts = {"tasks": {}}

        # 업데이트
        if task_id not in all_contexts['tasks']:
            all_contexts['tasks'][task_id] = {}

        all_contexts['tasks'][task_id].update(context_data)

        # 저장
        with open(task_context_path, 'w', encoding='utf-8') as f:
            json.dump(all_contexts, f, indent=2, ensure_ascii=False)

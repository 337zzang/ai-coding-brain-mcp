"""
Enhanced Listener Integration System
===================================

워크플로우 시스템의 모든 리스너를 자동으로 등록하고 관리하는 통합 시스템

주요 기능:
- 모든 리스너 자동 등록
- 이벤트 발행 시 자동 훅 실행
- 컨텍스트 자동 기록
- 에러 자동 수집
- 문서 자동 생성
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from python.workflow.v3.event_bus import EventBus
from python.workflow.v3.listener_manager import ListenerManager
from python.workflow.v3.workflow_event_adapter import WorkflowEventAdapter

# 리스너들 import
from python.workflow.v3.listeners.task_context_listener import TaskContextListener
from python.workflow.v3.listeners.error_collector_listener import ErrorCollectorListener
from python.workflow.v3.listeners.docs_generator_listener import DocsGeneratorListener
from python.workflow.v3.listeners.automation_listeners import (
    TaskAutoProgressListener,
    PlanAutoArchiveListener
)

# 기존 리스너들 (올바른 import 경로)
try:
    from python.workflow.v3.listeners import ErrorHandlerListener
except ImportError:
    # 다른 경로 시도
    try:
        from python.workflow.v3.listener_manager import ErrorHandlerListener
    except ImportError:
        ErrorHandlerListener = None

try:
    from python.workflow.v3.events import GitAutoCommitListener
except ImportError:
    GitAutoCommitListener = None

logger = logging.getLogger(__name__)


class EnhancedListenerIntegration:
    """향상된 리스너 통합 시스템"""
    
    def __init__(self, workflow_manager, helpers=None):
        self.workflow_manager = workflow_manager
        self.helpers = helpers
        self.event_adapter = None
        self.listeners = {}
        self.listener_stats = {
            'registered': 0,
            'events_processed': 0,
            'errors': 0
        }
        
    def initialize(self) -> bool:
        """리스너 시스템 초기화"""
        try:
            # EventAdapter 가져오기 또는 생성
            if hasattr(self.workflow_manager, 'event_adapter'):
                self.event_adapter = self.workflow_manager.event_adapter
            else:
                self.event_adapter = WorkflowEventAdapter(self.workflow_manager)
                self.workflow_manager.event_adapter = self.event_adapter
            
            # 모든 리스너 등록
            self._register_all_listeners()
            
            logger.info(
                f"Enhanced listener system initialized: "
                f"{self.listener_stats['registered']} listeners registered"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced listener system: {e}")
            return False
    
    def _register_all_listeners(self):
        """모든 리스너 자동 등록"""
        
        # 1. 컨텍스트 리스너 (태스크 시작 시 관련 정보 제공)
        context_listener = TaskContextListener(enabled=True)
        self._register_listener('task_context', context_listener)
        logger.info("✅ TaskContextListener registered (TASK_STARTED, TASK_ADDED)")
        
        # 2. 에러 수집 리스너 (오류 자동 수집 및 보고)
        error_collector = ErrorCollectorListener(enabled=True)
        self._register_listener('error_collector', error_collector)
        logger.info("✅ ErrorCollectorListener registered (TASK_FAILED)")
        
        # 3. 문서 생성 리스너 (태스크/플랜 완료 시 문서 자동 생성)
        docs_generator = DocsGeneratorListener(enabled=True)
        self._register_listener('docs_generator', docs_generator)
        logger.info("✅ DocsGeneratorListener registered (TASK_COMPLETED, PLAN_COMPLETED)")
        
        # 4. 자동 진행 리스너 (태스크 완료 시 자동으로 다음 태스크 시작)
        auto_progress = TaskAutoProgressListener(
            workflow_manager=self.workflow_manager,
            enabled=True
        )
        self._register_listener('auto_progress', auto_progress)
        logger.info("✅ TaskAutoProgressListener registered (TASK_COMPLETED)")
        
        # 5. 플랜 자동 보관 리스너 (플랜 완료 시 자동 보관)
        auto_archive = PlanAutoArchiveListener(
            workflow_manager=self.workflow_manager,
            enabled=True
        )
        self._register_listener('auto_archive', auto_archive)
        logger.info("✅ PlanAutoArchiveListener registered (PLAN_COMPLETED)")
        
        # 6. 에러 핸들러 리스너 (기존 - 태스크 실패 시 재시도)
        if ErrorHandlerListener:
            error_handler = ErrorHandlerListener(
                workflow_manager=self.workflow_manager,
                retry_limit=3,
                enabled=True
            )
            self._register_listener('error_handler', error_handler)
            logger.info("✅ ErrorHandlerListener registered (TASK_FAILED, TASK_BLOCKED)")
        else:
            logger.warning("⚠️ ErrorHandlerListener not available")
        
        # 7. Git 자동 커밋 리스너 (helpers가 있는 경우)
        if self.helpers and GitAutoCommitListener:
            git_listener = GitAutoCommitListener(self.helpers)
            self._register_listener('git_auto_commit', git_listener)
            logger.info("✅ GitAutoCommitListener registered")
        elif not GitAutoCommitListener:
            logger.warning("⚠️ GitAutoCommitListener not available")
    
    def _register_listener(self, name: str, listener):
        """개별 리스너 등록"""
        try:
            # WorkflowEventAdapter에 리스너 추가
            self.event_adapter.add_workflow_listener(listener)
            
            # 내부 추적
            self.listeners[name] = listener
            self.listener_stats['registered'] += 1
            
        except Exception as e:
            logger.error(f"Failed to register listener {name}: {e}")
            self.listener_stats['errors'] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """리스너 시스템 상태 조회"""
        return {
            'initialized': self.event_adapter is not None,
            'listeners': list(self.listeners.keys()),
            'stats': self.listener_stats,
            'enabled_listeners': [
                name for name, listener in self.listeners.items()
                if hasattr(listener, 'enabled') and listener.enabled
            ]
        }
    
    def enable_listener(self, name: str) -> bool:
        """특정 리스너 활성화"""
        if name in self.listeners:
            listener = self.listeners[name]
            if hasattr(listener, 'enabled'):
                listener.enabled = True
                logger.info(f"Listener {name} enabled")
                return True
        return False
    
    def disable_listener(self, name: str) -> bool:
        """특정 리스너 비활성화"""
        if name in self.listeners:
            listener = self.listeners[name]
            if hasattr(listener, 'enabled'):
                listener.enabled = False
                logger.info(f"Listener {name} disabled")
                return True
        return False


def integrate_enhanced_listeners(workflow_manager, helpers=None) -> Optional[EnhancedListenerIntegration]:
    """워크플로우에 향상된 리스너 시스템 통합
    
    Args:
        workflow_manager: WorkflowManager 인스턴스
        helpers: helpers 객체 (선택사항)
        
    Returns:
        EnhancedListenerIntegration 인스턴스 또는 None
    """
    integration = EnhancedListenerIntegration(workflow_manager, helpers)
    
    if integration.initialize():
        # WorkflowManager에 통합 시스템 연결
        workflow_manager.listener_integration = integration
        return integration
    
    return None


# 통합 테스트 함수
def test_enhanced_integration():
    """향상된 통합 시스템 테스트"""
    print("🧪 Enhanced Listener Integration Test\n")
    
    # 모의 WorkflowManager
    class MockWorkflowManager:
        def __init__(self):
            self.event_adapter = None
            self.listener_integration = None
    
    # 테스트 실행
    manager = MockWorkflowManager()
    integration = integrate_enhanced_listeners(manager)
    
    if integration:
        status = integration.get_status()
        print(f"✅ 초기화 성공")
        print(f"📊 등록된 리스너: {len(status['listeners'])}개")
        print(f"📋 리스너 목록: {', '.join(status['listeners'])}")
        print(f"✨ 활성 리스너: {', '.join(status['enabled_listeners'])}")
    else:
        print("❌ 초기화 실패")


if __name__ == "__main__":
    test_enhanced_integration()

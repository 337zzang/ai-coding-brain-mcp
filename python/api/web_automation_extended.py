"""
WebAutomation with Recording
액션 레코딩 기능이 추가된 WebAutomation 확장 클래스
"""

from typing import Dict, Any, Optional
from .web_automation import WebAutomation
from .web_automation_recorder import ActionRecorder


class WebAutomationWithRecording(WebAutomation):
    """액션 레코딩 기능이 추가된 WebAutomation 클래스"""

    def __init__(self, *args, record_actions: bool = True, project_name: str = "web_automation", **kwargs):
        """초기화

        Args:
            record_actions: 액션 레코딩 여부
            project_name: 프로젝트 이름 (스크립트 생성 시 사용)
            *args, **kwargs: WebAutomation 인자들
        """
        super().__init__(*args, **kwargs)
        self.recorder = ActionRecorder(project_name) if record_actions else None
        self.record_actions = record_actions

    def go_to_page(self, url: str, **kwargs) -> Dict[str, Any]:
        """페이지 이동 (레코딩 포함)"""
        result = super().go_to_page(url, **kwargs)

        if self.recorder and result['success']:
            self.recorder.record_action(
                'navigate',
                url=url,
                title=result.get('title'),
                load_time=result.get('load_time'),
                **kwargs
            )

        return result

    def click_element(self, selector: str, by: str = "css", **kwargs) -> Dict[str, Any]:
        """요소 클릭 (레코딩 포함)"""
        result = super().click_element(selector, by, **kwargs)

        if self.recorder:
            self.recorder.record_action(
                'click',
                success=result['success'],
                selector=selector,
                by=by,
                page_changed=result.get('page_changed', False),
                **kwargs
            )

        return result

    def input_text(self, selector: str, text: str, by: str = "css", **kwargs) -> Dict[str, Any]:
        """텍스트 입력 (레코딩 포함)"""
        result = super().input_text(selector, text, by, **kwargs)

        if self.recorder:
            # 민감한 정보는 마스킹
            masked_text = '***' if any(w in selector.lower() for w in ['password', 'secret', 'token']) else text

            self.recorder.record_action(
                'input',
                success=result['success'],
                selector=selector,
                text=masked_text,
                by=by,
                **kwargs
            )

        return result

    def scroll_page(self, **kwargs) -> Dict[str, Any]:
        """페이지 스크롤 (레코딩 포함)"""
        result = super().scroll_page(**kwargs)

        if self.recorder and result['success']:
            self.recorder.record_action(
                'scroll',
                action=kwargs.get('action', 'down'),
                scroll_distance=result.get('scroll_distance'),
                at_bottom=result.get('at_bottom'),
                at_top=result.get('at_top'),
                **kwargs
            )

        return result

    def extract_text(self, selector: str, by: str = "css", **kwargs) -> Dict[str, Any]:
        """텍스트 추출 (레코딩 포함)"""
        result = super().extract_text(selector, by, **kwargs)

        if self.recorder and result['success']:
            self.recorder.record_action(
                'extract',
                selector=selector,
                by=by,
                text_length=len(result.get('text', '')) if 'text' in result else 0,
                count=result.get('count', 1),
                **kwargs
            )

        return result

    def generate_script(self, output_file: str = None) -> Dict[str, Any]:
        """레코딩된 액션을 스크립트로 생성

        Args:
            output_file: 출력 파일 경로

        Returns:
            Dict: 생성 결과
        """
        if not self.recorder:
            return {
                "success": False,
                "message": "레코더가 활성화되지 않았습니다."
            }

        return self.recorder.generate_script(output_file)

    def get_recording_status(self) -> Dict[str, Any]:
        """레코딩 상태 조회"""
        if not self.recorder:
            return {
                "success": True,
                "recording": False,
                "message": "레코딩이 비활성화되어 있습니다."
            }

        return {
            "success": True,
            "recording": True,
            "project_name": self.recorder.project_name,
            "total_actions": len(self.recorder.actions),
            "duration": (datetime.now() - self.recorder.start_time).total_seconds(),
            "last_action": self.recorder.actions[-1] if self.recorder.actions else None
        }

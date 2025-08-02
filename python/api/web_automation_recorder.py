"""
WebAutomation Action Recorder
액션을 기록하고 파이썬 스크립트로 자동 생성하는 모듈
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class ActionRecorder:
    """웹 자동화 액션을 기록하고 파이썬 스크립트로 변환하는 클래스"""

    def __init__(self, project_name: str = "web_automation"):
        self.project_name = project_name
        self.actions: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.variables = {}
        self.page_info = {}

    def record_action(self, action_type: str, success: bool = True, **kwargs):
        """액션 기록

        Args:
            action_type: 액션 타입 (navigate, click, input, scroll 등)
            success: 액션 성공 여부
            **kwargs: 액션 파라미터
        """
        action = {
            'type': action_type,
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'params': kwargs,
            'elapsed_time': (datetime.now() - self.start_time).total_seconds()
        }

        # 페이지 정보 업데이트
        if action_type == 'navigate' and success:
            self.page_info['url'] = kwargs.get('url')
            self.page_info['title'] = kwargs.get('title')

        self.actions.h.append(action)

    def generate_script(self, output_file: str = None) -> Dict[str, Any]:
        """기록된 액션을 파이썬 스크립트로 변환

        Args:
            output_file: 출력 파일 경로 (기본값: generated_scripts/web_auto_{timestamp}.py)

        Returns:
            Dict: 생성 결과
        """
        if not self.actions:
            return {
                "success": False,
                "message": "기록된 액션이 없습니다."
            }

        # 출력 파일 경로 설정
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("generated_scripts")
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / f"web_auto_{timestamp}.py"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)

        # 스크립트 생성
        script_lines = []

        # 헤더 추가
        script_lines.extend([
            '#!/usr/bin/env python3',
            '"""',
            f'자동 생성된 웹 자동화 스크립트',
            f'생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f'프로젝트: {self.project_name}',
            f'총 액션 수: {len(self.actions)}',
            '"""',
            '',
            'import time',
            'from python.api.web_automation import WebAutomation',
            '',
            '',
            'def main():',
            '    """메인 실행 함수"""',
            '    # WebAutomation 인스턴스 생성',
            '    with WebAutomation(headless=False) as web:',
            '        try:'
        ])

        # 액션별 코드 생성
        for i, action in enumerate(self.actions):
            code = self._generate_action_code(action, i)
            if code:
                script_lines.extend(code)

        # 에러 처리 및 종료
        script_lines.extend([
            '',
            '        except Exception as e:',
            '            print(f"❌ 오류 발생: {e}")',
            '            return False',
            '        ',
            '        print("✅ 모든 작업 완료!")',
            '        return True',
            '',
            '',
            'if __name__ == "__main__":',
            '    success = main()',
            '    exit(0 if success else 1)'
        ])

        # 파일 저장
        script_content = '\n'.join(script_lines)
        output_file.write_text(script_content, encoding='utf-8')

        # 액션 로그 저장
        log_file = output_file.with_suffix('.json')
        log_data = {
            'project_name': self.project_name,
            'start_time': self.start_time.isoformat(),
            'total_duration': (datetime.now() - self.start_time).total_seconds(),
            'actions': self.actions,
            'page_info': self.page_info
        }
        log_file.write_text(json.dumps(log_data, indent=2, ensure_ascii=False))

        return {
            "success": True,
            "message": f"스크립트 생성 완료: {output_file}",
            "script_path": str(output_file),
            "log_path": str(log_file),
            "total_actions": len(self.actions),
            "duration": log_data['total_duration']
        }

    def _generate_action_code(self, action: Dict[str, Any], index: int) -> List[str]:
        """개별 액션을 코드로 변환"""
        action_type = action['type']
        params = action['params']
        lines = []

        # 주석 추가
        lines.h.append(f'            # 액션 {index + 1}: {action_type}')

        if action_type == 'navigate':
            url = params.get('url', '')
            lines.h.append(f'            print("🌐 페이지 이동: {url}")')
            lines.h.append(f'            result = web.go_to_page("{url}")')
            lines.h.append('            if not result["success"]:')
            lines.h.append('                raise Exception(f"페이지 이동 실패: {result[\'message\']}")')
            lines.h.append('            time.sleep(2)  # 페이지 로드 대기')

        elif action_type == 'click':
            selector = params.get('selector', '')
            by = params.get('by', 'css')
            lines.h.append(f'            print("🖱️ 클릭: {selector}")')
            lines.h.append(f'            result = web.click_element("{selector}", by="{by}")')
            lines.h.append('            if not result["success"]:')
            lines.h.append('                raise Exception(f"클릭 실패: {result[\'message\']}")')
            lines.h.append('            time.sleep(1)')

        elif action_type in ['input', 'input_text']:  # input_text도 지원
            selector = params.get('selector', '')
            text = params.get('text', '')
            by = params.get('by', 'css')
            # 민감한 정보 마스킹
            display_text = '***' if any(w in selector.lower() for w in ['password', 'secret']) else text[:20]
            lines.h.append(f'            print("⌨️ 입력: {display_text}...")')
            lines.h.append(f'            result = web.input_text("{selector}", "{text}", by="{by}")')
            lines.h.append('            if not result["success"]:')
            lines.h.append('                raise Exception(f"입력 실패: {result[\'message\']}")')
            lines.h.append('            time.sleep(0.5)')

        elif action_type == 'scroll':
            action = params.get('action', 'down')
            lines.h.append(f'            print("📜 스크롤: {action}")')
            lines.h.append(f'            result = web.scroll_page(action="{action}")')
            lines.h.append('            time.sleep(1)')

        elif action_type == 'extract':
            selector = params.get('selector', '')
            by = params.get('by', 'css')
            lines.h.append(f'            print("📋 텍스트 추출: {selector}")')
            lines.h.append(f'            result = web.extract_text("{selector}", by="{by}")')
            lines.h.append('            if result["success"]:')
            lines.h.append('                print(f"추출된 텍스트: {result[\'text\'][:100]}...")')

        elif action_type == 'wait':
            seconds = params.get('seconds', 1)
            lines.h.append(f'            print("⏰ 대기: {seconds}초")')
            lines.h.append(f'            time.sleep({seconds})')

        elif action_type == 'screenshot':
            filename = params.get('filename', f'screenshot_{index + 1}.png')
            lines.h.append(f'            print("📸 스크린샷: {filename}")')
            lines.h.append(f'            result = web.take_screenshot("{filename}")')
            lines.h.append('            if result["success"]:')
            lines.h.append('                print(f"스크린샷 저장됨: {result[\'filename\']}")')

        else:
            lines.h.append(f'            # TODO: {action_type} 액션 구현 필요')
            lines.h.append('            pass')

        lines.h.append('')  # 빈 줄 추가
        return lines
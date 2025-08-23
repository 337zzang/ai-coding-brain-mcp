"""
Context Capture Module for Web Automation
사용자의 브라우저 액션을 AI 컨텍스트로 변환하는 모듈
"""

import json
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# 기존 web 모듈 임포트
from . import web


class BrowserContextCapture:
    """브라우저 액션을 AI 컨텍스트로 캡처하는 클래스"""
    
    def __init__(self, session_id: str = None, output_to_stdout: bool = True):
        """
        초기화
        
        Args:
            session_id: 브라우저 세션 ID
            output_to_stdout: stdout으로 자동 출력 여부
        """
        self.session_id = session_id or f"context_{datetime.now():%Y%m%d_%H%M%S}"
        self.output_to_stdout = output_to_stdout
        self.context_buffer = []
        self.is_capturing = False
        
    def start_capture(self, url: str = None, headless: bool = False) -> Dict[str, Any]:
        """
        컨텍스트 캡처 시작
        
        Args:
            url: 시작 URL
            headless: 헤드리스 모드 여부
            
        Returns:
            시작 결과
        """
        try:
            # 1. 브라우저 시작 (오버레이 포함)
            result = web.web_start(
                session_id=self.session_id,
                headless=headless,
                overlay=True,
                overlay_config={
                    'mini_mode': True,
                    'auto_hide': False,
                    'position': 'top-right'
                }
            )
            
            if not result.get('ok'):
                return result
                
            # 2. URL 이동 (제공된 경우)
            if url:
                nav_result = web.web_goto(url, session_id=self.session_id)
                if not nav_result.get('ok'):
                    return nav_result
            
            # 3. 컨텍스트 캡처 모드 활성화
            enable_result = self._enable_context_mode()
            if not enable_result.get('ok'):
                return enable_result
                
            self.is_capturing = True
            
            return {
                'ok': True,
                'data': {
                    'session_id': self.session_id,
                    'url': url,
                    'message': 'Context capture started. User actions will be recorded.'
                }
            }
            
        except Exception as e:
            return {
                'ok': False,
                'error': str(e)
            }
    
    def _enable_context_mode(self) -> Dict[str, Any]:
        """컨텍스트 캡처 모드 활성화"""
        
        context_js = """
        (function() {
            // 기존 automationActions 확장
            if (!window.contextCapture) {
                window.contextCapture = {
                    enabled: true,
                    startTime: new Date().toISOString(),
                    actionCount: 0,
                    
                    // 의도 추론 함수
                    inferIntent: function(action) {
                        const selector = action.selector || '';
                        const text = action.text || '';
                        const type = action.type;
                        
                        // 할일 관련 의도 감지
                        if (text.includes('완료') || text.includes('complete')) {
                            return 'mark_complete';
                        } else if (text.includes('추가') || text.includes('새') || text.includes('new')) {
                            return 'create_new';
                        } else if (text.includes('삭제') || text.includes('delete')) {
                            return 'delete_item';
                        } else if (text.includes('수정') || text.includes('edit')) {
                            return 'edit_item';
                        }
                        
                        // 액션 타입 기반 의도
                        if (type === 'type') {
                            return 'input_data';
                        } else if (type === 'click' && selector.includes('submit')) {
                            return 'submit_form';
                        } else if (type === 'click' && selector.includes('checkbox')) {
                            return 'toggle_checkbox';
                        }
                        
                        return 'unknown';
                    },
                    
                    // 워크플로우 감지
                    detectWorkflow: function(actions) {
                        if (actions.length < 2) return 'single_action';
                        
                        const patterns = {
                            'task_creation': ['create_new', 'input_data', 'submit_form'],
                            'task_completion': ['toggle_checkbox', 'mark_complete'],
                            'task_editing': ['edit_item', 'input_data', 'submit_form'],
                            'form_filling': ['input_data', 'input_data', 'submit_form']
                        };
                        
                        // 패턴 매칭
                        const intents = actions.map(a => a.intent);
                        for (const [workflow, pattern] of Object.entries(patterns)) {
                            if (this.matchesPattern(intents, pattern)) {
                                return workflow;
                            }
                        }
                        
                        return 'custom_workflow';
                    },
                    
                    matchesPattern: function(intents, pattern) {
                        // 간단한 패턴 매칭 (순서 고려)
                        let patternIndex = 0;
                        for (const intent of intents) {
                            if (intent === pattern[patternIndex]) {
                                patternIndex++;
                                if (patternIndex >= pattern.length) {
                                    return true;
                                }
                            }
                        }
                        return false;
                    },
                    
                    // 컨텍스트 데이터 생성
                    getContext: function() {
                        const actions = window.automationActions || [];
                        const enrichedActions = actions.map((action, index) => ({
                            index: index + 1,
                            type: action.type,
                            selector: action.selector,
                            text: action.text || '',
                            value: action.value || '',
                            intent: this.inferIntent(action),
                            timestamp: action.timestamp || Date.now(),
                            page: {
                                url: window.location.href,
                                title: document.title
                            }
                        }));
                        
                        return {
                            context_type: 'user_browser_actions',
                            session: {
                                id: '""" + self.session_id + """',
                                start_time: this.startTime,
                                current_time: new Date().toISOString(),
                                url: window.location.href,
                                title: document.title
                            },
                            actions: enrichedActions,
                            statistics: {
                                total_actions: enrichedActions.length,
                                action_types: this.countActionTypes(enrichedActions),
                                duration_ms: Date.now() - new Date(this.startTime).getTime()
                            },
                            detected_workflow: this.detectWorkflow(enrichedActions),
                            summary: this.generateSummary(enrichedActions)
                        };
                    },
                    
                    countActionTypes: function(actions) {
                        const counts = {};
                        actions.forEach(a => {
                            counts[a.type] = (counts[a.type] || 0) + 1;
                        });
                        return counts;
                    },
                    
                    generateSummary: function(actions) {
                        if (actions.length === 0) return '사용자가 아직 액션을 수행하지 않음';
                        
                        const workflow = this.detectWorkflow(actions);
                        const actionCount = actions.length;
                        const lastAction = actions[actions.length - 1];
                        
                        let summary = `사용자가 ${actionCount}개의 액션을 수행함. `;
                        
                        if (workflow === 'task_creation') {
                            summary += '새로운 할일을 생성하는 작업을 수행함.';
                        } else if (workflow === 'task_completion') {
                            summary += '할일을 완료 처리하는 작업을 수행함.';
                        } else if (workflow === 'task_editing') {
                            summary += '기존 할일을 수정하는 작업을 수행함.';
                        } else {
                            summary += `마지막 액션: ${lastAction.type} on ${lastAction.selector}`;
                        }
                        
                        return summary;
                    }
                };
                
                // 기존 액션 캡처 함수 후킹
                const originalPush = Array.prototype.push;
                window.automationActions.push = function(...args) {
                    const result = originalPush.apply(this, args);
                    
                    // 새 액션이 추가될 때마다 컨텍스트 출력
                    if (window.contextCapture.enabled) {
                        const context = window.contextCapture.getContext();
                        console.log('[CONTEXT_UPDATE]', JSON.stringify(context));
                    }
                    
                    return result;
                };
            }
            
            // 녹화 모드 자동 시작
            if (!window.recordingMode && window.toggleRecording) {
                window.toggleRecording();
            }
            
            return {
                ok: true,
                message: 'Context capture mode enabled'
            };
        })()
        """
        
        return web.web_execute_js(context_js, self.session_id)
    
    def get_current_context(self) -> Dict[str, Any]:
        """현재까지 캡처된 컨텍스트 가져오기"""
        
        if not self.is_capturing:
            return {
                'ok': False,
                'error': 'Context capture not started'
            }
        
        try:
            # JavaScript에서 컨텍스트 가져오기
            result = web.web_execute_js(
                "window.contextCapture ? window.contextCapture.getContext() : null",
                self.session_id
            )
            
            if not result.get('ok'):
                return result
            
            context_data = result.get('data')
            
            if not context_data:
                return {
                    'ok': False,
                    'error': 'No context data available'
                }
            
            # stdout으로 출력 (옵션)
            if self.output_to_stdout:
                self._output_to_stdout(context_data)
            
            # 버퍼에 저장
            self.context_buffer.append(context_data)
            
            return {
                'ok': True,
                'data': context_data
            }
            
        except Exception as e:
            return {
                'ok': False,
                'error': str(e)
            }
    
    def _output_to_stdout(self, context_data: Dict[str, Any]):
        """컨텍스트를 stdout으로 출력"""
        
        # AI가 읽기 쉬운 형식으로 출력
        print("\n" + "="*60)
        print("[AI_CONTEXT_CAPTURE]")
        print("="*60)
        
        # 세션 정보
        session = context_data.get('session', {})
        print(f"📍 Session: {session.get('id')}")
        print(f"📍 URL: {session.get('url')}")
        print(f"📍 Duration: {context_data.get('statistics', {}).get('duration_ms', 0)/1000:.1f}s")
        
        # 액션 요약
        actions = context_data.get('actions', [])
        print(f"\n📊 Actions: {len(actions)} total")
        
        for action in actions[-5:]:  # 최근 5개만 표시
            print(f"  #{action['index']}: {action['type']} → {action['intent']}")
            if action.get('value'):
                print(f"       Value: {action['value'][:50]}...")
        
        # 워크플로우
        print(f"\n🔄 Detected Workflow: {context_data.get('detected_workflow')}")
        print(f"📝 Summary: {context_data.get('summary')}")
        
        # JSON 전체 (접힌 형태)
        print(f"\n📦 Full Context (JSON):")
        print(json.dumps(context_data, ensure_ascii=False, indent=2))
        print("="*60 + "\n")
    
    def save_context(self, filepath: str = None) -> Dict[str, Any]:
        """컨텍스트를 파일로 저장"""
        
        if not self.context_buffer:
            return {
                'ok': False,
                'error': 'No context to save'
            }
        
        try:
            if not filepath:
                # 기본 경로
                context_dir = Path(".web_sessions") / "contexts"
                context_dir.mkdir(parents=True, exist_ok=True)
                filepath = context_dir / f"context_{self.session_id}.json"
            
            # 전체 세션 컨텍스트 생성
            full_context = {
                'session_id': self.session_id,
                'created_at': datetime.now().isoformat(),
                'snapshots': self.context_buffer
            }
            
            # 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(full_context, f, ensure_ascii=False, indent=2)
            
            return {
                'ok': True,
                'data': {
                    'filepath': str(filepath),
                    'size': len(self.context_buffer)
                }
            }
            
        except Exception as e:
            return {
                'ok': False,
                'error': str(e)
            }
    
    def stop_capture(self) -> Dict[str, Any]:
        """컨텍스트 캡처 중지"""
        
        if not self.is_capturing:
            return {
                'ok': False,
                'error': 'Context capture not running'
            }
        
        try:
            # 최종 컨텍스트 가져오기
            final_context = self.get_current_context()
            
            # 자동 저장
            save_result = self.save_context()
            
            # 브라우저 정리 (옵션)
            # web.web_close(self.session_id)
            
            self.is_capturing = False
            
            return {
                'ok': True,
                'data': {
                    'final_context': final_context.get('data') if final_context.get('ok') else None,
                    'saved_to': save_result.get('data', {}).get('filepath') if save_result.get('ok') else None,
                    'total_actions': len(self.context_buffer)
                }
            }
            
        except Exception as e:
            return {
                'ok': False,
                'error': str(e)
            }


# 편의 함수들
def start_context_capture(url: str = None, headless: bool = False) -> BrowserContextCapture:
    """컨텍스트 캡처 빠른 시작"""
    
    capture = BrowserContextCapture()
    result = capture.start_capture(url, headless)
    
    if result.get('ok'):
        print(f"✅ Context capture started: {capture.session_id}")
        print(f"📍 URL: {url or 'waiting for navigation'}")
        print(f"🔴 Recording mode activated - perform your actions in the browser")
    else:
        print(f"❌ Failed to start context capture: {result.get('error')}")
    
    return capture


def capture_and_print(session_id: str = None) -> Dict[str, Any]:
    """현재 세션의 컨텍스트를 즉시 출력"""
    
    if not session_id:
        session_id = web._current_session_id
    
    if not session_id:
        return {
            'ok': False,
            'error': 'No active session'
        }
    
    # 컨텍스트 가져오기
    result = web.web_execute_js(
        "window.contextCapture ? window.contextCapture.getContext() : null",
        session_id
    )
    
    if result.get('ok') and result.get('data'):
        context = result['data']
        
        # 간단한 형식으로 출력
        print(f"\n[CONTEXT] {json.dumps(context, ensure_ascii=False)}")
        
        return {
            'ok': True,
            'data': context
        }
    
    return result
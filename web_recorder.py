#!/usr/bin/env python3
"""
완벽한 양방향 웹 자동화 레코더
REPL ↔ Browser 양방향 통신 시스템
"""

import sys
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))
import ai_helpers_new as h

class WebRecorder:
    """양방향 웹 자동화 레코더 - REPL에서 브라우저를 완전 제어"""
    
    def __init__(self):
        self.session_id: Optional[str] = None
        self.recording: bool = False
        self.actions: List[Dict[str, Any]] = []
        self.guidance: List[str] = []
        self.workflows: Dict[str, Any] = {}
        
    def start(self, url: str = "https://example.com", headless: bool = False) -> str:
        """브라우저 시작 및 레코딩 환경 준비"""
        self.session_id = f"recorder_{int(time.time())}"
        
        print(f"🚀 브라우저 시작 중... (세션: {self.session_id})")
        result = h.web.start(self.session_id, headless=headless)
        
        if not result['ok']:
            print(f"❌ 브라우저 시작 실패: {result['error']}")
            return None
            
        print(f"✅ 브라우저 시작 성공!")
        
        # 페이지 이동
        h.web.goto(url, self.session_id)
        print(f"📍 페이지 로드: {url}")
        
        # 가이드 UI 주입
        self._inject_guide_ui()
        print("🎯 가이드 UI 활성화 완료")
        
        # 자동 레코딩 시작
        self._setup_recording()
        
        return self.session_id
    
    def _inject_guide_ui(self):
        """브라우저에 가이드 UI 주입"""
        guide_script = """
        // 기존 가이드 제거
        const existingGuide = document.getElementById('repl-guide');
        if (existingGuide) existingGuide.remove();
        
        // 가이드 UI 생성
        const guide = document.createElement('div');
        guide.id = 'repl-guide';
        guide.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            width: 320px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            z-index: 2147483647;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        `;
        
        guide.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="font-size: 24px; margin-right: 10px;">🎯</div>
                <h3 style="margin: 0; font-size: 18px; font-weight: 600;">REPL 웹 레코더</h3>
            </div>
            
            <div id="guide-message" style="
                background: rgba(255,255,255,0.2);
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 12px;
                font-size: 14px;
                line-height: 1.5;
            ">레코딩 준비 완료! REPL에서 지시를 기다리는 중...</div>
            
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div id="guide-status" style="display: flex; align-items: center;">
                    <span id="recording-indicator" style="
                        display: inline-block;
                        width: 10px;
                        height: 10px;
                        background: #4CAF50;
                        border-radius: 50%;
                        margin-right: 8px;
                        animation: pulse 2s infinite;
                    "></span>
                    <span id="recording-text" style="font-size: 14px;">레코딩 대기</span>
                </div>
                
                <div id="captured-count" style="
                    background: rgba(255,255,255,0.2);
                    padding: 5px 10px;
                    border-radius: 20px;
                    font-size: 14px;
                ">
                    액션: <span id="action-count" style="font-weight: bold;">0</span>
                </div>
            </div>
            
            <style>
                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.5; }
                    100% { opacity: 1; }
                }
                
                #repl-guide:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 15px 35px rgba(0,0,0,0.3);
                }
            </style>
        `;
        
        document.body.appendChild(guide);
        
        // REPL Bridge 객체 생성
        window.replBridge = {
            actions: [],
            recording: false,
            
            setGuidance: function(message) {
                const elem = document.getElementById('guide-message');
                if (elem) {
                    elem.innerText = message;
                    // 메시지 변경 시 하이라이트 효과
                    elem.style.background = 'rgba(255,255,255,0.4)';
                    setTimeout(() => {
                        elem.style.background = 'rgba(255,255,255,0.2)';
                    }, 300);
                }
            },
            
            startRecording: function() {
                this.recording = true;
                const indicator = document.getElementById('recording-indicator');
                const text = document.getElementById('recording-text');
                if (indicator) {
                    indicator.style.background = '#f44336';
                    indicator.style.animation = 'pulse 0.5s infinite';
                }
                if (text) text.innerText = '🔴 레코딩 중';
                
                this.captureEvents();
                return true;
            },
            
            stopRecording: function() {
                this.recording = false;
                const indicator = document.getElementById('recording-indicator');
                const text = document.getElementById('recording-text');
                if (indicator) {
                    indicator.style.background = '#9E9E9E';
                    indicator.style.animation = 'none';
                }
                if (text) text.innerText = '⏸️ 레코딩 중지';
                
                return this.actions;
            },
            
            captureEvents: function() {
                // 클릭 이벤트 캡처
                if (!window.replClickHandler) {
                    window.replClickHandler = (e) => {
                        if (!window.replBridge.recording) return;
                        
                        const action = {
                            type: 'click',
                            selector: this.getSelector(e.target),
                            text: (e.target.innerText || '').substring(0, 50),
                            tagName: e.target.tagName,
                            position: {x: e.clientX, y: e.clientY},
                            timestamp: Date.now()
                        };
                        
                        this.actions.push(action);
                        this.updateCount();
                        this.showCapture(action);
                        console.log('🔴 Click captured:', action);
                    };
                    document.addEventListener('click', window.replClickHandler, true);
                }
                
                // 입력 이벤트 캡처
                if (!window.replInputHandler) {
                    window.replInputHandler = (e) => {
                        if (!window.replBridge.recording) return;
                        
                        const action = {
                            type: 'input',
                            selector: this.getSelector(e.target),
                            value: e.target.value,
                            tagName: e.target.tagName,
                            inputType: e.target.type || 'text',
                            timestamp: Date.now()
                        };
                        
                        this.actions.push(action);
                        this.updateCount();
                        console.log('🔴 Input captured:', action);
                    };
                    document.addEventListener('input', window.replInputHandler, true);
                }
                
                // 키보드 이벤트 캡처 (Enter, Tab 등)
                if (!window.replKeyHandler) {
                    window.replKeyHandler = (e) => {
                        if (!window.replBridge.recording) return;
                        if (!['Enter', 'Tab', 'Escape'].includes(e.key)) return;
                        
                        const action = {
                            type: 'keypress',
                            key: e.key,
                            selector: this.getSelector(e.target),
                            timestamp: Date.now()
                        };
                        
                        this.actions.push(action);
                        this.updateCount();
                        console.log('🔴 Key captured:', action);
                    };
                    document.addEventListener('keydown', window.replKeyHandler, true);
                }
            },
            
            getSelector: function(element) {
                // 우선순위: id > data-testid > class > tag+index
                if (element.id) return '#' + element.id;
                if (element.getAttribute('data-testid')) 
                    return '[data-testid="' + element.getAttribute('data-testid') + '"]';
                if (element.className && typeof element.className === 'string') {
                    const classes = element.className.split(' ').filter(c => c.length > 0);
                    if (classes.length > 0) return '.' + classes[0];
                }
                
                // 태그명과 인덱스로 선택자 생성
                const tagName = element.tagName.toLowerCase();
                const siblings = Array.from(element.parentNode.children);
                const index = siblings.indexOf(element);
                return `${tagName}:nth-child(${index + 1})`;
            },
            
            updateCount: function() {
                const counter = document.getElementById('action-count');
                if (counter) counter.innerText = this.actions.length;
            },
            
            showCapture: function(action) {
                // 캡처 시각 효과
                const flash = document.createElement('div');
                flash.style.cssText = `
                    position: fixed;
                    top: ${action.position?.y || 100}px;
                    left: ${action.position?.x || 100}px;
                    width: 20px;
                    height: 20px;
                    background: radial-gradient(circle, rgba(255,0,0,0.8) 0%, rgba(255,0,0,0) 70%);
                    border-radius: 50%;
                    pointer-events: none;
                    z-index: 2147483646;
                    animation: captureFlash 0.5s ease-out;
                `;
                
                document.body.appendChild(flash);
                setTimeout(() => flash.remove(), 500);
            },
            
            getActions: function() {
                return this.actions;
            },
            
            clearActions: function() {
                this.actions = [];
                this.updateCount();
            }
        };
        
        // 캡처 애니메이션 스타일 추가
        const style = document.createElement('style');
        style.textContent = `
            @keyframes captureFlash {
                0% { transform: scale(0); opacity: 1; }
                100% { transform: scale(3); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
        
        console.log('✅ REPL Bridge initialized successfully!');
        """
        
        h.web.execute_js(guide_script, self.session_id)
    
    def _setup_recording(self):
        """레코딩 환경 설정"""
        h.web.execute_js("window.replBridge.startRecording()", self.session_id)
        self.recording = True
        print("🔴 레코딩 시작됨")
    
    def guide(self, message: str) -> None:
        """사용자에게 가이드 메시지 표시"""
        # JavaScript 문자열 이스케이프
        escaped_message = message.replace("'", "\\'").replace('"', '\\"')
        script = f"window.replBridge.setGuidance('{escaped_message}')"
        
        result = h.web.execute_js(script, self.session_id)
        if result['ok']:
            self.guidance.append(message)
            print(f"📢 가이드: {message}")
        else:
            print(f"❌ 가이드 설정 실패")
    
    def wait(self, seconds: int = 3) -> None:
        """사용자 액션 대기"""
        print(f"⏳ {seconds}초 대기 중...")
        for i in range(seconds, 0, -1):
            print(f"\r⏳ {i}초 남음...", end="", flush=True)
            time.sleep(1)
        print("\r✅ 대기 완료        ")
    
    def get_actions(self) -> List[Dict[str, Any]]:
        """캡처된 액션 가져오기"""
        result = h.web.execute_js("return window.replBridge.getActions()", self.session_id)
        if result['ok']:
            self.actions = result['data'] or []
            print(f"📊 캡처된 액션: {len(self.actions)}개")
            return self.actions
        return []
    
    def show_actions(self) -> None:
        """캡처된 액션 출력"""
        if not self.actions:
            print("📭 캡처된 액션이 없습니다.")
            return
            
        print("\n📋 캡처된 액션 목록:")
        print("-" * 50)
        for i, action in enumerate(self.actions, 1):
            if action['type'] == 'click':
                print(f"{i}. CLICK → {action['selector']} ({action.get('text', '')[:30]})")
            elif action['type'] == 'input':
                print(f"{i}. INPUT → {action['selector']} = '{action['value']}'")
            elif action['type'] == 'keypress':
                print(f"{i}. KEY → {action['key']} on {action['selector']}")
        print("-" * 50)
    
    def clear_actions(self) -> None:
        """캡처된 액션 초기화"""
        h.web.execute_js("window.replBridge.clearActions()", self.session_id)
        self.actions = []
        print("🗑️ 액션 목록이 초기화되었습니다.")
    
    def stop(self) -> List[Dict[str, Any]]:
        """레코딩 중지"""
        result = h.web.execute_js("return window.replBridge.stopRecording()", self.session_id)
        self.recording = False
        
        if result['ok']:
            self.actions = result['data'] or []
            print(f"⏹️ 레코딩 중지 (총 {len(self.actions)}개 액션)")
            return self.actions
        return []
    
    def replay(self, actions: List[Dict[str, Any]] = None, delay: float = 0.5) -> str:
        """캡처된 액션 재실행"""
        actions = actions or self.actions
        
        if not actions:
            return "❌ 재실행할 액션이 없습니다."
        
        print(f"\n🔄 {len(actions)}개 액션 재실행 시작...")
        
        for i, action in enumerate(actions, 1):
            print(f"  [{i}/{len(actions)}] ", end="")
            
            if action['type'] == 'click':
                print(f"클릭: {action['selector']}")
                h.web.click(action['selector'], self.session_id)
                
            elif action['type'] == 'input':
                print(f"입력: {action['selector']} = '{action['value']}'")
                h.web.type(action['selector'], action['value'], self.session_id, clear=True)
                
            elif action['type'] == 'keypress':
                if action['key'] == 'Enter':
                    print(f"Enter 키: {action['selector']}")
                    h.web.execute_js(f"""
                        const elem = document.querySelector('{action['selector']}');
                        if (elem) {{
                            const event = new KeyboardEvent('keydown', {{key: 'Enter', bubbles: true}});
                            elem.dispatchEvent(event);
                        }}
                    """, self.session_id)
            
            time.sleep(delay)
        
        return f"✅ {len(actions)}개 액션 재실행 완료!"
    
    def save_workflow(self, name: str) -> str:
        """워크플로우 저장"""
        workflow = {
            'name': name,
            'url': h.web.execute_js("return window.location.href", self.session_id)['data'],
            'actions': self.actions,
            'guidance': self.guidance,
            'created': datetime.now().isoformat(),
            'total_actions': len(self.actions)
        }
        
        filename = f'workflow_{name}_{int(time.time())}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        
        self.workflows[name] = workflow
        return f"💾 워크플로우 '{name}'이 {filename}에 저장되었습니다."
    
    def load_workflow(self, filename: str) -> Dict[str, Any]:
        """워크플로우 로드"""
        with open(filename, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        self.actions = workflow['actions']
        self.guidance = workflow['guidance']
        
        print(f"📂 워크플로우 '{workflow['name']}' 로드 완료")
        print(f"  • URL: {workflow.get('url', 'N/A')}")
        print(f"  • 액션 수: {len(self.actions)}")
        print(f"  • 생성일: {workflow.get('created', 'N/A')}")
        
        return workflow
    
    def close(self) -> None:
        """브라우저 종료"""
        if self.session_id:
            h.web.close(self.session_id)
            print("👋 브라우저가 종료되었습니다.")
            self.session_id = None


# 사용 예제
if __name__ == "__main__":
    print("=" * 60)
    print("🎯 WebRecorder 데모")
    print("=" * 60)
    
    # 레코더 생성
    recorder = WebRecorder()
    
    # 브라우저 시작
    recorder.start("https://www.google.com", headless=False)
    
    # 대화형 사용 예제
    print("\n💡 사용 가능한 명령어:")
    print("  recorder.guide('메시지')  - 가이드 메시지 표시")
    print("  recorder.wait(초)         - 대기")
    print("  recorder.get_actions()    - 액션 가져오기")
    print("  recorder.show_actions()   - 액션 목록 보기")
    print("  recorder.replay()         - 액션 재실행")
    print("  recorder.save_workflow('이름') - 워크플로우 저장")
    print("  recorder.close()          - 브라우저 종료")
    
    print("\n이제 REPL에서 recorder 객체를 사용하여 웹 자동화를 제어할 수 있습니다!")
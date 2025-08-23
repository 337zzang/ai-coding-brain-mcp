#!/usr/bin/env python3
"""
실시간 사용자 이벤트 캡처 - 개선된 버전
브라우저를 띄우고 실시간으로 사용자 액션을 모니터링합니다.
"""

import sys
import os
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))
import ai_helpers_new as h

def realtime_capture():
    session_id = f"realtime_{datetime.now().strftime('%H%M%S')}"
    
    print("🎯 실시간 사용자 이벤트 캡처")
    print("=" * 60)
    
    # 1. 브라우저 시작
    print("\n1️⃣ 브라우저 시작...")
    result = h.web.start(session_id, headless=False)
    if not result['ok']:
        print(f"❌ 실패: {result['error']}")
        return
    print("✅ 브라우저가 열렸습니다!")
    
    # 2. 테스트 페이지 생성
    print("\n2️⃣ 테스트 페이지 생성...")
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>이벤트 캡처 테스트</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            button { padding: 10px 20px; margin: 10px; font-size: 16px; }
            input { padding: 10px; margin: 10px; font-size: 16px; width: 300px; }
            #output { 
                border: 1px solid #ccc; 
                padding: 10px; 
                margin: 20px 0;
                min-height: 200px;
                background: #f5f5f5;
            }
            .event-item { 
                padding: 5px; 
                margin: 2px 0; 
                background: white;
                border-left: 3px solid #4CAF50;
            }
        </style>
    </head>
    <body>
        <h1>🎯 실시간 이벤트 캡처 테스트</h1>
        <p>아래 버튼과 입력창을 클릭하고 타이핑해보세요!</p>
        
        <div>
            <button id="btn1" onclick="addEvent('Button 1 clicked')">버튼 1</button>
            <button id="btn2" onclick="addEvent('Button 2 clicked')">버튼 2</button>
            <button id="btn3" onclick="addEvent('Button 3 clicked')">버튼 3</button>
        </div>
        
        <div>
            <input type="text" id="input1" placeholder="여기에 텍스트를 입력하세요..." />
            <input type="email" id="input2" placeholder="이메일을 입력하세요..." />
        </div>
        
        <div>
            <button onclick="clearEvents()">이벤트 초기화</button>
            <button onclick="showCaptured()">캡처된 이벤트 보기</button>
        </div>
        
        <h3>📊 실시간 이벤트 로그:</h3>
        <div id="output"></div>
        
        <script>
            // 이벤트 캡처 시스템 초기화
            window.capturedEvents = [];
            window.recordingMode = true;
            
            function addEvent(message) {
                const output = document.getElementById('output');
                const item = document.createElement('div');
                item.className = 'event-item';
                item.innerHTML = `[${new Date().toLocaleTimeString()}] ${message}`;
                output.appendChild(item);
            }
            
            function clearEvents() {
                document.getElementById('output').innerHTML = '';
                window.capturedEvents = [];
                addEvent('이벤트 로그가 초기화되었습니다.');
            }
            
            function showCaptured() {
                alert(`캡처된 이벤트: ${window.capturedEvents.length}개`);
                console.log('Captured Events:', window.capturedEvents);
            }
            
            // 모든 클릭 이벤트 캡처
            document.addEventListener('click', function(e) {
                const event = {
                    type: 'click',
                    target: e.target.tagName,
                    id: e.target.id || 'no-id',
                    text: e.target.innerText || '',
                    x: e.clientX,
                    y: e.clientY,
                    timestamp: new Date().toISOString()
                };
                window.capturedEvents.push(event);
                addEvent(`CLICK: ${event.target}#${event.id} at (${event.x}, ${event.y})`);
                console.log('Click captured:', event);
            }, true);
            
            // 키보드 이벤트 캡처
            document.addEventListener('keydown', function(e) {
                const event = {
                    type: 'keydown',
                    key: e.key,
                    target: e.target.tagName,
                    id: e.target.id || 'no-id',
                    value: e.target.value || '',
                    timestamp: new Date().toISOString()
                };
                window.capturedEvents.push(event);
                if (e.key.length === 1) {  // 일반 문자만 표시
                    addEvent(`KEY: "${e.key}" in ${event.target}#${event.id}`);
                }
                console.log('Key captured:', event);
            }, true);
            
            // 입력 이벤트 캡처
            document.addEventListener('input', function(e) {
                const event = {
                    type: 'input',
                    target: e.target.tagName,
                    id: e.target.id || 'no-id',
                    value: e.target.value,
                    timestamp: new Date().toISOString()
                };
                window.capturedEvents.push(event);
                addEvent(`INPUT: "${event.value}" in ${event.target}#${event.id}`);
                console.log('Input captured:', event);
            }, true);
            
            console.log('✅ Event capture system initialized!');
            addEvent('시스템 준비 완료! 버튼을 클릭하거나 텍스트를 입력해보세요.');
        </script>
    </body>
    </html>
    """
    
    # data: URL로 HTML 로드
    data_url = f"data:text/html;charset=utf-8,{test_html}"
    h.web.goto(data_url, session_id)
    print("✅ 테스트 페이지 로드 완료")
    
    # 3. 오버레이 활성화
    print("\n3️⃣ 오버레이 활성화...")
    h.web.activate_overlay(session_id)
    
    # 4. AI 스트리밍 시작
    print("\n4️⃣ AI 스트리밍 시작...")
    h.web.stream_to_ai(session_id)
    
    print("\n" + "="*60)
    print("📢 브라우저에서 다음을 수행해주세요:")
    print("   1. 버튼들을 클릭해보세요")
    print("   2. 입력창에 텍스트를 입력해보세요")
    print("   3. '캡처된 이벤트 보기' 버튼을 클릭해보세요")
    print("="*60)
    
    # 5. 실시간 모니터링 (60초)
    print("\n⏳ 60초 동안 실시간 모니터링...")
    start_time = time.time()
    last_count = 0
    
    while time.time() - start_time < 60:
        remaining = 60 - int(time.time() - start_time)
        
        # JavaScript에서 캡처된 이벤트 확인
        result = h.web.execute_js("return window.capturedEvents || [];", session_id)
        
        if result['ok'] and result['data']:
            current_count = len(result['data'])
            if current_count > last_count:
                print(f"\n🔴 새 이벤트 {current_count - last_count}개 캡처! (총 {current_count}개)")
                
                # 새 이벤트 출력
                for event in result['data'][last_count:current_count]:
                    if event['type'] == 'click':
                        print(f"   • CLICK: {event['target']}#{event['id']} ({event['x']}, {event['y']})")
                    elif event['type'] == 'keydown':
                        print(f"   • KEY: '{event['key']}' in {event['target']}#{event['id']}")
                    elif event['type'] == 'input':
                        print(f"   • INPUT: '{event['value'][:20]}...' in {event['target']}#{event['id']}")
                
                last_count = current_count
        
        print(f"\r⏱️ 남은 시간: {remaining:2d}초 | 캡처된 이벤트: {last_count}개", end="", flush=True)
        time.sleep(1)
    
    print("\n\n" + "="*60)
    print("📊 최종 결과")
    print("="*60)
    
    # 6. 최종 데이터 수집
    final_events = h.web.execute_js("return window.capturedEvents || [];", session_id)
    stream_data = h.web.get_stream_data(session_id)
    overlay_actions = h.web.get_overlay_actions(session_id)
    
    if final_events['ok']:
        events = final_events['data']
        print(f"\n✅ 총 {len(events)}개 이벤트 캡처됨!")
        
        # 이벤트 타입별 통계
        event_types = {}
        for event in events:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        print("\n📈 이벤트 타입별 통계:")
        for event_type, count in event_types.items():
            print(f"   • {event_type}: {count}개")
        
        # 결과 저장
        results = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'total_events': len(events),
            'event_types': event_types,
            'captured_events': events,
            'stream_data': stream_data['data'] if stream_data['ok'] else None,
            'overlay_actions': overlay_actions['data'] if overlay_actions['ok'] else None
        }
        
        filename = f'realtime_capture_{session_id}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 결과가 {filename}에 저장되었습니다.")
        
        # MCP에서 확인할 수 있도록 요약 출력
        print("\n📝 MCP에서 확인 가능한 데이터:")
        print(f"   • 파일명: {filename}")
        print(f"   • 이벤트 수: {len(events)}")
        print(f"   • 첫 이벤트: {events[0] if events else 'None'}")
    
    # 7. 브라우저 유지
    print("\n브라우저를 계속 사용하려면 Enter, 종료하려면 'q' 입력:")
    choice = input()
    
    if choice.lower() != 'q':
        print("브라우저를 열어둡니다. 수동으로 닫아주세요.")
        time.sleep(60)
    
    # 정리
    h.web.stop_streaming(session_id)
    h.web.close(session_id)
    print("✅ 완료!")

if __name__ == "__main__":
    realtime_capture()
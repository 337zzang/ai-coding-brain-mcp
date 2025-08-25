#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🚀 Enhanced JSON REPL Session with Smart Memory Management
Version: 4.0.0

Features:
- Real-time memory monitoring
- Automatic garbage collection
- Variable limit management  
- Memory usage reporting in stdout
"""

import sys
import os
import json
import time
import gc
import io
import traceback
import threading
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Import memory facade
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory_facade import MEMORY_MANAGER, execute_code_with_memory_check, get_memory_report

# Import original components
from repl_core import EnhancedREPLSession, ExecutionMode

# Windows UTF-8 configuration
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass
    os.environ['PYTHONIOENCODING'] = 'utf-8'

class SmartSessionPool:
    """메모리 관리가 강화된 세션 풀"""
    
    def __init__(self):
        self.session = None
        self.namespace = {}
        self.lock = threading.RLock()
        
        # 메모리 매니저 연결
        self.memory_manager = MEMORY_MANAGER
        
        # 통계
        self.stats = {
            'total_executions': 0,
            'memory_cleanups': 0,
            'peak_memory_mb': 0
        }
    
    def get_or_create_session(self) -> EnhancedREPLSession:
        """세션 가져오기 또는 생성"""
        with self.lock:
            if self.session is None:
                self.session = EnhancedREPLSession(
                    mode=ExecutionMode.MEMORY_OPTIMIZED,
                    enable_caching=True
                )
                self._init_namespace()
            return self.session
    
    def _init_namespace(self):
        """네임스페이스 초기화"""
        self.namespace = {
            '__builtins__': __builtins__,
            '__name__': '__main__',
            'sys': sys,
            'os': os,
            'Path': Path,
            'datetime': datetime,
            'gc': gc,
            # 메모리 관리 함수 추가
            'mem_status': self.memory_manager.get_memory_status,
            'mem_clean': self.memory_manager.clean_memory,
            'mem_report': lambda: print(get_memory_report()),
            'set_var': self.memory_manager.set_variable,
            'get_var': self.memory_manager.get_variable,
        }
    
    def execute_with_memory_management(self, code: str) -> Dict[str, Any]:
        """메모리 관리가 포함된 코드 실행"""
        
        # 실행 전 메모리 체크
        before_status = self.memory_manager.get_memory_status()
        
        # stdout에 메모리 정보 출력
        print(f"\n{'='*50}", file=sys.stderr)
        print(f"[MEM] 실행 시작", file=sys.stderr)
        print(f"[MEM] 메모리: {before_status['used_mb']:.1f}MB / "
              f"{before_status['percent_used']:.1f}%", file=sys.stderr)
        print(f"[MEM] 변수: {before_status['variables_count']}개 / "
              f"{self.memory_manager.MAX_VARIABLES}개", file=sys.stderr)
        
        # 메모리 임계값 체크
        if before_status['critical']:
            print(f"[MEM] ⚠️ 메모리 위험! 자동 정리 시작...", file=sys.stderr)
            clean_result = self.memory_manager.clean_memory(force=True)
            print(f"[MEM] ✅ {clean_result['memory_freed_mb']:.1f}MB 해제, "
                  f"{clean_result['cleaned_variables']}개 변수 정리", file=sys.stderr)
            self.stats['memory_cleanups'] += 1
        elif before_status['warning']:
            print(f"[MEM] 🟡 메모리 주의 수준", file=sys.stderr)
        
        print(f"{'='*50}", file=sys.stderr)
        
        # 실제 코드 실행
        try:
            # 출력 캡처
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            # 네임스페이스에서 실행
            exec(code, self.namespace)
            
            # 출력 가져오기
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            # 실행 후 메모리 상태
            after_status = self.memory_manager.get_memory_status()
            memory_delta = after_status['used_mb'] - before_status['used_mb']
            
            # 통계 업데이트
            self.stats['total_executions'] += 1
            if after_status['used_mb'] > self.stats['peak_memory_mb']:
                self.stats['peak_memory_mb'] = after_status['used_mb']
            
            # 메모리 변화 출력
            print(f"\n[MEM] 실행 완료", file=sys.stderr)
            print(f"[MEM] 메모리 변화: {memory_delta:+.1f}MB", file=sys.stderr)
            print(f"[MEM] 현재: {after_status['used_mb']:.1f}MB / "
                  f"{after_status['percent_used']:.1f}%", file=sys.stderr)
            
            # 메모리 급증 경고
            if memory_delta > 100:
                print(f"[MEM] ⚠️ 메모리 급증 감지!", file=sys.stderr)
            
            return {
                'status': 'success',
                'stdout': output,  # Changed from 'output' to 'stdout' for MCP compatibility
                'stderr': '',  # Add stderr for compatibility
                'memory': {
                    'before_mb': before_status['used_mb'],
                    'after_mb': after_status['used_mb'],
                    'delta_mb': round(memory_delta, 2),
                    'percent': after_status['percent_used'],
                    'variables': after_status['variables_count']
                },
                'stats': self.stats
            }
            
        except Exception as e:
            sys.stdout = old_stdout if 'old_stdout' in locals() else sys.stdout
            
            # 에러 시에도 메모리 상태 확인
            error_status = self.memory_manager.get_memory_status()
            
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'memory': {
                    'current_mb': error_status['used_mb'],
                    'percent': error_status['percent_used'],
                    'variables': error_status['variables_count']
                }
            }
    
    def get_stats_report(self) -> str:
        """통계 리포트 생성"""
        return f"""
📊 세션 통계
- 총 실행: {self.stats['total_executions']}회
- 메모리 정리: {self.stats['memory_cleanups']}회
- 최대 메모리: {self.stats['peak_memory_mb']:.1f}MB
"""

# 전역 세션 풀
SESSION_POOL = SmartSessionPool()

def execute_code(code: str, agent_id: Optional[str] = None, 
                session_id: Optional[str] = None) -> Dict[str, Any]:
    """메모리 관리가 강화된 코드 실행"""
    
    # 세션 풀에서 실행
    result = SESSION_POOL.execute_with_memory_management(code)
    
    # 주기적으로 통계 출력 (10회마다)
    if SESSION_POOL.stats['total_executions'] % 10 == 0:
        print(SESSION_POOL.get_stats_report(), file=sys.stderr)
        print(get_memory_report(), file=sys.stderr)
    
    return result

def process_json_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """JSON-RPC 요청 처리"""
    try:
        # 코드 추출
        params = request.get('params', {})
        code = params.get('code', '')
        agent_id = params.get('agent_id')
        session_id = params.get('session_id')
        
        # 코드 실행
        result = execute_code(code, agent_id, session_id)
        
        # 응답 생성
        if result['status'] == 'success':
            return {
                'jsonrpc': '2.0',
                'id': request.get('id', 1),
                'result': {
                    'output': result['output'],
                    'memory': result['memory'],
                    'stats': result['stats']
                }
            }
        else:
            return {
                'jsonrpc': '2.0',
                'id': request.get('id', 1),
                'error': {
                    'code': -32603,
                    'message': result['error'],
                    'data': {
                        'traceback': result.get('traceback'),
                        'memory': result['memory']
                    }
                }
            }
    except Exception as e:
        return {
            'jsonrpc': '2.0',
            'id': request.get('id', 1),
            'error': {
                'code': -32603,
                'message': str(e)
            }
        }

def main():
    """메인 실행 루프"""
    print("Enhanced JSON REPL with Memory Management", file=sys.stderr)
    print(f"Memory Limits: {MEMORY_MANAGER.MAX_VARIABLES} vars, "
          f"{MEMORY_MANAGER.MAX_VAR_SIZE_MB}MB/var", file=sys.stderr)
    print(f"Thresholds: Warning {MEMORY_MANAGER.MEMORY_WARNING_THRESHOLD}%, "
          f"Critical {MEMORY_MANAGER.MEMORY_CRITICAL_THRESHOLD}%", file=sys.stderr)
    print("Ready for requests...", file=sys.stderr)
    
    while True:
        try:
            # 입력 읽기
            line = sys.stdin.readline()
            if not line:
                break
            
            # JSON 파싱
            request = json.loads(line.strip())
            
            # 요청 처리
            response = process_json_request(request)
            
            # 응답 전송
            print(json.dumps(response, ensure_ascii=False))
            sys.stdout.flush()
            
        except KeyboardInterrupt:
            break
        except json.JSONDecodeError as e:
            error_response = {
                'jsonrpc': '2.0',
                'error': {
                    'code': -32700,
                    'message': f'Parse error: {str(e)}'
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
    
    print("\nSession ended", file=sys.stderr)
    print(SESSION_POOL.get_stats_report(), file=sys.stderr)
    print(get_memory_report(), file=sys.stderr)

if __name__ == "__main__":
    main()
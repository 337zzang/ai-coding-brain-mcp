#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🚀 Shared Session Mode for Workflow Continuity
Version: 1.0.0

Purpose: Enable data sharing between agents while maintaining safety
"""

import sys
import time
from typing import Dict, Any, Optional
from pathlib import Path

class WorkflowSession:
    """단일 공유 세션으로 에이전트 간 데이터 전달"""
    
    def __init__(self):
        # 공유 데이터 저장소
        self.shared_data = {}
        
        # 에이전트별 실행 기록
        self.execution_history = []
        
        # 워크플로우 상태
        self.workflow_state = {
            'current_agent': None,
            'previous_agent': None,
            'step_count': 0
        }
        
        # 공통 네임스페이스 (한 번만 로드)
        self.base_namespace = self._initialize_namespace()
    
    def _initialize_namespace(self) -> Dict[str, Any]:
        """공통 네임스페이스 초기화 - 한 번만 import"""
        namespace = {}
        
        # AI helpers 로드 (한 번만!)
        exec("import ai_helpers_new as h", namespace)
        exec("import sys", namespace)
        exec("import os", namespace)
        exec("from pathlib import Path", namespace)
        exec("import json", namespace)
        exec("import time", namespace)
        
        # 공유 데이터 접근 함수
        namespace['shared'] = self.shared_data
        namespace['get_shared'] = lambda key: self.shared_data.get(key)
        namespace['set_shared'] = lambda key, value: self.shared_data.update({key: value})
        namespace['list_shared'] = lambda: list(self.shared_data.keys())
        
        # 워크플로우 함수
        namespace['get_workflow_state'] = lambda: self.workflow_state
        namespace['get_previous_result'] = self._get_previous_result
        
        return namespace
    
    def execute_for_agent(self, code: str, agent_id: str) -> Dict[str, Any]:
        """특정 에이전트를 위한 코드 실행"""
        
        # 워크플로우 상태 업데이트
        self.workflow_state['previous_agent'] = self.workflow_state['current_agent']
        self.workflow_state['current_agent'] = agent_id
        self.workflow_state['step_count'] += 1
        
        # 실행 네임스페이스 준비 (base + agent 정보)
        namespace = self.base_namespace.copy()
        namespace['agent_id'] = agent_id
        namespace['step'] = self.workflow_state['step_count']
        
        # 실행 시작
        start_time = time.time()
        stdout_buffer = []
        stderr_buffer = []
        
        try:
            # stdout/stderr 캡처
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, namespace)
            
            stdout_result = stdout_capture.getvalue()
            stderr_result = stderr_capture.getvalue()
            
            # 실행 성공
            result = {
                'success': True,
                'agent_id': agent_id,
                'step': self.workflow_state['step_count'],
                'stdout': stdout_result,
                'stderr': stderr_result,
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'shared_keys': list(self.shared_data.keys()),
                'workflow_state': self.workflow_state.copy()
            }
            
        except Exception as e:
            result = {
                'success': False,
                'agent_id': agent_id,
                'step': self.workflow_state['step_count'],
                'error': str(e),
                'stdout': '',
                'stderr': traceback.format_exc(),
                'execution_time_ms': int((time.time() - start_time) * 1000)
            }
        
        # 실행 기록 저장
        self.execution_history.append({
            'agent_id': agent_id,
            'timestamp': time.time(),
            'success': result['success'],
            'shared_snapshot': list(self.shared_data.keys())
        })
        
        return result
    
    def _get_previous_result(self) -> Optional[Any]:
        """이전 에이전트의 결과 가져오기"""
        if self.workflow_state['previous_agent']:
            key = f"{self.workflow_state['previous_agent']}_result"
            return self.shared_data.get(key)
        return None
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """워크플로우 전체 요약"""
        return {
            'total_steps': self.workflow_state['step_count'],
            'agents_executed': [h['agent_id'] for h in self.execution_history],
            'shared_data_keys': list(self.shared_data.keys()),
            'current_agent': self.workflow_state['current_agent'],
            'execution_count': len(self.execution_history)
        }
    
    def clear_shared_data(self):
        """공유 데이터 초기화"""
        self.shared_data.clear()
        print(f"✅ 공유 데이터 초기화 완료")
    
    def reset_workflow(self):
        """워크플로우 완전 초기화"""
        self.shared_data.clear()
        self.execution_history.clear()
        self.workflow_state = {
            'current_agent': None,
            'previous_agent': None,
            'step_count': 0
        }
        print(f"✅ 워크플로우 리셋 완료")


# 전역 워크플로우 세션 인스턴스
WORKFLOW_SESSION = WorkflowSession()


def execute_in_workflow(code: str, agent_id: str = "default") -> Dict[str, Any]:
    """워크플로우 세션에서 코드 실행"""
    return WORKFLOW_SESSION.execute_for_agent(code, agent_id)


# 사용 예시
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Shared Session Mode - Workflow Example")
    print("=" * 60)
    
    # 1. Analyzer 실행
    analyzer_code = """
print("🔍 Analyzing code...")
analysis_result = {
    'complexity': 'medium',
    'lines': 150,
    'functions': 10
}
set_shared('analysis', analysis_result)
print(f"Analysis saved: {analysis_result}")
"""
    
    result1 = execute_in_workflow(analyzer_code, "code-analyzer")
    print(f"\n1. Analyzer: {result1['success']}")
    
    # 2. Validator 실행 (analyzer 결과 활용)
    validator_code = """
print("✅ Validating based on analysis...")
analysis = get_shared('analysis')
print(f"Retrieved analysis: {analysis}")

validation_result = {
    'valid': True,
    'issues': [],
    'complexity_ok': analysis['complexity'] != 'high'
}
set_shared('validation', validation_result)
print(f"Validation complete: {validation_result}")
"""
    
    result2 = execute_in_workflow(validator_code, "code-validator")
    print(f"2. Validator: {result2['success']}")
    
    # 3. Optimizer 실행 (모든 이전 결과 활용)
    optimizer_code = """
print("⚡ Optimizing based on all previous results...")
analysis = get_shared('analysis')
validation = get_shared('validation')

print(f"Using analysis: {analysis}")
print(f"Using validation: {validation}")

if validation['valid'] and analysis['complexity'] == 'medium':
    optimization = {
        'optimized': True,
        'improvements': ['reduced complexity', 'better performance']
    }
else:
    optimization = {'optimized': False, 'reason': 'Not suitable for optimization'}

set_shared('optimization', optimization)
print(f"Optimization result: {optimization}")
"""
    
    result3 = execute_in_workflow(optimizer_code, "code-optimizer")
    print(f"3. Optimizer: {result3['success']}")
    
    # 워크플로우 요약
    print("\n" + "=" * 60)
    print("📊 Workflow Summary:")
    summary = WORKFLOW_SESSION.get_workflow_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n📦 Final Shared Data:")
    for key, value in WORKFLOW_SESSION.shared_data.items():
        print(f"  {key}: {value}")
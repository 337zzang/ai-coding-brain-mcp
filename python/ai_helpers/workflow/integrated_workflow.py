
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 프로토콜 임포트 경로 추가
sys.path.append('./python')
from ai_helpers.protocols.stdout_protocol import StdoutProtocol, IDGenerator

class IntegratedWorkflowManager:
    '''워크플로우와 프로토콜을 통합하는 관리자 클래스'''

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.id_generator = IDGenerator()
        self.protocol = StdoutProtocol(self.id_generator)

        # 워크플로우 상태
        self.workflow_state = {
            'plan_id': None,
            'tasks': [],
            'current_task': None,
            'completed_tasks': 0,
            'total_tasks': 0
        }

        # 실행 추적 (프로토콜 연동)
        self.execution_tracker = {
            'executions': [],
            'performance_metrics': {},
            'error_history': []
        }

        # 데이터 공유 레이어
        self.shared_data = {
            'session_id': self.id_generator.generate_id('SES', project_name),
            'checkpoints': {},
            'cache': {}
        }

    def start_workflow(self, plan_name: str, tasks: List[Dict]) -> str:
        '''워크플로우 시작 - 프로토콜을 통해 추적'''
        # 프로토콜로 섹션 시작
        workflow_section = self.protocol.section(f"WORKFLOW:{plan_name}")

        # 워크플로우 ID 생성
        plan_id = self.id_generator.generate_id('WF', plan_name)

        # 상태 초기화
        self.workflow_state.update({
            'plan_id': plan_id,
            'plan_name': plan_name,
            'tasks': tasks,
            'total_tasks': len(tasks),
            'started_at': datetime.now().isoformat()
        })

        # 프로토콜로 데이터 출력
        self.protocol.data('workflow_id', plan_id)
        self.protocol.data('total_tasks', len(tasks))

        # 실행 추적 시작
        exec_id = self.protocol.exec_start(f"workflow_{plan_name}")
        self.workflow_state['exec_id'] = exec_id

        return plan_id

    def execute_task(self, task: Dict) -> Dict:
        '''단일 작업 실행 - 프로토콜로 추적'''
        task_id = task.get('id', self.id_generator.generate_id('TASK'))

        # 작업 섹션 시작
        task_section = self.protocol.section(f"TASK:{task['title']}")

        # 실행 추적 시작
        exec_id = self.protocol.exec_start(f"task_{task_id}")

        try:
            # 작업 실행 (실제 구현은 task type에 따라 다름)
            result = self._perform_task(task)

            # 성공 기록
            self.protocol.exec_end(exec_id, 'success', duration)
            self.protocol.data('result', result)

            # 진행 상황 업데이트
            self.workflow_state['completed_tasks'] += 1
            progress = (self.workflow_state['completed_tasks'] / 
                       self.workflow_state['total_tasks'] * 100)

            self.protocol.progress(
                self.workflow_state['plan_id'],
                self.workflow_state['completed_tasks'],
                self.workflow_state['total_tasks']
            )

            return {
                'task_id': task_id,
                'status': 'success',
                'result': result,
                'exec_id': exec_id
            }

        except Exception as e:
            # 오류 처리
            self.protocol.error(str(e), type(e).__name__)
            self.protocol.exec_end(exec_id, 'error', duration)

            # 오류 기록
            self.execution_tracker['error_history'].append({
                'task_id': task_id,
                'error': str(e),
                'timestamp': time.time()
            })

            return {
                'task_id': task_id,
                'status': 'error',
                'error': str(e),
                'exec_id': exec_id
            }

        finally:
            # 섹션 종료
            self.protocol.end_section()

    def _perform_task(self, task: Dict) -> Any:
        '''실제 작업 수행 로직'''
        # 여기서 helpers 함수들을 활용
        task_type = task.get('type', 'general')

        if task_type == 'code_analysis':
            # 코드 분석 작업
            return self._analyze_code(task)
        elif task_type == 'file_operation':
            # 파일 작업
            return self._file_operation(task)
        elif task_type == 'test_execution':
            # 테스트 실행
            return self._run_tests(task)
        else:
            # 일반 작업
            return {'completed': True, 'timestamp': time.time()}

    def checkpoint(self, name: str, data: Any) -> str:
        '''체크포인트 생성 - 프로토콜과 워크플로우 양쪽에 저장'''
        checkpoint_id = self.protocol.checkpoint(name, data)

        # 공유 데이터에 저장
        self.shared_data['checkpoints'][name] = {
            'id': checkpoint_id,
            'data': data,
            'timestamp': time.time()
        }

        return checkpoint_id

    def get_status(self) -> Dict:
        '''현재 상태 조회'''
        return {
            'workflow': self.workflow_state,
            'execution': {
                'total': len(self.execution_tracker['executions']),
                'errors': len(self.execution_tracker['error_history'])
            },
            'shared_data': {
                'session_id': self.shared_data['session_id'],
                'checkpoints': len(self.shared_data['checkpoints']),
                'cache_size': len(self.shared_data['cache'])
            }
        }

    def next_action(self, action: str, params: Dict) -> None:
        '''다음 작업 지시 - 프로토콜 활용'''
        self.protocol.next_action(action, params)

        # 워크플로우 상태 업데이트
        self.workflow_state['next_action'] = {
            'action': action,
            'params': params,
            'timestamp': time.time()
        }

    def _analyze_code(self, task: Dict) -> Dict:
        '''코드 분석 작업 구현'''
        # helpers 활용
        file_path = task.get('file_path', '.')
        pattern = task.get('pattern', '')

        if pattern:
            results = helpers.search_code_content(file_path, pattern, "*.py")
            return {'matches': len(results.get('results', [])), 'results': results}
        else:
            structure = helpers.scan_directory_dict(file_path)
            return {'files': len(structure['files']), 'structure': structure}

    def _file_operation(self, task: Dict) -> Dict:
        '''파일 작업 구현'''
        operation = task.get('operation')

        if operation == 'read':
            content = helpers.read_file(task['path'])
            return {'content_length': len(str(content))}
        elif operation == 'write':
            helpers.create_file(task['path'], task['content'])
            return {'written': True}
        elif operation == 'search':
            results = helpers.search_files_advanced(task['path'], task['pattern'])
            return {'found': len(results.get('results', []))}

        return {'operation': operation, 'completed': True}

    def _run_tests(self, task: Dict) -> Dict:
        '''테스트 실행 구현'''
        test_file = task.get('test_file')

        # 실제 테스트 실행 로직
        # 여기서는 시뮬레이션
        return {
            'tests_run': 10,
            'passed': 9,
            'failed': 1,
            'coverage': '85%'
        }

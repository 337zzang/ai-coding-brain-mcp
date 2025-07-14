"""
Stdout Protocol v3.0 - 표준화된 출력 프로토콜
AI Coding Brain MCP 프로젝트용 stdout 표준화 시스템
"""

import time
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class IDGenerator:
    """고유 ID 생성 및 관리"""

    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.id_map: Dict[str, Dict[str, Any]] = {}  # ID -> 데이터 매핑

    def generate_id(self, prefix: str = "ID", context: Optional[Any] = None) -> str:
        """컨텍스트 기반 고유 ID 생성

        형식: PREFIX_TIMESTAMP_COUNTER_HASH
        - PREFIX: 작업 유형 (SEC, DATA, EXEC, PROG, ERR 등)
        - TIMESTAMP: 밀리초 단위 타임스탬프
        - COUNTER: 동일 유형 내 순번 (4자리)
        - HASH: 컨텍스트 해시 (선택적, 6자리)
        """
        timestamp = int(time.time() * 1000)

        if prefix not in self.counters:
            self.counters[prefix] = 0
        self.counters[prefix] += 1

        # 고유 ID 생성
        if context:
            hash_part = hashlib.md5(str(context).encode()).hexdigest()[:6]
            id_value = f"{prefix}_{timestamp}_{self.counters[prefix]:04d}_{hash_part}"
        else:
            id_value = f"{prefix}_{timestamp}_{self.counters[prefix]:04d}"

        return id_value

    def register_id(self, id_value: str, data: Any) -> None:
        """ID와 데이터 연결"""
        self.id_map[id_value] = {
            'data': data,
            'timestamp': time.time(),
            'access_count': 0
        }

    def get_by_id(self, id_value: str) -> Optional[Any]:
        """ID로 데이터 조회"""
        if id_value in self.id_map:
            self.id_map[id_value]['access_count'] += 1
            return self.id_map[id_value]['data']
        return None


class StdoutProtocol:
    """표준화된 출력 프로토콜

    표준 마커:
    - [SECTION:id:name] / [/SECTION:id] - 섹션 관리
    - [DATA:id:key:value] - 데이터 출력
    - [EXEC:id:function:timestamp] / [/EXEC:id:status:duration] - 실행 추적
    - [PROGRESS:id:current/total:percentage%] - 진행 상황
    - [CHECKPOINT:id:name:size] - 체크포인트
    - [ERROR:id:type:message] - 오류 처리
    - [NEXT:id:action:params] - 다음 작업 지시
    """

    VERSION = "3.0"

    def __init__(self, id_gen: Optional[IDGenerator] = None):
        self.id_gen = id_gen or IDGenerator()
        self.current_section: Optional[str] = None
        self.section_stack: List[Tuple[str, str]] = []
        self.output_history: List[Dict[str, Any]] = []

    def section(self, name: str) -> str:
        """섹션 시작"""
        section_id = self.id_gen.generate_id("SEC", name)
        self.section_stack.append((section_id, name))
        self.current_section = section_id

        output = f"[SECTION:{section_id}:{name}]"
        self._record_output(output)
        print(output)
        return section_id

    def end_section(self) -> None:
        """섹션 종료"""
        if self.section_stack:
            section_id, name = self.section_stack.pop()
            output = f"[/SECTION:{section_id}]"
            self._record_output(output)
            print(output)

            if self.section_stack:
                self.current_section = self.section_stack[-1][0]
            else:
                self.current_section = None

    def data(self, key: str, value: Any) -> str:
        """데이터 출력"""
        data_id = self.id_gen.generate_id("DATA", f"{key}:{value}")
        self.id_gen.register_id(data_id, {'key': key, 'value': value})

        output = f"[DATA:{data_id}:{key}:{value}]"
        self._record_output(output)
        print(output)
        return data_id

    def exec_start(self, function_name: str) -> str:
        """실행 시작"""
        exec_id = self.id_gen.generate_id("EXEC", function_name)
        timestamp = datetime.now().isoformat()

        output = f"[EXEC:{exec_id}:{function_name}:{timestamp}]"
        self._record_output(output)
        print(output)
        return exec_id

    def exec_end(self, exec_id: str, status: str, duration: float) -> None:
        """실행 종료"""
        output = f"[/EXEC:{exec_id}:{status}:{duration:.3f}s]"
        self._record_output(output)
        print(output)

    def progress(self, current: int, total: int, context: Optional[str] = None) -> str:
        """진행 상황"""
        progress_id = self.id_gen.generate_id("PROG", context)
        percentage = int((current / total) * 100) if total > 0 else 0

        output = f"[PROGRESS:{progress_id}:{current}/{total}:{percentage}%]"
        self._record_output(output)
        print(output)
        return progress_id

    def error(self, error_type: str, message: str) -> str:
        """오류 출력"""
        error_id = self.id_gen.generate_id("ERR", error_type)
        self.id_gen.register_id(error_id, {
            'type': error_type,
            'message': message,
            'timestamp': time.time()
        })

        output = f"[ERROR:{error_id}:{error_type}:{message}]"
        self._record_output(output)
        print(output)
        return error_id

    def next_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> str:
        """다음 액션 지시"""
        next_id = self.id_gen.generate_id("NEXT", action)
        params_str = json.dumps(params) if params else "{}"

        output = f"[NEXT:{next_id}:{action}:{params_str}]"
        self._record_output(output)
        print(output)
        return next_id

    def checkpoint(self, name: str, data: Any) -> str:
        """체크포인트 저장"""
        checkpoint_id = self.id_gen.generate_id("CKPT", name)

        # 데이터 저장
        self.id_gen.register_id(checkpoint_id, {
            'name': name,
            'data': data,
            'timestamp': time.time()
        })

        data_size = len(str(data))
        output = f"[CHECKPOINT:{checkpoint_id}:{name}:{data_size}]"
        self._record_output(output)
        print(output)
        return checkpoint_id

    def cache_hit(self, key: str) -> str:
        """캐시 적중"""
        cache_id = self.id_gen.generate_id("CACHE", f"hit_{key}")
        output = f"[CACHE_HIT:{cache_id}:{key}]"
        self._record_output(output)
        print(output)
        return cache_id

    def cache_miss(self, key: str) -> str:
        """캐시 미스"""
        cache_id = self.id_gen.generate_id("CACHE", f"miss_{key}")
        output = f"[CACHE_MISS:{cache_id}:{key}]"
        self._record_output(output)
        print(output)
        return cache_id

    def cache_save(self, key: str, ttl: int = 300) -> str:
        """캐시 저장"""
        cache_id = self.id_gen.generate_id("CACHE", f"save_{key}")
        output = f"[CACHE_SAVE:{cache_id}:{key}:{ttl}]"
        self._record_output(output)
        print(output)
        return cache_id

    def _record_output(self, output: str) -> None:
        """출력 히스토리 기록"""
        self.output_history.append({
            'output': output,
            'timestamp': time.time(),
            'section': self.current_section
        })


class ExecutionTracker:
    """ID 기반 실행 추적"""

    def __init__(self, protocol: StdoutProtocol):
        self.protocol = protocol
        self.execution_graph: Dict[str, List[str]] = {}  # 실행 관계 그래프
        self.execution_timeline: List[Dict[str, Any]] = []  # 시간순 실행 기록

    def track(self, func):
        """데코레이터: 함수 실행 추적"""
        def wrapper(*args, **kwargs):
            # 실행 시작
            exec_id = self.protocol.exec_start(func.__name__)
            start_time = time.time()

            # 실행 정보 기록
            exec_info = {
                'id': exec_id,
                'function': func.__name__,
                'args': str(args)[:50],
                'kwargs': str(kwargs)[:50],
                'start_time': start_time,
                'parent_section': self.protocol.current_section
            }

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # 성공 기록
                exec_info['status'] = 'success'
                exec_info['duration'] = duration
                exec_info['result_type'] = type(result).__name__

                self.protocol.exec_end(exec_id, 'success', duration)

            except Exception as e:
                duration = time.time() - start_time

                # 오류 기록
                exec_info['status'] = 'error'
                exec_info['duration'] = duration
                exec_info['error'] = str(e)

                error_id = self.protocol.error(type(e).__name__, str(e)[:100])
                exec_info['error_id'] = error_id

                self.protocol.exec_end(exec_id, 'error', duration)
                raise

            finally:
                # 타임라인에 추가
                self.execution_timeline.append(exec_info)

                # 관계 그래프 업데이트
                if self.protocol.current_section:
                    if self.protocol.current_section not in self.execution_graph:
                        self.execution_graph[self.protocol.current_section] = []
                    self.execution_graph[self.protocol.current_section].append(exec_id)

            return result

        return wrapper


def query_history(protocol: StdoutProtocol, 
                 pattern: Optional[str] = None, 
                 id_prefix: Optional[str] = None, 
                 time_range: Optional[Tuple[float, float]] = None) -> List[Dict[str, Any]]:
    """stdout 히스토리 조회"""
    results = []

    for record in protocol.output_history:
        # 패턴 매칭
        if pattern and pattern not in record['output']:
            continue

        # ID 접두사 필터
        if id_prefix and not any(f"{id_prefix}_" in record['output'] for id_prefix in [id_prefix]):
            continue

        # 시간 범위 필터
        if time_range:
            start, end = time_range
            if not (start <= record['timestamp'] <= end):
                continue

        results.append(record)

    return results


# 싱글톤 인스턴스 생성
_id_generator = IDGenerator()
_stdout_protocol = StdoutProtocol(_id_generator)
_execution_tracker = ExecutionTracker(_stdout_protocol)

# 편의 함수들
def get_protocol() -> StdoutProtocol:
    """전역 프로토콜 인스턴스 반환"""
    return _stdout_protocol

def get_id_generator() -> IDGenerator:
    """전역 ID 생성기 반환"""
    return _id_generator

def get_tracker() -> ExecutionTracker:
    """전역 실행 추적기 반환"""
    return _execution_tracker

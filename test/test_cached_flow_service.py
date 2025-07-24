# test_cached_flow_service.py
'''
CachedFlowService 단위 테스트
'''

import os
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
import pytest
import sys

# 테스트를 위한 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from ai_helpers_new.service.cached_flow_service import CachedFlowService, FlowCache
from ai_helpers_new.domain.models import Flow, Plan, Task
from ai_helpers_new.exceptions import ValidationError, StorageError


class TestFlowCache:
    """FlowCache 단위 테스트"""

    def test_cache_basic_operations(self):
        cache = FlowCache()

        # 빈 캐시 테스트
        assert cache.get('test_id') is None

        # Flow 모의 객체
        flow = Flow(
            id='test_id',
            name='Test Flow',
            plans={},
            created_at=datetime.now().isoformat()
        )

        # 캐시 저장
        cache.put('test_id', flow, 1000.0)

        # 캐시 조회
        cached = cache.get('test_id')
        assert cached is not None
        assert cached.id == 'test_id'
        assert cached.name == 'Test Flow'

    def test_cache_invalidation(self):
        cache = FlowCache()

        flow1 = Flow(id='flow1', name='Flow 1', plans={})
        flow2 = Flow(id='flow2', name='Flow 2', plans={})

        cache.put('flow1', flow1, 1000.0)
        cache.put('flow2', flow2, 1000.0)

        # 특정 항목 무효화
        cache.invalidate('flow1')
        assert cache.get('flow1') is None
        assert cache.get('flow2') is not None

        # 전체 무효화
        cache.invalidate()
        assert cache.get('flow2') is None

    def test_cache_validity_check(self):
        cache = FlowCache()
        flow = Flow(id='test', name='Test', plans={})

        # 캐시 저장 (mtime=1000)
        cache.put('test', flow, 1000.0)

        # 같은 시간 - 유효
        assert cache.is_valid('test', 1000.0) is True

        # 이전 시간 - 유효
        assert cache.is_valid('test', 999.0) is True

        # 이후 시간 - 무효
        assert cache.is_valid('test', 1001.0) is False



    def test_cache_ttl_expiration(self):
        """TTL 만료 테스트"""
        import time

        # 짧은 TTL로 캐시 생성 (1초)
        cache = FlowCache(ttl_seconds=1)

        # 데이터 저장
        test_data = {"key": "value"}
        cache.put("test_ttl", test_data, datetime.now())

        # 즉시 확인 - 데이터가 있어야 함
        assert cache.get("test_ttl") == test_data
        assert cache.is_valid("test_ttl", datetime.now())

        # 1.5초 대기
        time.sleep(1.5)

        # TTL 만료 후 - 데이터가 없어야 함
        assert cache.get("test_ttl") is None
        assert not cache.is_valid("test_ttl", datetime.now())

    def test_cache_memory_limit(self):
        """메모리 제한 테스트"""
        # 작은 메모리 제한으로 캐시 생성 (3개 항목만)
        cache = FlowCache(max_size=3)

        # 4개 항목 추가
        for i in range(4):
            cache.put(f"key_{i}", {f"data": f"value_{i}"}, datetime.now())

        # 첫 번째 항목은 제거되어야 함 (LRU)
        assert cache.get("key_0") is None
        assert cache.get("key_1") is not None
        assert cache.get("key_2") is not None
        assert cache.get("key_3") is not None

    def test_cache_statistics(self):
        """캐시 통계 테스트"""
        cache = FlowCache()

        # 초기 상태
        stats = cache.get_statistics()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 0.0

        # 데이터 추가 및 조회
        cache.put("key1", {"data": "value1"}, datetime.now())

        # 히트
        cache.get("key1")  # hit
        cache.get("key1")  # hit

        # 미스
        cache.get("key2")  # miss
        cache.get("key3")  # miss
        cache.get("key4")  # miss

        # 통계 확인
        stats = cache.get_statistics()
        assert stats['hits'] == 2
        assert stats['misses'] == 3
        assert stats['hit_rate'] == 0.4  # 2/5 = 0.4


class TestCachedFlowService:
    """CachedFlowService 통합 테스트"""

    @pytest.fixture
    def temp_dir(self):
        """임시 디렉토리 생성"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def service(self, temp_dir):
        """테스트용 서비스 인스턴스"""
        return CachedFlowService(base_path=temp_dir)

    def test_empty_flows(self, service):
        """빈 상태 테스트"""
        flows = service.list_flows()
        assert flows == []

        flow = service.get_flow('non_existent')
        assert flow is None

    def test_save_and_load_flow(self, service):
        """Flow 저장 및 로드 테스트"""
        # Flow 생성
        flow = Flow(
            id='test_flow',
            name='Test Flow',
            plans={
                'plan1': Plan(
                    id='plan1',
                    name='Test Plan',
                    tasks={
                        'task1': Task(
                            id='task1',
                            name='Test Task',
                            status='todo'
                        )
                    }
                )
            }
        )

        # 저장
        service.save_flow(flow)

        # 로드
        loaded = service.get_flow('test_flow')
        assert loaded is not None
        assert loaded.id == 'test_flow'
        assert loaded.name == 'Test Flow'
        assert 'plan1' in loaded.plans

    def test_cache_performance(self, service):
        """캐시 성능 테스트"""
        import time

        # 큰 Flow 생성 (성능 차이를 명확히 하기 위해)
        plans = {}
        for i in range(10):
            tasks = {}
            for j in range(10):
                tasks[f'task_{i}_{j}'] = Task(
                    id=f'task_{i}_{j}',
                    name=f'Task {i}-{j}',
                    status='todo',
                    context={'data': 'x' * 1000}  # 큰 데이터
                )
            plans[f'plan_{i}'] = Plan(
                id=f'plan_{i}',
                name=f'Plan {i}',
                tasks=tasks
            )

        flow = Flow(id='perf_test', name='Performance Test', plans=plans)
        service.save_flow(flow)

        # 캐시 무효화 (첫 로드가 파일에서 되도록)
        service._cache.invalidate()

        # 첫 번째 로드 (파일에서) - 여러 번 측정
        first_times = []
        for _ in range(3):
            service._cache.invalidate()  # 캐시 클리어
            start = time.perf_counter()
            flow1 = service.get_flow('perf_test')
            first_times.append(time.perf_counter() - start)
        first_load_time = sum(first_times) / len(first_times)

        # 두 번째 로드 (캐시에서) - 여러 번 측정
        second_times = []
        for _ in range(3):
            start = time.perf_counter()
            flow2 = service.get_flow('perf_test')
            second_times.append(time.perf_counter() - start)
        second_load_time = sum(second_times) / len(second_times)

        # 캐시가 최소 50% 더 빨라야 함
        print(f"First load (file): {first_load_time:.6f}s")
        print(f"Second load (cache): {second_load_time:.6f}s")
        print(f"Speed up: {first_load_time / second_load_time:.2f}x")

        assert second_load_time < first_load_time * 0.5
        assert flow1.id == flow2.id

    def test_atomic_save(self, service, temp_dir):
        """원자적 저장 테스트"""
        flow = Flow(id='atomic_test', name='Atomic Test', plans={})

        # 저장 중 임시 파일 확인
        service.save_flow(flow)

        # 최종 파일만 있어야 함
        files = list(Path(temp_dir).glob('*'))
        assert len(files) == 1
        assert files[0].name == 'flows.json'

        # 임시 파일은 없어야 함
        temp_files = list(Path(temp_dir).glob('.flows_*.tmp'))
        assert len(temp_files) == 0

    def test_update_task_status(self, service):
        """Task 상태 업데이트 테스트"""
        # Flow 생성
        flow = Flow(
            id='update_test',
            name='Update Test',
            plans={
                'plan1': Plan(
                    id='plan1',
                    name='Plan 1',
                    tasks={
                        'task1': Task(
                            id='task1',
                            name='Task 1',
                            status='todo'
                        )
                    }
                )
            }
        )

        service.save_flow(flow)

        # Task 상태 업데이트
        service.update_task_status('update_test', 'plan1', 'task1', 'completed')

        # 확인
        updated = service.get_flow('update_test')
        task = updated.plans['plan1'].tasks['task1']
        assert task.status == 'completed'

    def test_concurrent_access(self, service):
        """동시 접근 테스트"""
        import threading

        flow = Flow(id='concurrent', name='Concurrent Test', plans={})
        service.save_flow(flow)

        results = []

        def load_flow():
            loaded = service.get_flow('concurrent')
            results.append(loaded)

        # 10개 스레드에서 동시 접근
        threads = []
        for _ in range(10):
            t = threading.Thread(target=load_flow)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 모두 같은 결과여야 함
        assert len(results) == 10
        assert all(r.id == 'concurrent' for r in results)

    def test_error_handling(self, service):
        """에러 처리 테스트"""
        # 존재하지 않는 Flow 업데이트
        with pytest.raises(ValidationError):
            service.update_task_status('non_existent', 'plan1', 'task1', 'done')

        # 잘못된 JSON 파일
        flows_file = Path(service.base_path) / 'flows.json'
        flows_file.write_text('invalid json')

        with pytest.raises(StorageError):
            service.list_flows()



def test_large_data_handling(self, service):
        """대용량 데이터 처리 테스트"""
        # 큰 Flow 생성 (10 plans x 50 tasks = 500 tasks)
        large_flow = Flow(
            id="large_flow_test",
            name="Large Flow Test"
        )

        # 많은 Plan과 Task 추가
        for p in range(10):
            plan = Plan(
                id=f"plan_{p}",
                name=f"Large Plan {p}",
                flow_id=large_flow.id
            )

            for t in range(50):
                task = Task(
                    id=f"task_{p}_{t}",
                    name=f"Task {p}-{t}",
                    plan_id=plan.id,
                    context={
                        "large_data": "x" * 1000,  # 1KB 데이터
                        "metadata": {"index": t, "plan": p}
                    }
                )
                plan.tasks[task.id] = task

            large_flow.plans[plan.id] = plan

        # 저장 및 로드
        start_save = time.perf_counter()
        service.save_flow(large_flow)
        save_time = time.perf_counter() - start_save

        start_load = time.perf_counter()
        loaded_flow = service.get_flow(large_flow.id)
        load_time = time.perf_counter() - start_load

        # 검증
        assert loaded_flow is not None
        assert len(loaded_flow.plans) == 10
        assert sum(len(p.tasks) for p in loaded_flow.plans.values()) == 500

        # 성능 기준 (1초 이내)
        assert save_time < 1.0, f"Save took too long: {save_time:.2f}s"
        assert load_time < 0.5, f"Load took too long: {load_time:.2f}s"

        print(f"\n  ⚡ 대용량 데이터 처리 성능:")
        print(f"    - 저장 시간: {save_time*1000:.0f}ms (500 tasks)")
        print(f"    - 로드 시간: {load_time*1000:.0f}ms")
# 실행
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
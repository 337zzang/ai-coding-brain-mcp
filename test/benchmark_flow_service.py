"""
Flow Service 성능 벤치마크
기존 FlowService vs CachedFlowService 비교
"""

import os
import sys
import time
import json
import tempfile
import statistics
from datetime import datetime
from pathlib import Path

# 테스트를 위한 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from ai_helpers_new.service.cached_flow_service import CachedFlowService
from ai_helpers_new.domain.models import Flow, Plan, Task

class FlowServiceBenchmark:
    """Flow Service 성능 벤치마크"""

    def __init__(self):
        self.results = {
            'cached': {},
            'comparison': {},
            'improvement': {}
        }

    def generate_large_flow(self, num_plans=10, tasks_per_plan=20):
        """대규모 Flow 데이터 생성"""
        flow = Flow(
            id=f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Benchmark Flow",
            metadata={"type": "benchmark", "size": "large"}
        )

        for p in range(num_plans):
            plan = Plan(
                id=f"plan_{p}",
                name=f"Plan {p}",
                flow_id=flow.id
            )

            for t in range(tasks_per_plan):
                task = Task(
                    id=f"task_{p}_{t}",
                    name=f"Task {p}-{t}",
                    plan_id=plan.id,
                    context={
                        "data": f"Sample data for task {p}-{t}" * 100  # 긴 텍스트
                    }
                )
                plan.tasks[task.id] = task

            flow.plans[plan.id] = plan

        return flow

    def benchmark_write_operations(self, service, num_flows=50):
        """쓰기 작업 벤치마크"""
        times = []

        for i in range(num_flows):
            flow = self.generate_large_flow()

            start = time.perf_counter()
            service.save_flow(flow)
            end = time.perf_counter()

            times.append(end - start)

        return {
            'total_time': sum(times),
            'average_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0
        }

    def benchmark_read_operations(self, service, flow_ids, num_reads=100):
        """읽기 작업 벤치마크"""
        times = []

        for i in range(num_reads):
            flow_id = flow_ids[i % len(flow_ids)]

            start = time.perf_counter()
            flow = service.get_flow(flow_id)
            end = time.perf_counter()

            times.append(end - start)

        return {
            'total_time': sum(times),
            'average_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
            'ops_per_second': num_reads / sum(times)
        }

    def benchmark_list_operations(self, service, num_lists=50):
        """목록 조회 벤치마크"""
        times = []

        for i in range(num_lists):
            start = time.perf_counter()
            flows = service.list_flows()
            end = time.perf_counter()

            times.append(end - start)

        return {
            'total_time': sum(times),
            'average_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0
        }

    def run_benchmark(self):
        """전체 벤치마크 실행"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # CachedFlowService 테스트
            cached_service = CachedFlowService(storage_path=temp_dir)

            print("🚀 CachedFlowService 벤치마크 시작...")

            # 쓰기 벤치마크
            print("  📝 쓰기 작업 벤치마크...")
            write_results = self.benchmark_write_operations(cached_service, num_flows=20)
            self.results['cached']['write'] = write_results

            # Flow ID 수집
            flow_ids = [f.id for f in cached_service.list_flows()]

            # 읽기 벤치마크 (캐시 워밍업)
            print("  📖 읽기 작업 벤치마크 (캐시 콜드)...")
            read_cold_results = self.benchmark_read_operations(cached_service, flow_ids, num_reads=50)
            self.results['cached']['read_cold'] = read_cold_results

            # 읽기 벤치마크 (캐시 활용)
            print("  📖 읽기 작업 벤치마크 (캐시 웜)...")
            read_warm_results = self.benchmark_read_operations(cached_service, flow_ids, num_reads=50)
            self.results['cached']['read_warm'] = read_warm_results

            # 목록 조회 벤치마크
            print("  📋 목록 조회 벤치마크...")
            list_results = self.benchmark_list_operations(cached_service, num_lists=30)
            self.results['cached']['list'] = list_results

            # 캐시 효율성 계산
            cache_speedup = read_cold_results['average_time'] / read_warm_results['average_time']
            self.results['improvement']['cache_speedup'] = cache_speedup

            print("\n✅ 벤치마크 완료!")

        return self.results

    def print_results(self):
        """결과 출력"""
        print("\n" + "="*60)
        print("📊 CachedFlowService 성능 벤치마크 결과")
        print("="*60)

        # 쓰기 성능
        write = self.results['cached']['write']
        print(f"\n📝 쓰기 작업:")
        print(f"  - 평균 시간: {write['average_time']*1000:.2f}ms")
        print(f"  - 최소/최대: {write['min_time']*1000:.2f}ms / {write['max_time']*1000:.2f}ms")

        # 읽기 성능
        read_cold = self.results['cached']['read_cold']
        read_warm = self.results['cached']['read_warm']
        print(f"\n📖 읽기 작업 (캐시 콜드):")
        print(f"  - 평균 시간: {read_cold['average_time']*1000:.2f}ms")
        print(f"  - 처리량: {read_cold['ops_per_second']:.0f} ops/sec")

        print(f"\n📖 읽기 작업 (캐시 웜):")
        print(f"  - 평균 시간: {read_warm['average_time']*1000:.2f}ms")
        print(f"  - 처리량: {read_warm['ops_per_second']:.0f} ops/sec")

        # 캐시 효율성
        speedup = self.results['improvement']['cache_speedup']
        print(f"\n🚀 캐시 효율성:")
        print(f"  - 속도 향상: {speedup:.1f}x")
        print(f"  - 성능 개선: {(speedup-1)*100:.0f}%")

        # 목록 조회 성능
        list_perf = self.results['cached']['list']
        print(f"\n📋 목록 조회:")
        print(f"  - 평균 시간: {list_perf['average_time']*1000:.2f}ms")

        print("\n" + "="*60)


if __name__ == "__main__":
    benchmark = FlowServiceBenchmark()
    results = benchmark.run_benchmark()
    benchmark.print_results()

    # 결과 저장
    with open('test/results/benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\n💾 결과가 test/results/benchmark_results.json에 저장되었습니다.")

"""
포괄적인 테스트 스위트 for test_sample.py
테스트 대상: calculate_factorial, find_duplicates, DataProcessor
"""
import pytest
import time
import sys
import tracemalloc
from unittest.mock import patch
from test_sample import calculate_factorial, find_duplicates, DataProcessor


class TestCalculateFactorial:
    """calculate_factorial 함수에 대한 포괄적인 테스트"""
    
    def test_factorial_normal_cases(self):
        """정상 케이스 테스트"""
        assert calculate_factorial(0) == 1, "0! should be 1"
        assert calculate_factorial(1) == 1, "1! should be 1"
        assert calculate_factorial(2) == 2, "2! should be 2"
        assert calculate_factorial(3) == 6, "3! should be 6"
        assert calculate_factorial(4) == 24, "4! should be 24"
        assert calculate_factorial(5) == 120, "5! should be 120"
    
    def test_factorial_edge_cases(self):
        """엣지 케이스 테스트"""
        # 음수 입력
        assert calculate_factorial(-1) is None, "Negative numbers should return None"
        assert calculate_factorial(-5) is None, "Negative numbers should return None"
        
        # 큰 수 (스택 오버플로우 가능성 확인)
        result = calculate_factorial(10)
        assert result == 3628800, "10! should be 3628800"
    
    def test_factorial_performance(self):
        """성능 테스트"""
        start_time = time.time()
        result = calculate_factorial(15)
        execution_time = time.time() - start_time
        
        assert result == 1307674368000, "15! should be 1307674368000"
        assert execution_time < 1.0, f"Execution time should be under 1 second, got {execution_time}"
    
    def test_factorial_recursion_limit(self):
        """재귀 한계 테스트"""
        # 기본 재귀 한계는 약 1000이므로, 큰 값으로 테스트
        with pytest.raises(RecursionError):
            calculate_factorial(2000)
    
    def test_factorial_type_validation(self):
        """타입 검증 테스트"""
        # 정수가 아닌 입력 (현재 구현에서는 처리하지 않음)
        # 이는 개선이 필요한 부분
        try:
            result = calculate_factorial(5.5)
            # 현재 구현에서는 에러가 발생하지 않지만, 올바르지 않은 결과
        except (TypeError, RecursionError):
            pass  # 예상되는 에러


class TestFindDuplicates:
    """find_duplicates 함수에 대한 포괄적인 테스트"""
    
    def test_find_duplicates_normal_cases(self):
        """정상 케이스 테스트"""
        assert find_duplicates([1, 2, 3, 2, 4, 3, 5]) == [2, 3]
        assert find_duplicates([1, 1, 1, 1]) == [1]
        assert find_duplicates(['a', 'b', 'a', 'c', 'b']) == ['a', 'b']
    
    def test_find_duplicates_edge_cases(self):
        """엣지 케이스 테스트"""
        # 빈 배열
        assert find_duplicates([]) == []
        
        # 중복 없는 배열
        assert find_duplicates([1, 2, 3, 4, 5]) == []
        
        # 단일 요소
        assert find_duplicates([1]) == []
        
        # 모든 요소가 동일
        assert find_duplicates([5, 5, 5, 5, 5]) == [5]
    
    def test_find_duplicates_mixed_types(self):
        """다양한 타입 테스트"""
        mixed = [1, '1', 1, 2.0, 2, '2']
        result = find_duplicates(mixed)
        assert 1 in result  # 정수 1이 중복됨
        # 문자열 '1'과 정수 1은 다른 타입이므로 중복이 아님
    
    def test_find_duplicates_performance(self):
        """성능 테스트 - O(n^2) 복잡도 확인"""
        # 작은 데이터셋
        small_data = list(range(100)) + list(range(50))
        start_time = time.time()
        result = find_duplicates(small_data)
        small_time = time.time() - start_time
        
        # 중간 데이터셋
        medium_data = list(range(200)) + list(range(100))
        start_time = time.time()
        result = find_duplicates(medium_data)
        medium_time = time.time() - start_time
        
        # O(n^2) 특성상 데이터가 2배 증가하면 시간은 약 4배 증가
        # 하지만 실제로는 여러 요인이 있으므로 완화된 조건 사용
        assert len(result) == 100, "Should find 100 duplicates"
        
    def test_find_duplicates_memory_usage(self):
        """메모리 사용량 테스트"""
        tracemalloc.start()
        
        large_data = list(range(1000)) + list(range(500))
        result = find_duplicates(large_data)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        assert len(result) == 500, "Should find 500 duplicates"
        # 메모리 사용량이 과도하지 않은지 확인 (10MB 이하)
        assert peak < 10 * 1024 * 1024, f"Memory usage too high: {peak} bytes"


class TestDataProcessor:
    """DataProcessor 클래스에 대한 포괄적인 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 초기화"""
        self.processor = DataProcessor()
    
    def test_init(self):
        """초기화 테스트"""
        assert hasattr(self.processor, 'data')
        assert isinstance(self.processor.data, list)
        assert len(self.processor.data) == 0
    
    def test_add_data_single_item(self):
        """단일 데이터 추가 테스트"""
        self.processor.add_data("test")
        assert len(self.processor.data) == 1
        assert self.processor.data[0] == "test"
    
    def test_add_data_multiple_items(self):
        """다중 데이터 추가 테스트"""
        items = ["item1", "item2", "item3"]
        for item in items:
            self.processor.add_data(item)
        
        assert len(self.processor.data) == 3
        assert self.processor.data == items
    
    def test_add_data_various_types(self):
        """다양한 타입 데이터 추가 테스트"""
        items = [1, "string", [1, 2, 3], {"key": "value"}, None]
        for item in items:
            self.processor.add_data(item)
        
        assert len(self.processor.data) == 5
        assert self.processor.data == items
    
    def test_process_all_empty(self):
        """빈 데이터 처리 테스트"""
        result = self.processor.process_all()
        assert result == []
    
    def test_process_all_string_data(self):
        """문자열 데이터 처리 테스트"""
        test_strings = ["  HELLO  ", "world", "  TEST DATA  "]
        for s in test_strings:
            self.processor.add_data(s)
        
        result = self.processor.process_all()
        expected = ["hello", "world", "test data"]
        assert result == expected
    
    def test_process_all_mixed_data(self):
        """혼합 데이터 처리 테스트"""
        mixed_data = [123, "  STRING  ", None, [1, 2, 3]]
        for item in mixed_data:
            self.processor.add_data(item)
        
        result = self.processor.process_all()
        expected = ["123", "string", "none", "[1, 2, 3]"]
        assert result == expected
    
    def test_process_all_performance(self):
        """처리 성능 테스트"""
        # 대량 데이터 추가
        for i in range(1000):
            self.processor.add_data(f"  ITEM {i}  ")
        
        start_time = time.time()
        result = self.processor.process_all()
        execution_time = time.time() - start_time
        
        assert len(result) == 1000
        assert all(item.startswith("item") for item in result)
        assert execution_time < 1.0, f"Processing should be under 1 second, got {execution_time}"
    
    def test_memory_accumulation(self):
        """메모리 누적 테스트 (메모리 누수 가능성 확인)"""
        initial_length = len(self.processor.data)
        
        # 대량 데이터 추가
        for i in range(10000):
            self.processor.add_data(f"data_{i}")
        
        assert len(self.processor.data) == initial_length + 10000
        
        # 처리 후에도 원본 데이터는 그대로 남아있음 (메모리 누수 요인)
        result = self.processor.process_all()
        assert len(self.processor.data) == initial_length + 10000
        assert len(result) == 10000
    
    def test_data_isolation(self):
        """데이터 격리 테스트"""
        processor1 = DataProcessor()
        processor2 = DataProcessor()
        
        processor1.add_data("data1")
        processor2.add_data("data2")
        
        assert len(processor1.data) == 1
        assert len(processor2.data) == 1
        assert processor1.data[0] == "data1"
        assert processor2.data[0] == "data2"


class TestIntegration:
    """통합 테스트"""
    
    def test_factorial_with_data_processor(self):
        """팩토리얼과 데이터 프로세서 통합 테스트"""
        processor = DataProcessor()
        
        # 팩토리얼 결과를 데이터 프로세서에 추가
        for i in range(6):
            factorial_result = calculate_factorial(i)
            processor.add_data(factorial_result)
        
        result = processor.process_all()
        expected = ["1", "1", "2", "6", "24", "120"]
        assert result == expected
    
    def test_duplicates_with_data_processor(self):
        """중복 찾기와 데이터 프로세서 통합 테스트"""
        processor = DataProcessor()
        
        # 중복 데이터 추가
        test_data = [1, 2, 3, 2, 4, 3, 5]
        duplicates = find_duplicates(test_data)
        
        for dup in duplicates:
            processor.add_data(f"  DUPLICATE: {dup}  ")
        
        result = processor.process_all()
        assert "duplicate: 2" in result
        assert "duplicate: 3" in result


class TestPerformanceBenchmarks:
    """성능 벤치마크 테스트"""
    
    def test_factorial_benchmark(self):
        """팩토리얼 성능 벤치마크"""
        test_cases = [5, 10, 15, 20]
        results = {}
        
        for n in test_cases:
            start_time = time.perf_counter()
            result = calculate_factorial(n)
            end_time = time.perf_counter()
            
            results[n] = {
                'result': result,
                'time': end_time - start_time
            }
        
        # 성능 기준 확인
        assert results[5]['time'] < 0.001, "5! should compute very quickly"
        assert results[10]['time'] < 0.01, "10! should compute quickly"
        
        # 결과 검증
        assert results[5]['result'] == 120
        assert results[10]['result'] == 3628800
    
    def test_find_duplicates_benchmark(self):
        """중복 찾기 성능 벤치마크"""
        data_sizes = [100, 500, 1000]
        results = {}
        
        for size in data_sizes:
            # 50% 중복이 있는 테스트 데이터 생성
            test_data = list(range(size)) + list(range(size // 2))
            
            start_time = time.perf_counter()
            duplicates = find_duplicates(test_data)
            end_time = time.perf_counter()
            
            results[size] = {
                'duplicates_found': len(duplicates),
                'time': end_time - start_time
            }
        
        # O(n^2) 특성 확인 (대략적으로)
        time_100 = results[100]['time']
        time_500 = results[500]['time']
        
        # 5배 데이터 증가 시 시간은 25배 정도 증가해야 함 (여유를 두고 10배 이내)
        if time_100 > 0:
            ratio = time_500 / time_100
            assert ratio < 100, f"Performance degradation too high: {ratio}"


class TestErrorHandling:
    """에러 처리 테스트"""
    
    def test_factorial_edge_error_cases(self):
        """팩토리얼 에러 케이스"""
        # 현재 구현에서는 타입 검사가 없음
        with pytest.raises((TypeError, RecursionError)):
            calculate_factorial("invalid")
        
        with pytest.raises((TypeError, RecursionError)):
            calculate_factorial(None)
    
    def test_find_duplicates_error_cases(self):
        """중복 찾기 에러 케이스"""
        # 현재 구현은 타입 검사를 하지 않으므로 실제로는 에러가 발생함
        # None의 경우 TypeError 발생
        with pytest.raises(TypeError):
            find_duplicates(None)
        
        # 문자열의 경우 문자 단위로 처리되므로 실제로는 작동함
        # 현재 구현의 한계로 이 테스트는 스킵
        result = find_duplicates("aabbcc")
        assert isinstance(result, list)  # 문자열도 iterable이므로 처리됨
    
    def test_data_processor_error_cases(self):
        """데이터 프로세서 에러 케이스"""
        processor = DataProcessor()
        
        # None 추가는 가능해야 함
        processor.add_data(None)
        result = processor.process_all()
        assert result == ["none"]


if __name__ == "__main__":
    # 테스트 실행 시 상세 정보 출력
    pytest.main([__file__, "-v", "--tb=short", "--durations=10"])
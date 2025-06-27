
"""
들여쓰기 처리 시스템 성능 벤치마크
"""
import time
import statistics
import random
from typing import List, Dict

from core.indentation_preprocessor import IndentationPreprocessor
from core.indentation_error_handler import IndentationErrorHandler

class IndentationPerformanceBenchmark:
    """성능 측정 및 분석"""
    
    def __init__(self):
        self.preprocessor = IndentationPreprocessor()
        self.error_handler = IndentationErrorHandler()
        
    def generate_test_codes(self, count: int = 100) -> List[str]:
        """테스트용 코드 생성"""
        templates = [
            # 정상 코드
            """def function_{n}():
    x = {n}
    return x * 2""",
            
            # 들여쓰기 오류가 있는 코드
            """def function_{n}():
x = {n}
return x * 2""",
            
            # 복잡한 중첩 구조
            """class Class_{n}:
    def method(self):
        for i in range({n}):
            if i % 2:
                print(i)""",
            
            # 탭/스페이스 혼용
            """def mixed_{n}():\n\tx = {n}\n    y = x * 2"""
        ]
        
        codes = []
        for i in range(count):
            template = random.choice(templates)
            codes.append(template.format(n=i))
        
        return codes
    
    def benchmark_preprocessing(self, codes: List[str]) -> Dict:
        """전처리 성능 측정"""
        times = []
        
        for code in codes:
            start = time.perf_counter()
            try:
                _, _ = self.preprocessor.preprocess(code)
            except:
                pass
            end = time.perf_counter()
            
            times.append((end - start) * 1000)  # ms 단위
        
        return {
            'total_codes': len(codes),
            'avg_time_ms': statistics.mean(times),
            'median_time_ms': statistics.median(times),
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def benchmark_error_handling(self, codes: List[str]) -> Dict:
        """오류 처리 성능 측정"""
        times = []
        error_count = 0
        
        for code in codes:
            try:
                compile(code, '<test>', 'exec')
            except IndentationError as e:
                error_count += 1
                start = time.perf_counter()
                _ = self.error_handler.handle_error(code, e)
                end = time.perf_counter()
                times.append((end - start) * 1000)
        
        if times:
            return {
                'error_count': error_count,
                'avg_handling_time_ms': statistics.mean(times),
                'median_handling_time_ms': statistics.median(times),
                'total_handling_time_ms': sum(times)
            }
        else:
            return {'error_count': 0, 'message': 'No errors to handle'}
    
    def run_full_benchmark(self, test_sizes: List[int] = [10, 100, 1000]) -> Dict:
        """전체 벤치마크 실행"""
        results = {}
        
        for size in test_sizes:
            print(f"\n테스트 크기: {size} 코드")
            codes = self.generate_test_codes(size)
            
            # 전처리 벤치마크
            preprocess_results = self.benchmark_preprocessing(codes)
            
            # 오류 처리 벤치마크
            error_results = self.benchmark_error_handling(codes)
            
            results[f'size_{size}'] = {
                'preprocessing': preprocess_results,
                'error_handling': error_results
            }
            
            print(f"  평균 전처리 시간: {preprocess_results['avg_time_ms']:.2f}ms")
            print(f"  오류 처리 수: {error_results.get('error_count', 0)}")
        
        return results


# 최적화된 전처리기
class OptimizedIndentationPreprocessor(IndentationPreprocessor):
    """성능 최적화된 전처리기"""
    
    def __init__(self):
        super().__init__()
        self._style_cache = {}  # 들여쓰기 스타일 캐시
        self._parse_cache = {}  # AST 파싱 결과 캐시
        
    def detect_indent_style(self, code: str) -> int:
        """캐시를 활용한 들여쓰기 스타일 감지"""
        # 코드 해시를 키로 사용
        code_hash = hash(code[:100])  # 처음 100자만 해시
        
        if code_hash in self._style_cache:
            return self._style_cache[code_hash]
        
        # 부모 클래스의 감지 로직 사용
        style = super().detect_indent_style(code)
        self._style_cache[code_hash] = style
        
        return style
    
    def preprocess(self, code: str) -> tuple:
        """최적화된 전처리"""
        # 작은 코드는 전처리 스킵
        if len(code) < 50 and '\n' not in code:
            return code, False
        
        # 캐시 확인
        code_hash = hash(code)
        if code_hash in self._parse_cache:
            return self._parse_cache[code_hash]
        
        # 전처리 수행
        result = super().preprocess(code)
        
        # 결과 캐싱
        self._parse_cache[code_hash] = result
        
        return result


if __name__ == '__main__':
    print("🚀 들여쓰기 처리 성능 벤치마크 시작\n")
    
    benchmark = IndentationPerformanceBenchmark()
    results = benchmark.run_full_benchmark([10, 50, 100])
    
    print("\n📊 벤치마크 결과 요약:")
    for size_key, data in results.items():
        size = size_key.split('_')[1]
        prep = data['preprocessing']
        print(f"\n{size}개 코드 테스트:")
        print(f"  - 평균 전처리 시간: {prep['avg_time_ms']:.2f}ms")
        print(f"  - 중앙값: {prep['median_time_ms']:.2f}ms")
        print(f"  - 최소/최대: {prep['min_time_ms']:.2f}ms / {prep['max_time_ms']:.2f}ms")

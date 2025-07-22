# Flow 시스템 개선 테스트 계획

## 1. 단위 테스트

### 1.1 FlowRegistry 테스트
- test_create_flow()
- test_get_flow_with_cache()
- test_delete_flow()
- test_find_flows_by_name()
- test_concurrent_access()

### 1.2 마이그레이션 테스트
- test_migrate_empty_flows()
- test_migrate_list_to_dict()
- test_migrate_duplicate_names()
- test_migrate_preserve_data()

## 2. 성능 벤치마크

```python
def benchmark_flow_operations():
    # 데이터 준비
    num_flows = [10, 50, 100, 500, 1000]

    for n in num_flows:
        # 리스트 구조 테스트
        list_time = measure_list_operations(n)

        # 딕셔너리 구조 테스트
        dict_time = measure_dict_operations(n)

        # 결과 비교
        print(f"Flows: {n}")
        print(f"  List: {list_time:.3f}ms")
        print(f"  Dict: {dict_time:.3f}ms")
        print(f"  Speedup: {list_time/dict_time:.1f}x")
```

## 3. 통합 테스트

- [ ] 실제 flows.json 파일로 테스트
- [ ] 중복 이름 처리 확인
- [ ] 대용량 데이터 테스트 (1000+ flows)
- [ ] 메모리 사용량 측정

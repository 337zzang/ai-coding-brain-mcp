
# Flow 시스템 개선안 요약

## 1. 데이터 구조 개선
### 현재
```python
{
    "flows": [
        {"id": "flow_1", "name": "project1", ...},
        {"id": "flow_2", "name": "project2", ...}
    ],
    "current_flow_id": "flow_1"
}
```

### 개선안
```python
{
    "flows": {
        "flow_1": {"name": "project1", ...},
        "flow_2": {"name": "project2", ...}
    },
    "current_flow_id": "flow_1",
    "flow_index": {  # 이름으로 빠른 검색을 위한 인덱스
        "project1": ["flow_1"],
        "project2": ["flow_2"]
    }
}
```

## 2. 새로운 메서드
- `get_flow(flow_id)`: O(1) 직접 접근
- `find_flows_by_name(name)`: 이름으로 검색
- `load_all_flows()`: 전체 상태 로드
- `migrate_legacy_structure()`: 자동 마이그레이션

## 3. 예상 성능 개선
- Flow 검색: O(n) → O(1)
- 메모리 사용: 약간 증가 (인덱스 추가)
- 코드 복잡도: 감소

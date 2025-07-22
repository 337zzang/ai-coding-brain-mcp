# Flow 시스템 현재 구조 분석

## 1. 현재 문제점

### 1.1 데이터 구조 문제
- **flows가 리스트로 저장됨**: O(n) 검색 시간 복잡도
- **중복 Flow 이름 허용**: 동일 이름의 Flow가 여러 개 존재 가능
- **ID 검색 비효율**: 매번 전체 리스트를 순회해야 함

### 1.2 코드에서 발견된 패턴
```python
# 초기화
self.flows = []

# Flow 추가
self.flows.append(new_flow)

# Flow 검색 (O(n))
for flow in self.flows:
    if flow['id'] == flow_id:
        ...

# Flow 삭제 (리스트 컴프리헨션)
self.flows = [f for f in self.flows if f['id'] != flow_id]
```

### 1.3 _load_flows 메서드 분석
def _load_flows(self):
        """
        flows.json에서 flow 데이터 로드

        flows.json 구조:
        {
            "flows": [...],
            "current_flow_id": "...",
            "last_saved": "...",
            "version": "2.0"
        }
        """
        flows_path = os.path.join(self.data_dir,...

### 1.4 _save_flows 메서드 분석
def _save_flows(self, force: bool = False) -> bool:
        """
        Flow 데이터 저장 (개선된 버전)

        Args:
            force: 강제 저장 여부

        Returns:
            bool: 저장 성공 여부
        """
        flows_path = os.path.join(self.data_dir, 'flows.json')

        try:
            # 저장할 데이터 준비
     ...

## 2. 개선 필요 사항

1. **데이터 구조 변경**: 리스트 → 딕셔너리
   - Key: flow_id
   - Value: flow 객체
   - O(1) 검색 시간

2. **통합 읽기 함수**: 전체 Flow 데이터를 한 번에 읽는 함수
   - 현재: flows, current_flow_id 등을 개별적으로 관리
   - 개선: 통합된 상태 관리

3. **마이그레이션**: 기존 리스트 구조를 딕셔너리로 변환
   - 하위 호환성 유지
   - 자동 마이그레이션

## 3. 영향 받는 메서드
- _load_flows()
- _save_flows()
- create_flow()
- delete_flow()
- switch_flow()
- _list_flows()
- _handle_flow_command()

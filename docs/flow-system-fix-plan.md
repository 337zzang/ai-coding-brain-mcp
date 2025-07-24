
## 📋 Flow 시스템 수정 계획

### 🔍 문제 분석 완료
1. **근본 원인**: LegacyFlowAdapter.switch_project()에서 Flow가 없으면 자동 생성
2. **영향**: 모든 /flow [name] 명령이 의도치 않게 새 Flow를 생성

### 🛠️ 수정 방안

#### 1. switch_project 메서드 수정
```python
# 현재 코드 (문제 있음)
if not target_flow:
    # 없으면 새로 생성
    target_flow = self._manager.create_flow(name=name)

# 수정된 코드
if not target_flow:
    # Flow가 없으면 에러 반환
    return err(f"Flow '{name}'을 찾을 수 없습니다. '/flow create {name}'으로 먼저 생성하세요.")
```

#### 2. flow_subcommands에 'list' 추가
```python
self.flow_subcommands = {
    'create': self.handle_flow_create,
    'list': self.handle_flow_list,  # 추가
    'status': self.handle_flow_status,
    'delete': self.handle_flow_delete,
    'archive': self.handle_flow_archive,
    'restore': self.handle_flow_restore,
}
```

#### 3. handle_flow_list 메서드 추가
- Flow 목록을 표시하는 전용 핸들러

### 📋 작업 단계
1. 백업 생성
2. switch_project 메서드 수정
3. flow_subcommands에 'list' 추가
4. handle_flow_list 메서드 구현
5. 테스트 및 검증

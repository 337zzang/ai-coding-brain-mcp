
## execute_code 고급 활용 - AI 자율성 확장

### 핵심 원칙
1. **세션 유지 활용**: globals()로 상태 확인, 복잡한 작업 분할
2. **stdout 통신**: [NEXT_ACTION]으로 다음 작업 지시
3. **실행 추적**: 고유 ID로 모든 실행 관리
4. **병렬 처리**: asyncio로 성능 최적화
5. **동적 코드**: AST와 exec()로 자가 개선

### AI 자율성 레벨
- Level 1: 기본 실행
- Level 2: 상태 인식 (세션 변수)
- Level 3: 능동적 의사결정 (stdout 지시)
- Level 4: 자가 개선 (AST 분석)
- Level 5: 완전 자율 (통합 시스템)

### 실전 패턴
```python
# 1. 장기 작업 관리
if 'project' not in globals():
    project = initialize_project()
else:
    project = continue_work(project)

# 2. AI 자율 의사결정
if should_proceed():
    print("[NEXT_ACTION]")
    print(json.dumps({'action': 'optimize'}))

# 3. 실행 추적
exec_id = generate_execution_id()
track_execution(exec_id, results)
```

이제 AI는 단순한 도구가 아닌, 자율적 파트너입니다.

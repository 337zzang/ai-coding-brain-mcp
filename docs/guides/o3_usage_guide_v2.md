
## 🤖 O3 활용 가이드 (v2.0 개선판)

### 📊 O3 코드 제공 가이드라인 (신규)

#### 코드 크기별 권장사항
| 분석 유형 | 코드 크기 | 용도 | 예상 시간 |
|-----------|-----------|------|-----------|
| 간단 분석 | 1,000-5,000자 | 함수 단위 분석 | 5-10초 |
| 일반 분석 | 5,000-15,000자 | 모듈 분석 | 10-20초 |
| 상세 분석 | 15,000-50,000자 | 전체 파일 분석 | 20-60초 |
| 대규모 | 50,000자 이상 | 청크 분할 필요 | 분할 처리 |

#### 실전 코드 제공 패턴
```python
# ✅ 올바른 방법: 코드와 함께 질문
file_content = h.file.read("module.py")['data']
if len(file_content) < 50000:  # 토큰 제한 체크
    question = f'''
    다음 코드를 분석해주세요:

    === 코드 시작 ({len(file_content)}자) ===
    {file_content}
    === 코드 끝 ===

    분석 요청:
    1. 성능 병목 지점
    2. 메모리 최적화 방안
    3. 코드 품질 개선점
    '''
    task_id = h.ask_o3_async(question)['data']

# ❌ 잘못된 방법: 코드 없이 질문만
h.ask_o3_async("search.py의 버그를 찾아줘")  # O3는 파일 접근 불가!
```

### 🎯 O3 vs Claude 사용 기준 (신규)

#### O3 사용이 적합한 경우
- 🔍 **심층 분석**: 전체 아키텍처 검토, 리팩토링 제안
- 🚀 **성능 최적화**: 알고리즘 개선, 병목 지점 분석
- 🔒 **보안 검토**: 취약점 분석, 코드 감사
- 🧮 **복잡한 로직**: 수학적 검증, 알고리즘 정확성
- 📚 **대규모 코드**: 1000줄 이상 코드베이스 분석

#### Claude가 더 적합한 경우
- ✏️ **코드 작성**: 새 기능 구현, 버그 수정
- 🔧 **즉시 수정**: 빠른 응답이 필요한 작업
- 💬 **대화형 작업**: 단계별 디버깅, 설명
- 📁 **파일 작업**: 파일 읽기/쓰기, 실행
- 🔄 **반복 작업**: 여러 파일 처리

### 📝 O3 결과 처리 패턴 (신규)

```python
# 1. 결과 구조 확인 및 파싱
result = h.get_o3_result(task_id)

if result['ok']:
    data = result.get('data', {})

    # O3 응답 형식 처리
    if isinstance(data, dict) and 'answer' in data:
        answer = data['answer']
        usage = data.get('usage', {})

        # 토큰 사용량 확인
        print(f"토큰 사용: {usage.get('total_tokens', 'N/A')}")

        # 결과 저장
        h.file.write(f"o3_analysis_{task_id}.md", answer)
    else:
        # 아직 처리 중
        print(f"Status: {data.get('status', 'unknown')}")

# 2. 에러 처리
else:
    error = result.get('error', 'Unknown error')
    if 'running' in error:
        print("⏳ O3가 아직 분석 중...")
    else:
        print(f"❌ 오류: {error}")
```

### 🔄 Claude + O3 협업 워크플로우 (개선)

```python
# Step 1: Claude가 문제 정의 및 코드 준비
code = h.file.read("problematic_module.py")['data']
issues = h.search.code("TODO|FIXME|BUG", ".")

# Step 2: O3에게 심층 분석 요청 (비동기)
o3_task = h.ask_o3_async(f"코드: {code}\n\n심층 분석 요청...")['data']

# Step 3: O3 분석 중 Claude가 다른 작업 수행
h.file.write("issues.md", str(issues))
test_results = h.execute_code("python -m pytest")

# Step 4: O3 결과 수신 및 구현
o3_result = h.get_o3_result(o3_task)
if o3_result['ok']:
    # Claude가 O3 제안을 코드로 구현
    improvements = parse_o3_suggestions(o3_result['data']['answer'])
    implement_improvements(improvements)

# Step 5: O3로 구현 검증
validation_task = h.ask_o3_async(f"구현 검증: {new_code}")
```

### ⏱️ 성능 고려사항 (신규)

| 작업 유형 | O3 응답 시간 | Claude 응답 시간 |
|-----------|-------------|-----------------|
| 간단 분석 | 5-10초 | 즉시 |
| 복잡 분석 | 20-60초 | 즉시 |
| 대규모 분석 | 1-5분 | N/A |

### 🐛 일반적인 문제 해결

| 문제 | 원인 | 해결 방법 |
|------|------|-----------|
| O3ContextBuilder import 실패 | 직접 import 불가 | `h.llm.create_context()` 사용 |
| 결과가 None | 아직 처리 중 | `h.show_o3_progress()` 확인 |
| 토큰 초과 | 코드가 너무 김 | 40,000자 단위로 분할 |
| 느린 응답 | 복잡한 분석 | 비동기 처리 + 다른 작업 병행 |

### 💡 Pro Tips

1. **코드 100% 제공**: O3는 파일 시스템 접근 불가, 반드시 코드 포함
2. **비동기 우선**: `ask_o3_async` 사용하여 대기 시간 활용
3. **청크 전략**: 50,000자 이상은 의미 단위로 분할
4. **결과 저장**: O3 분석은 비싸므로 항상 파일로 저장
5. **용도 구분**: 분석은 O3, 구현은 Claude

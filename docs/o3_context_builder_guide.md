# O3ContextBuilder 사용 가이드

## 🎯 개요
O3ContextBuilder는 o3 모델에게 질문할 때 풍부한 컨텍스트를 제공하면서도 실용적인 답변을 받을 수 있도록 돕는 도구입니다.

## 📦 설치
이미 `ai_helpers_new`에 통합되어 있습니다.

```python
import ai_helpers_new as h
```

## 🚀 기본 사용법

### 1. 에러 해결
```python
# 빠른 방법
builder = h.quick_o3_context(
    error_msg="TypeError: 'NoneType' object has no attribute 'id'",
    file_path="auth.py",
    line_num=25
)
question = builder.build_question("이 에러를 해결하는 실용적인 방법은?")
task_id = h.ask_o3_async(question)['data']
```

### 2. 코드 리뷰
```python
builder = h.O3ContextBuilder()
builder.add_file("new_feature.py", "새 기능") \
       .add_file("tests/test_feature.py", "테스트") \
       .analyze_structure("new_feature.py") \
       .add_git_history(5)

question = builder.build_question("""
이 코드의 실용적인 개선점을 제안해주세요:
1. 즉시 수정 가능한 버그
2. 간단한 리팩토링 (10분 이내)
""")
```

### 3. 성능 최적화
```python
builder = h.O3ContextBuilder()
builder.add_function("processor.py", "process_large_file") \
       .search_and_add("process_large_file", ".", "사용처")

question = builder.build_question("메모리 사용량을 줄이는 실용적 방법은?")
```

## 📋 주요 메서드

- `add_file(path, label)` - 파일 전체 추가
- `add_function(path, name)` - 특정 함수만 추가
- `add_error_context(msg, file, line)` - 에러 정보 추가
- `add_git_history(limit)` - Git 커밋 히스토리
- `search_and_add(pattern, path)` - 코드 검색 결과
- `analyze_structure(path)` - 파일 구조 분석
- `build_question(q, guidelines)` - 최종 질문 생성

## 💡 팁

1. **체이닝 활용**: 모든 메서드는 self를 반환하므로 체이닝 가능
2. **커스텀 가이드라인**: 팀의 코딩 규칙을 guidelines로 전달
3. **점진적 구축**: REPL에서 단계별로 정보 추가하며 확인

## 🎯 실용적 답변을 위한 가이드라인
기본적으로 다음 가이드라인이 포함됩니다:
- 현재 코드 수준에 맞는 해결책
- Quick Fix 우선
- 기존 패턴 유지
- 과도한 리팩토링 지양

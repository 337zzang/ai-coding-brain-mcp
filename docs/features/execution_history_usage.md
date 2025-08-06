
## 1. 디버깅 시나리오

### 오류 발생 시 컨텍스트 파악
```python
# 사용자가 오류 발생
>>> df.groupby('category').mean()
❌ KeyError: 'category'

# 히스토리 확인으로 이전 실행 추적
>>> show_recent_executions(5)
[3] df = pd.read_csv('data.csv')  ✓
[4] df.columns  ✓
[5] df.groupby('category').mean()  ✗

# 아하! 컬럼명이 'Category'였구나 (대문자)
```

## 2. 작업 재현 시나리오

### 성공한 작업 순서 재현
```python
>>> export_execution_history('successful_analysis.py')
# 히스토리에서 성공한 코드만 추출하여 스크립트 생성
# 1. import pandas as pd
# 2. df = pd.read_csv('sales.csv')
# 3. df['profit'] = df['revenue'] - df['cost']
# 4. summary = df.groupby('region').agg({...})
```

## 3. 패턴 분석 시나리오

### 자주 사용하는 패턴 발견
```python
>>> analyze_execution_patterns()
가장 많이 사용된 import:
- pandas (45회)
- numpy (23회)
- matplotlib (18회)

자주 발생한 오류:
- NameError (12회) → 변수 오타
- KeyError (8회) → 컬럼명 실수
```

## 4. 협업 시나리오

### 작업 내용 공유
```python
>>> share_session_history('2025-08-05_analysis')
# 오늘 세션의 실행 히스토리를 팀원과 공유
# 성공/실패 포함하여 시행착오 과정도 공유
```

## 5. 학습 도구 시나리오

### 실수에서 배우기
```python
>>> show_failed_executions()
[12] df.sort_values('date')  ✗  # inplace=True 빠뜨림
[23] plt.plot(x, y)  ✗  # plt.show() 안 함
[34] model.fit(X_train)  ✗  # y_train 빠뜨림

# 자주 하는 실수 패턴을 인식하고 개선
```



## 🛠️ 실행 히스토리 헬퍼 함수 (구현 예시)

```python
def show_recent_executions(n=10):
    '''최근 n개 실행 표시'''
    for item in EXECUTION_HISTORY[-n:]:
        status = "✓" if item['success'] else "✗"
        print(f"[{item['execution_count']}] {item['code'][:50]}...  {status}")

def get_failed_executions():
    '''실패한 실행만 필터링'''
    return [e for e in EXECUTION_HISTORY if not e['success']]

def export_successful_code(filename):
    '''성공한 코드만 추출하여 파일로 저장'''
    successful = [e for e in EXECUTION_HISTORY if e['success']]
    with open(filename, 'w') as f:
        for e in successful:
            f.write(f"# [{e['timestamp']}]\n")
            f.write(f"{e['code']}\n\n")

def analyze_error_patterns():
    '''오류 패턴 분석'''
    errors = {}
    for e in get_failed_executions():
        # stderr에서 오류 타입 추출
        error_type = extract_error_type(e.get('stderr', ''))
        errors[error_type] = errors.get(error_type, 0) + 1
    return errors

def get_execution_stats():
    '''실행 통계'''
    total = len(EXECUTION_HISTORY)
    successful = sum(1 for e in EXECUTION_HISTORY if e['success'])
    return {
        'total': total,
        'successful': successful,
        'failed': total - successful,
        'success_rate': successful / total if total > 0 else 0
    }
```

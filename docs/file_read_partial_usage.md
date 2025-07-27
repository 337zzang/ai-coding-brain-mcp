
=== h.read() 함수 사용 가이드 ===

## 기본 사용법 (기존과 동일)
```python
# 전체 파일 읽기
content = h.read('file.txt')
```

## 새로운 부분 읽기 기능

### 1. 특정 위치부터 읽기
```python
# 10번째 줄부터 20줄 읽기
partial = h.read('file.txt', offset=10, length=20)

# 50번째 줄부터 끝까지 읽기
from_middle = h.read('file.txt', offset=50)
```

### 2. 파일 끝에서부터 읽기 (tail 기능)
```python
# 마지막 20줄 읽기
last_lines = h.read('file.txt', offset=-20)

# 마지막 100줄 중 처음 10줄만
tail_partial = h.read('file.txt', offset=-100, length=10)
```

### 3. 대용량 파일 처리
```python
# 로그 파일의 마지막 50줄만 확인
logs = h.read('large.log', offset=-50)

# 중간 부분만 샘플링
sample = h.read('data.csv', offset=1000, length=100)
```

## 반환값
```python
{
    'ok': True,
    'data': '파일 내용',
    'path': '절대 경로',
    'lines': 읽은 라인 수,
    'total_lines': 전체 라인 수 (부분 읽기 시),
    'size': 파일 크기,
    'encoding': '인코딩',
    'offset': 사용된 offset,
    'length': 사용된 length
}
```

## 성능 팁
- 대용량 파일에서 특정 부분만 필요한 경우 offset/length 사용
- 로그 모니터링 등에는 음수 offset 활용
- 전체 파일이 필요한 경우는 기존처럼 파라미터 없이 사용

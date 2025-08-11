# 프리퍼런스 업데이트 제안 (2025-08-11)

## 배경
- list_directory() 반환 구조가 명확하지 않아 'entries' 키로 잘못 접근하는 실수 발생
- 실제로는 'items' 키를 사용해야 함

## 프리퍼런스 수정 위치
"🔧 헬퍼 함수 상세 참조 (Facade 완성)" 섹션의 "📁 h.file.*" 부분에 추가

## 추가할 내용

### list_directory() 정확한 반환 구조
```python
dirs = h.file.list_directory(".")
# 반환 구조:
# {
#     'ok': True,
#     'data': {
#         'path': str,
#         'items': [...],  # ⚠️ 'entries' 아님!
#         'count': int
#     }
# }

# ✅ 올바른 사용
if dirs['ok']:
    items = dirs['data']['items']

# ❌ 잘못된 사용
dirs['data']['entries']  # KeyError!
```

## 체크리스트 추가
프리퍼런스의 "일반적인 오류 해결" 테이블에 추가:

| 오류 | 증상 | 해결 |
|------|------|------|
| **list_directory 키 오류** | KeyError: 'entries' | 'items' 키 사용 |

## 실수 방지 팁
1. 반환값 구조 확인: print(list(result['data'].keys()))
2. 자동완성 활용보다 문서 참조
3. 테스트 코드 먼저 작성

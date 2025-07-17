
## 🎯 권장 헬퍼 함수 (핵심 20개)

### 파일 작업 (6개)
1. **helpers.read_file(path)** - 파일 읽기
2. **helpers.write_file(path, content)** - 파일 쓰기
3. **helpers.create_file(path, content)** - 파일 생성
4. **helpers.append_to_file(path, content)** - 파일에 추가
5. **helpers.file_exists(path)** - 파일 존재 확인
6. **helpers.list_directory(path)** - 디렉토리 목록

### JSON 작업 (2개)
7. **helpers.read_json(path)** - JSON 파일 읽기
8. **helpers.write_json(path, data)** - JSON 파일 쓰기

### 검색 (2개)
9. **helpers.search_files(path, pattern)** - 파일명 검색
10. **helpers.search_code(path, pattern, file_pattern)** - 코드 내용 검색

### Git 작업 (4개)
11. **helpers.git_status()** - Git 상태 확인
12. **helpers.git_add(path)** - 스테이징
13. **helpers.git_commit(message)** - 커밋
14. **helpers.git_push()** - 푸시

### 디렉토리 작업 (2개)
15. **helpers.scan_directory_dict(path)** - 디렉토리 구조 스캔
16. **helpers.create_project_structure(path, structure)** - 프로젝트 구조 생성

### 전역 함수 - 코드 분석 (4개)
17. **parse_file(path)** - 코드 구조 분석
18. **safe_find_function(path, name)** - 함수 찾기
19. **safe_find_class(path, name)** - 클래스 찾기
20. **safe_git_status()** - 안전한 Git 상태

## ⚠️ 사용하지 말아야 할 함수들
- **replace_block** - 작동하지 않음
- **safe_replace_block** - 동일한 문제
- **insert_block** - 신뢰할 수 없음
- **parse_with_snippets** - parse_file 사용 권장

## 💡 코드 수정 권장 방법
```python
# 방법 1: 전체 파일 수정
content = helpers.read_file("file.py")
new_content = content.replace("old", "new")
helpers.write_file("file.py", new_content)

# 방법 2: Desktop Commander 사용
# DC: edit_block 사용 (더 안정적)
```

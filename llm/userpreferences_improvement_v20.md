# 유저 프리퍼런스 v20.0 개선안

## 1. 누락된 기능 (문서에서 제거 필요)

### Quick 함수들
```python
# 이 함수들은 실제로 구현되지 않음:
qs(pattern)           # ❌ 미구현
qfind(path, pattern)  # ❌ 미구현  
qc(pattern)           # ❌ 미구현
qv(file, func)        # ❌ 미구현
qproj()               # ❌ 미구현
```

### 코드 수정 권장 함수
```python
# 이 함수들도 미구현:
replace_function(filepath, func_name, new_code)  # ❌
replace_method(filepath, class_name, method_name, new_code)  # ❌
extract_code_elements(filepath)  # ❌
replace_block()  # ❌ (h.replace는 존재)
```

### safe_* 함수들
```python
# 미구현:
safe_search_code()  # ❌
safe_read_file()    # ❌
safe_parse_file()   # ❌
```

### HelperResult 패턴
- SearchResult, FileResult, ParseResult 클래스 미구현
- 현재는 단순 dict 패턴만 사용 중

## 2. /flow 명령 동작 개선

### 현재 동작 (과도함)
1. 워크플로우 상태 확인 ✓
2. 현재 프로젝트 확인 ✓
3. o3 백그라운드 작업 확인 ✓
4. 최근 변경 파일 확인 ✓ (불필요)
5. o3 분석 결과 상세 검토 ✓ (불필요)

### 개선된 동작 (간단하게)
```python
# /flow 처리 시:
1. wf('/status') 실행
2. 현재 프로젝트 표시
3. 진행 중인 o3 작업 개수만 표시
# 끝. 추가 분석은 사용자 요청 시에만
```

## 3. 워크플로우 명령어 수정

### 실제 사용 가능한 명령어
```
/task add [이름] #태그    (O) - 작업 추가
/task list               (O) - 목록 보기
/start [id]              (O) - 작업 시작
/complete [id] [요약]     (O) - 작업 완료

# 문서에 있지만 실제와 다른 것:
/task [내용]    (X) → /task add [내용]
/next          (X) → /start [id]
/done          (X) → /complete [id]
/focus [내용]   (?) - 확인 필요
/clear         (?) - 확인 필요
```

## 4. 실제 사용 가능한 AI Helpers 함수

### 파일 작업
- h.read(), h.write(), h.append()
- h.read_json(), h.write_json()
- h.exists(), h.info()

### 코드 분석/수정
- h.parse(), h.view()
- h.replace() (단순 텍스트 교체만)
- h.insert(), h.functions(), h.classes()

### 검색
- h.search_files(), h.search_code()
- h.find_function(), h.find_class()
- h.grep(), h.find_in_file()

### o3 백그라운드
- h.ask_o3_async(), h.check_o3_status()
- h.get_o3_result(), h.show_o3_progress()
- h.list_o3_tasks(), h.clear_completed_tasks()

### Git
- h.git_status(), h.git_add(), h.git_commit()
- h.git_push(), h.git_pull(), h.git_branch()
- h.git_log(), h.git_diff()

### 프로젝트
- h.get_current_project()
- h.detect_project_type()
- h.scan_directory(), h.scan_directory_dict()
- h.create_project_structure()

## 5. 권장사항

1. **유저 프리퍼런스 문서 업데이트**
   - 미구현 함수 제거
   - 실제 동작과 일치하도록 수정

2. **/flow 명령 처리 간소화**
   - 간단한 상태만 표시
   - 상세 분석은 별도 명령으로

3. **워크플로우 명령어 통일**
   - 실제 구현과 문서 일치시키기

4. **누락 기능 구현 검토**
   - Quick 함수들이 정말 필요한지?
   - safe_* 함수의 필요성?

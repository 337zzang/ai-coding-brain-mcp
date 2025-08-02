# AI Helpers API 일관성 개선 가이드

## 📋 개요
AI Helpers API의 일관성과 안정성을 개선하기 위한 수정 사항 문서입니다.

## 🎯 수정 사항

### 1. get_current_project (project.py)
- **상태**: 수정 불필요 (이미 정상 작동)
- **반환값**: `{'ok': True, 'data': {'name', 'path', 'type', 'has_git'}}`

### 2. search_files (search.py)
- **추가**: `max_depth` 파라미터 지원
- **동작**: 
  - `max_depth=1`: 현재 디렉토리만
  - `max_depth=2`: 한 단계 하위까지
  - `recursive=False`: 자동으로 `max_depth=1` 설정
- **예시**:
  ```python
  # 2단계 깊이까지만 검색
  h.search_files("*.py", path, max_depth=2)
  ```

### 3. get_file_info (file.py)
- **추가 필드**:
  - `lineCount`: 파일의 총 라인 수
  - `lastLine`: 마지막 라인 번호 (0-based)
  - `appendPosition`: 추가 시 위치 (라인 수)
  - `type`: 'file' 또는 'directory'
- **텍스트 파일 확장자 확대**: .py, .js, .md, .json, .yml 등 25+ 확장자
- **예시**:
  ```python
  info = h.get_file_info("file.py")
  # {'lineCount': 100, 'lastLine': 99, 'appendPosition': 100, ...}
  ```

## 📊 하위 호환성
- 모든 기존 코드는 수정 없이 정상 작동
- 새로운 파라미터는 선택적 (optional)
- 기존 반환값 구조 유지

## 🧪 테스트 결과
- ✅ 모든 단위 테스트 통과
- ✅ 통합 테스트 성공
- ✅ 웹 자동화 코드와 호환
- ✅ 엣지 케이스 처리 완료

## 📝 변경 파일
1. `python/ai_helpers_new/search.py` - search_files 함수
2. `python/ai_helpers_new/file.py` - info 함수
3. 백업 위치: `backups/api_consistency_20250802_201137/`

## 🚀 사용 권장사항
1. 대용량 프로젝트에서는 `max_depth`로 검색 범위 제한
2. 파일 정보가 필요한 경우 `get_file_info` 사용 (Desktop Commander 대체)
3. 텍스트/바이너리 파일 자동 구분 활용

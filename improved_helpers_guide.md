
# 개선된 헬퍼 함수 사용 가이드

## 파일 작업
- ✅ helpers.read_file(path) - 정상 작동
- ✅ helpers.create_file(path, content) - 정상 작동
- ✅ helpers.write_file(path, content) - create_file과 동일

## 디렉토리 스캔
- ⚠️ helpers.scan_directory_dict() - 작동 안함
- ✅ helpers.scan_directory(path) - 대체 사용

## 검색 기능
- ⚠️ helpers.search_code_content() - 미구현
- ✅ helpers.search_code(path, pattern, file_pattern) - 대체 사용
- ✅ helpers.search_files(path, pattern) - 파일명 검색

## Git 작업
- ⚠️ Git이 설치되지 않은 경우 모든 git_* 메서드 실패
- 해결: Git 설치 후 사용

## 워크플로우
- ✅ helpers.workflow("/status") - 정상 작동
- ✅ helpers.workflow("/task list") - 정상 작동

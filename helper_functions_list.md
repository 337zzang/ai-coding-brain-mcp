# AI Helpers v2.0 함수 목록

## 총 54개의 실제 헬퍼 함수

### file.py 모듈 (10개)
- h.read - 파일 읽기
- h.write - 파일 쓰기
- h.append - 파일에 내용 추가
- h.exists - 파일 존재 확인
- h.info - 파일 정보 조회
- h.list_directory - 디렉토리 목록
- h.read_json - JSON 파일 읽기
- h.write_json - JSON 파일 쓰기
- h.ok - 성공 응답 생성
- h.err - 에러 응답 생성

### code.py 모듈 (8개)
- h.parse - 코드 파싱
- h.view - 코드 뷰어
- h.replace - 코드 교체
- h.insert - 코드 삽입
- h.functions - 함수 목록 조회
- h.classes - 클래스 목록 조회
- h.ok - 성공 응답 생성
- h.err - 에러 응답 생성

### search.py 모듈 (8개)
- h.search_files - 파일 검색
- h.search_code - 코드 내용 검색
- h.find_function - 함수 찾기
- h.find_class - 클래스 찾기
- h.find_in_file - 파일 내 검색
- h.grep - 패턴 검색
- h.ok - 성공 응답 생성
- h.err - 에러 응답 생성

### llm.py 모듈 (10개)
- h.ask_o3_async - o3 비동기 질문
- h.check_o3_status - o3 상태 확인
- h.get_o3_result - o3 결과 조회
- h.list_o3_tasks - o3 작업 목록
- h.show_o3_progress - o3 진행상황 표시
- h.clear_completed_tasks - 완료된 작업 정리
- h.prepare_o3_context - o3 컨텍스트 준비
- h.save_o3_result - o3 결과 저장
- h.ok - 성공 응답 생성
- h.err - 에러 응답 생성

### util.py 모듈 (5개)
- h.is_ok - 성공 여부 확인
- h.get_data - 데이터 추출
- h.get_error - 에러 메시지 추출
- h.ok - 성공 응답 생성
- h.err - 에러 응답 생성

### git.py 모듈 (13개)
- h.git_status - Git 상태 확인
- h.git_add - Git 스테이징
- h.git_commit - Git 커밋
- h.git_push - Git 푸시
- h.git_pull - Git 풀
- h.git_branch - Git 브랜치 관리
- h.git_log - Git 로그 조회
- h.git_diff - Git 차이점 확인
- h.git_current_branch - 현재 브랜치 확인
- h.find_git_executable - Git 실행파일 찾기
- h.run_git_command - Git 명령 실행
- h.ok - 성공 응답 생성
- h.err - 에러 응답 생성

## helpers 객체 추가 함수 (91개)
- 프로젝트 관리, Flow 관리, Task 관리 등 다양한 추가 기능 제공

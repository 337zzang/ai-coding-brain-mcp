# 워크플로우 V2 → V3 마이그레이션 가이드

## 변경 사항 요약

### 1. 파일 구조 변경
- **V2**: `memory/workflow_v2/*.json`
- **V3**: `memory/workflow_v3/*.json`

### 2. API 변경
- 모든 워크플로우 명령은 `helpers.workflow()` 통해 실행
- V2의 개별 함수들은 제거됨

### 3. 명령어 체계
V3는 7개 핵심 명령어로 통합:
- `/start` - 플랜 시작
- `/focus` - 태스크 선택  
- `/plan` - 플랜 관리
- `/task` - 태스크 관리
- `/next` - 태스크 완료 및 진행
- `/build` - 문서화
- `/status` - 상태 조회

### 4. 데이터 마이그레이션
V2 데이터는 자동으로 V3로 마이그레이션됩니다.

## 마이그레이션 단계

1. **백업 생성**
   ```bash
   cp -r memory/workflow_v2 memory/workflow_v2_backup_20250709
   ```

2. **코드 업데이트**
   - HelpersWrapper 사용 시 자동으로 V3 사용
   - 직접 호출 시 `from python.workflow.v3 import execute_workflow_command` 사용

3. **테스트 실행**
   ```bash
   python tests/test_workflow_v3.py
   ```

4. **정리**
   - 테스트 통과 후 V2 디렉토리 제거 가능

## 주의사항
- V3는 이벤트 기반으로 모든 활동이 기록됨
- 프로젝트별로 독립적인 워크플로우 파일 관리
- ContextIntegration을 통한 자동 동기화

## 문제 해결
- 마이그레이션 오류 시 `WorkflowMigrator` 로그 확인
- 데이터 손상 시 자동 백업 파일에서 복구 가능

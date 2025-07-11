# Workflow v2 Release Notes

## Version 2.0.0
**Release Date**: 2025-07-08

## 🎉 주요 변경사항

### 새로운 기능
1. **함수형 API** - 모든 기능을 함수로 직접 호출 가능
2. **독립적인 구조** - v1과 완전히 분리된 구현
3. **성능 최적화** - 캐싱, 배치 작업, 원자적 쓰기
4. **프로젝트별 관리** - 각 프로젝트별 독립적인 워크플로우

### 개선사항
- execute_code 환경과의 완벽한 통합
- 향상된 오류 처리
- 명확한 데이터 모델 (WorkflowPlan, Task)
- 컨텍스트 매니저 통합

### 문서화
- 상세한 사용자 가이드
- API Reference
- 마이그레이션 가이드
- 성능 최적화 가이드

## 🚀 시작하기

### 기본 사용법
```python
from workflow.v2 import WorkflowV2Manager

# 매니저 생성
manager = WorkflowV2Manager("my_project")

# 플랜 생성
plan = manager.create_plan("프로젝트", "설명")

# 태스크 추가
task = manager.add_task("할 일", "설명")
```

### helpers를 통한 사용
```python
# 상태 확인
status = helpers.workflow_v2_status()

# 플랜 생성
plan = helpers.workflow_v2_plan("프로젝트", "설명")

# 태스크 추가
task = helpers.workflow_v2_task("할 일", "설명")
```

## 📋 마이그레이션

v1에서 v2로의 마이그레이션은 선택사항입니다.
기존 시스템은 계속 사용 가능하며, 필요시 점진적으로 전환할 수 있습니다.

자세한 내용은 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)를 참조하세요.

## 🙏 감사의 말

Workflow v2 개발에 참여해주신 모든 분들께 감사드립니다.

## 📞 지원

문제나 제안사항이 있으시면 이슈를 등록해주세요.

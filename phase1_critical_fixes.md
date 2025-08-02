
# 🚨 Phase 1: 치명적 오류 긴급 수정

## 📋 현황
- **발견된 `.h.` 오류**: 200개 이상 (25개 파일)
- **영향**: 모든 핵심 기능 작동 불가
- **원인**: 리스트/Path 객체에 잘못된 `.h.` 속성 사용

## 🎯 수정 대상 파일 (우선순위순)
### 1차 수정 (핵심 기능)
1. `enhanced_ultra_simple_repository.py` - Flow 시스템 저장소
2. `ultra_simple_flow_manager.py` - Flow 매니저
3. `simple_flow_commands.py` - Flow 명령어
4. `project.py` - 프로젝트 관리

### 2차 수정 (헬퍼 함수)
5. `file.py` - 파일 작업
6. `code.py` - 코드 분석
7. `git.py` - Git 작업
8. `search.py` - 검색 기능

### 3차 수정 (유틸리티)
9. `safe_wrappers.py` - 안전 래퍼
10. `task_logger.py` - 작업 로거
11. 기타 파일들

## 🛠️ 수정 방법
### `.h.` 패턴별 수정 규칙
| 패턴 | 수정 방법 |
|------|----------|
| `list.h.append()` | `list.append()` |
| `Path.h.exists()` | `Path.exists()` |
| `dict.h.get()` | `dict.get()` |
| `str.h.split()` | `str.split()` |

## 📊 작업 계획
1. **TODO #1**: 핵심 Flow 시스템 파일 수정 (1-4번)
2. **TODO #2**: 헬퍼 함수 파일 수정 (5-8번)
3. **TODO #3**: 유틸리티 파일 수정 (9-11번)
4. **TODO #4**: 전체 테스트 및 검증

## ⚠️ 주의사항
- 한 파일씩 수정 후 즉시 테스트
- 수정 전 백업 (Git 사용)
- AST 검증으로 구문 오류 방지

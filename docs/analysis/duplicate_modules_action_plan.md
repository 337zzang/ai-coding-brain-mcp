# AI Coding Brain MCP - 중복 모듈 정리 계획

## 📅 작성일: 2025-08-08

## 🔍 분석 결과 요약

### O3 분석 (77.5초, high reasoning)
- PROJECT 계열: project.py를 메인으로 유지
- REPLACE 계열: code.py를 단일 진입점으로
- FLOW 계열: flow_api.py를 퍼사드로 고정

### Claude 분석
- __init__.py에서 실제 import되는 파일 확인
- 사용 중: project.py, code.py, flow_api.py, ultra_simple_flow_manager.py
- 미사용: *_improved.py, *_refactored.py, *_final.py 등

## 🎯 실행 계획

### 즉시 삭제 가능 (위험도: 낮음)
1. project_improved.py
2. project_refactored.py
3. integrate_replace_block.py
4. smart_replace_ultimate.py (구문 오류)

### 검토 후 통합 (위험도: 중간)
1. improved_insert_delete.py → code.py로 통합
2. replace_block_final.py → 유용한 기능만 code.py로
3. project_context.py → ProjectContext를 project.py로

### 신중한 검토 필요 (위험도: 높음)
1. flow 시스템 전체 재구조화
2. contextual_flow_manager.py vs ultra_simple_flow_manager.py

## ⚠️ 주의사항
1. 각 단계별로 테스트 실행
2. Git 브랜치에서 작업
3. 백업 유지
4. import 경로 업데이트 필수

## 📊 예상 효과
- 파일 수: 약 30% 감소
- 코드 중복: 50% 이상 제거
- 유지보수성: 크게 향상
- 혼란 감소: 명확한 단일 진입점

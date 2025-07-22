# Flow 경로 관리 개선 - 요약

## 핵심 변경사항
1. **ProjectContext 클래스** - 프로젝트 루트 관리
2. **동적 Repository** - 경로 변경 가능
3. **프로젝트별 메타데이터** - 전역 파일 제거
4. **switch_project API** - 런타임 프로젝트 전환

## 구현 순서
1. ProjectContext 구현
2. Repository 개선
3. FlowService 개선  
4. FlowManager 개선
5. 테스트 및 검증

## 예상 효과
- 프로젝트별 독립적 Flow 관리
- 한 프로세스에서 여러 프로젝트 처리
- 기존 코드와 호환성 유지

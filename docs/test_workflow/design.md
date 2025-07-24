
## 📋 작업 제목: Context Reporter 구현

### 🏗️ 전체 설계 (Architecture Design)
- **목표**: Context 데이터를 분석하여 유용한 리포트 생성
- **범위**: 기본 통계, 성능 분석, 에러 요약
- **접근 방법**: 간단하고 실용적인 구현
- **예상 소요 시간**: 1시간

### 🔍 현재 상태 분석
- Context 파일이 .ai-brain/contexts/에 저장됨
- auto_record로 자동 기록 중
- JSON 형식으로 이벤트 저장

### 📐 상세 설계
1. **ContextReporter 클래스**
   - load_context(flow_id): Context 파일 로드
   - generate_stats(): 기본 통계 생성
   - get_slow_operations(): 느린 작업 찾기
   - create_report(): Markdown 리포트 생성

### 🛠️ Task별 실행 계획
#### Task 1: ContextReporter 클래스 구현
- 목표: 핵심 클래스 구현
- 예상 시간: 30분

#### Task 2: 리포트 생성 기능
- 목표: Markdown 형식 리포트
- 예상 시간: 20분

#### Task 3: 테스트 및 문서화
- 목표: 실제 사용 예시
- 예상 시간: 10분

# Wisdom 시스템 재설계 - AI Coding Brain MCP

## 개요
AI Coding Brain MCP 환경에 최적화된 Wisdom 시스템 재설계안입니다. Claude Desktop의 MCP 도구 환경에서 코드 품질을 자동으로 관리하고 개선하는 통합 시스템을 구축합니다.

## 핵심 목표
1. **단일 진입점**: WisdomFactory를 통한 중앙 집중식 인스턴스 관리
2. **플러그인 시스템**: 확장 가능한 패턴 감지/수정 규칙
3. **자동 수정 루프**: AI 기반 코드 품질 자동 개선
4. **MCP 도구 통합**: execute_code와 완벽한 통합

## 1. WisdomFactory - 단일 팩토리 패턴

### 현재 문제점
- 여러 모듈에서 독립적으로 Wisdom 인스턴스 생성
- 프로젝트별 데이터 격리 미흡
- MCP 도구와 Python 코드 간 상태 불일치

### 해결책: WisdomFactory
```python
# python/core/wisdom_factory.py
class WisdomFactory:
    """MCP 환경에서 공유되는 Wisdom 인스턴스 관리"""
    
    _instances: Dict[str, ProjectWisdomManager] = {}
    
    @classmethod
    def get_manager(cls, project_id: str = None) -> ProjectWisdomManager:
        """프로젝트별 Wisdom Manager 반환 (싱글톤)"""
        # 현재 프로젝트 자동 감지
        # 인스턴스 캐싱
        # 통합 설정 관리
```

## 2. 플러그인 시스템

### 베이스 구조
```python
# python/core/wisdom_plugin_base.py
@dataclass
class WisdomPattern:
    key: str                    # 패턴 ID
    name: str                   # 표시명
    severity: str              # critical/high/medium/low
    fix_hint: Optional[str]    # 수정 힌트
    auto_fixable: bool = False # 자동 수정 가능 여부

class WisdomPlugin(ABC):
    """플러그인 베이스 클래스"""
    @abstractmethod
    def analyze(self, code: str) -> List[Detection]
    
    @abstractmethod
    def auto_fix(self, code: str, detection: Detection) -> str
```

### 기본 플러그인
1. **PythonIndentationPlugin**: 들여쓰기 규칙 검사
2. **ConsoleUsagePlugin**: console 사용 감지 및 logger 변환
3. **HardcodedPathPlugin**: 하드코딩된 경로 감지

## 3. 자동 수정 루프

### WisdomAutoFixer
```python
# python/core/wisdom_auto_fix.py
class WisdomAutoFixer:
    def analyze_and_fix(self, code: str) -> Tuple[str, List[Detection]]:
        # 1. 빠른 패턴 검사 (정규식)
        # 2. AST 기반 심층 분석
        # 3. 심각도별 분류
        # 4. 치명적 문제 시 실행 차단
        # 5. 자동 수정 적용
        # 6. 학습 데이터 저장
```

### Execute Code 통합
```python
# python/core/wisdom_execute_wrapper.py
class WisdomExecuteWrapper:
    def safe_execute(self, code: str) -> dict:
        # 1. Wisdom 분석
        # 2. 자동 수정
        # 3. 안전 검증
        # 4. 실제 실행
        # 5. 결과 학습
```

## 4. MCP 도구 확장

### 새로운 도구들

#### wisdom_analyze
- 코드 실행 전 품질 분석
- 자동 수정 옵션
- 상세 리포트 제공

#### wisdom_learn
- 새로운 패턴 학습
- 팀 규칙 추가
- 베스트 프랙티스 공유

#### wisdom_export
- 학습 데이터 내보내기
- 팀 간 지식 공유
- 다양한 포맷 지원 (JSON/CSV/Markdown)

## 5. 구현 로드맵

### Phase 1 (즉시 구현)
- [ ] WisdomFactory 구현
- [ ] 기존 코드 마이그레이션
- [ ] 기본 플러그인 3개 구현

### Phase 2 (1주일)
- [ ] wisdom_analyze MCP 도구 추가
- [ ] execute_code 래퍼 적용
- [ ] 자동 수정 기능 활성화

### Phase 3 (2주일)
- [ ] wisdom_learn, wisdom_export 도구 추가
- [ ] 팀 공유 기능 구현
- [ ] VS Code 확장 연동

## 기대 효과

### 개발 효율성
- 코드 품질 문제 90% 자동 감지
- 반복되는 실수 사전 차단
- 일관된 코딩 표준 유지

### 팀 협업
- 지식 공유 자동화
- 베스트 프랙티스 전파
- 신규 개발자 온보딩 가속

### AI 통합
- Claude와의 원활한 협업
- 자동 코드 개선
- 지속적인 학습과 진화

## 결론
이 재설계안은 AI Coding Brain MCP 환경에서 Wisdom 시스템을 더욱 강력하고 확장 가능하게 만듭니다. 단일 팩토리 패턴으로 일관성을 확보하고, 플러그인 시스템으로 확장성을 제공하며, 자동 수정 루프로 개발 효율성을 극대화합니다.

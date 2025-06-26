# ProjectAnalyzer 시스템 구현 계획

## 1. 디렉토리 구조 변경

### 신규 생성
```
python/
├── analyzers/
│   ├── __init__.py
│   ├── project_analyzer.py      # 메인 분석 오케스트레이터
│   ├── file_analyzer.py         # 개별 파일 분석 (AST + AI)
│   └── manifest_manager.py      # Manifest 읽기/쓰기 관리
```

### 삭제 대상
- ❌ python/enhanced_file_directory_generator.py
- ❌ python/enhanced_file_directory_generator.backup.py  
- ❌ python/file_directory_generator.py
- ❌ memory/file_directory.md (manifest.json으로 대체)

## 2. project_manifest.json 구조

```json
{
  "project_name": "ai-coding-brain-mcp",
  "last_analyzed": "2025-06-25T14:30:00Z",
  "total_files": 358,
  "analyzed_files": 45,
  "structure": {
    "python/": {
      "type": "directory",
      "file_count": 25,
      "summary": "Python 백엔드 코드 및 헬퍼 함수들"
    }
  },
  "files": {
    "python/commands/enhanced_flow.py": {
      "path": "python/commands/enhanced_flow.py",
      "last_modified": "2025-06-25T11:11:29Z",
      "size": 15234,
      "language": "python",
      "summary": "프로젝트 전환과 상태 브리핑을 담당하는 핵심 모듈",
      "imports": {
        "internal": ["project_wisdom", "helpers"],
        "external": ["os", "sys", "json"]
      },
      "classes": [],
      "functions": [
        {
          "name": "flow_project",
          "line": 498,
          "params": ["project_name: str"],
          "returns": "Dict[str, Any]",
          "summary": "프로젝트를 전환하고 전체 상태를 브리핑",
          "complexity": "high",
          "calls": ["find_project_root", "get_wisdom_manager"]
        }
      ],
      "wisdom_insights": {
        "potential_issues": [],
        "improvement_suggestions": ["캐시 활용 가능"]
      }
    }
  },
  "dependencies": {
    "graph": {
      "enhanced_flow.py": ["project_wisdom.py", "helpers.py"],
      "project_wisdom.py": ["wisdom_hooks.py"]
    }
  }
}
```

## 3. 구현 단계

### Phase 1: 기본 구조 구축 (1-2시간)
1. `python/analyzers/` 디렉토리 생성
2. `ProjectAnalyzer` 클래스 기본 구조 구현
3. 기존 `helpers.parse_with_snippets()` 활용한 AST 분석 통합

### Phase 2: Manifest 관리 (2-3시간)
1. `ManifestManager` 클래스 구현
2. 파일 변경 감지 (last_modified 비교)
3. 증분 업데이트 로직

### Phase 3: AI 요약 통합 (2-3시간)
1. AST 정보 기반 AI 요약 프롬프트 생성
2. 파일/함수별 의미 기반 요약 생성
3. 의존성 그래프 자동 생성

### Phase 4: 기존 시스템 통합 (1-2시간)
1. `flow_project()`에서 ProjectAnalyzer 호출
2. Wisdom 시스템과 통합
3. 기존 file_directory 생성기들 제거

## 4. 기대 효과

1. **성능 향상**
   - 파일 변경 감지로 불필요한 재분석 방지
   - 캐시된 Manifest로 즉시 프로젝트 구조 파악

2. **AI 정확도 향상**
   - 구조화된 컨텍스트 제공
   - 의존성 정보로 관련 파일 자동 포함

3. **유지보수성**
   - 단일 진실 공급원 (Single Source of Truth)
   - 모듈화된 구조로 확장 용이

## 5. 마이그레이션 계획

1. 기존 `file_directory.md` → `project_manifest.json` 변환 스크립트
2. 점진적 마이그레이션 (기존 기능 유지하며 전환)
3. 완전 전환 후 구 시스템 제거

## 6. 통합/삭제 대상 상세 분석

### 삭제 대상 파일들

#### 1. 파일 구조 생성기들 (3개)
- **삭제 이유**: 모두 같은 기능을 중복 구현
- **대체 방법**: `ProjectAnalyzer.generate_structure_report()`

#### 2. memory/file_directory.md
- **삭제 이유**: 구조화되지 않은 텍스트 형식
- **대체 방법**: `memory/project_manifest.json`의 구조화된 데이터

### 통합 대상 기능들

#### 1. AST 분석
- **현재**: `helpers.parse_with_snippets()` + `ast_wisdom_analyzer.py`
- **통합 후**: `FileAnalyzer` 클래스로 일원화

#### 2. Wisdom 시스템
- **현재**: 별도 모듈로 동작
- **통합 후**: ProjectAnalyzer 파이프라인에 통합

#### 3. 컨텍스트 관리
- **현재**: 여러 곳에 분산된 상태 정보
- **통합 후**: Manifest 기반 중앙 집중식 관리

## 7. 코드 예시

### ProjectAnalyzer 사용 예시
```python
# 기존 방식 (enhanced_flow.py)
file_structure = generate_file_directory()
wisdom_data = load_wisdom()
context = load_context()
briefing = create_briefing(file_structure, wisdom_data, context)

# 새로운 방식
analyzer = ProjectAnalyzer('.')
analyzer.analyze_and_update()  # 모든 분석 수행
manifest = analyzer.get_manifest()
briefing = analyzer.generate_briefing()
```

### Manifest 활용 예시
```python
# AI에게 컨텍스트 제공
manifest = analyzer.get_manifest()
context = f"""
프로젝트: {manifest['project_name']}
총 파일: {manifest['total_files']}개
주요 모듈:
{analyzer.get_module_summary()}

작업할 파일 'enhanced_flow.py'의 정보:
- 역할: {manifest['files']['enhanced_flow.py']['summary']}
- 의존성: {manifest['files']['enhanced_flow.py']['imports']}
"""
```
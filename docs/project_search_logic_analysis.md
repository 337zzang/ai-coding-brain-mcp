# flow_project_with_workflow() 검색 로직 분석 및 개선

## 현재 검색 로직

### find_project_path() 함수 동작
```python
def find_project_path(project_name: str) -> Optional[str]:
    # 1. 현재 디렉토리
    if current.name == project_name:
        return str(current)
    
    # 2. 형제 디렉토리
    for path in parent.iterdir():
        if path.name == project_name:
            return str(path)
    
    # 3. Desktop 디렉토리
    for path in desktop.iterdir():
        if path.name == project_name:
            return str(path)
    
    # 4. 홈 디렉토리
    for path in home.iterdir():
        if path.name == project_name:
            return str(path)
    
    return None
```

## 문제점

### 1. 단순 이름 매칭
- 폴더 이름만 확인
- 실제 프로젝트 검증 없음
- .ai-brain 존재 여부 미확인

### 2. 중첩 구조 처리 불가
```
Desktop/
└── sales_ocr/          ← 실제 프로젝트
    └── sales_ocr/      ← 중첩 (문제!)
        └── README.md   ← 파일들이 여기 생성됨
```

### 3. 검색 깊이 제한
- 1단계 깊이만 검색
- 하위 폴더 구조 무시

## 개선 방안

### 1. 스마트 프로젝트 검색
```python
def find_project_path_improved(project_name: str) -> Optional[str]:
    """개선된 프로젝트 검색"""
    candidates = []
    
    # 검색 경로들
    search_paths = [
        Path.cwd(),
        Path.home() / "Desktop",
        Path.home()
    ]
    
    for base_path in search_paths:
        # 재귀적 검색 (rglob 사용)
        for path in base_path.rglob(project_name):
            if not path.is_dir():
                continue
            
            # 프로젝트 점수 계산
            score = calculate_project_score(path)
            candidates.append((score, path))
    
    # 최고 점수 프로젝트 반환
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_path = candidates[0]
        
        # 다중 매칭 경고
        if len(candidates) > 1:
            print(f"⚠️ {len(candidates)}개의 '{project_name}' 발견")
            print(f"   선택: {best_path}")
        
        return str(best_path)
    
    return None
```

### 2. 프로젝트 점수 계산
```python
def calculate_project_score(path: Path) -> int:
    """프로젝트 유효성 점수 계산"""
    score = 0
    
    # Flow 프로젝트 (최우선)
    if (path / ".ai-brain").exists():
        score += 100
    
    # Git 저장소
    if (path / ".git").exists():
        score += 50
    
    # 프로젝트 파일들
    if (path / "requirements.txt").exists():
        score += 20  # Python
    if (path / "package.json").exists():
        score += 20  # Node.js
    if (path / "Cargo.toml").exists():
        score += 20  # Rust
    
    # 중첩 구조 페널티
    if path.parent.name == path.name:
        score -= 30
        print(f"⚠️ 중첩 구조 감지: {path}")
    
    # README 존재
    if (path / "README.md").exists():
        score += 10
    
    # 깊이 페널티 (너무 깊은 곳은 감점)
    depth = len(path.parts)
    if depth > 10:
        score -= (depth - 10) * 5
    
    return score
```

### 3. 중첩 구조 자동 수정
```python
def fix_nested_structure(path: Path) -> Path:
    """중첩된 구조 자동 수정"""
    if path.parent.name == path.name:
        print(f"🔧 중첩 구조 수정 중...")
        
        nested = path
        parent = path.parent
        
        # 중첩된 파일들을 상위로 이동
        import shutil
        for item in nested.iterdir():
            target = parent / item.name
            if not target.exists():
                shutil.move(str(item), str(target))
                print(f"   이동: {item.name}")
        
        # 빈 중첩 폴더 삭제
        if not list(nested.iterdir()):
            nested.rmdir()
            print(f"   삭제: {nested.name}/")
        
        return parent
    
    return path
```

### 4. 프로젝트 생성 옵션 추가
```python
def flow_project_with_workflow(
    project: str,
    create_if_not_exists: bool = False,
    auto_fix_nested: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """개선된 프로젝트 전환"""
    
    # 1. 프로젝트 검색
    project_path = find_project_path_improved(project)
    
    # 2. 못 찾으면 생성 옵션 확인
    if not project_path and create_if_not_exists:
        project_path = create_new_project(project)
    
    # 3. 여전히 없으면 에러
    if not project_path:
        return {
            "ok": False,
            "error": f"프로젝트를 찾을 수 없습니다: {project}"
        }
    
    # 4. 중첩 구조 자동 수정
    if auto_fix_nested:
        project_path = fix_nested_structure(Path(project_path))
    
    # 5. 나머지 로직...
    return {"ok": True, "data": {...}}
```

## 테스트 시나리오

| 시나리오 | 현재 동작 | 개선 후 |
|----------|----------|---------|
| 새 프로젝트 | ❌ 에러 | ✅ 자동 생성 |
| 중첩 구조 | ❌ 잘못된 위치 | ✅ 자동 수정 |
| 다중 매칭 | ❌ 첫 번째 선택 | ✅ 점수 기반 선택 |
| 깊은 구조 | ❌ 못 찾음 | ✅ 재귀 검색 |

## 구현 우선순위

1. **Phase 1** - 중첩 구조 감지
2. **Phase 2** - 프로젝트 점수 시스템
3. **Phase 3** - 자동 생성 옵션
4. **Phase 4** - 중첩 자동 수정

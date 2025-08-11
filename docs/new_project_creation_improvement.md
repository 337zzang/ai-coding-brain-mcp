# 새 프로젝트 생성 시스템 개선 방안

## 문제 진단

### 발견된 문제
1. **flow_project_with_workflow()의 한계**
   - 기존 프로젝트만 검색 가능
   - 새 프로젝트 생성 기능 없음
   - 프로젝트가 없으면 에러 반환

2. **수동 생성의 문제점**
   - Flow 시스템과 연동 안됨
   - 표준 구조 보장 안됨
   - 메타데이터 없음

## 개선 방안

### 1. create_new_project() 함수 추가
```python
def create_new_project(
    project_name: str,
    base_path: str = None,
    template: str = "default",
    auto_init: bool = True
) -> Dict[str, Any]:
    """
    새 프로젝트 생성 및 초기화
    
    Args:
        project_name: 프로젝트 이름
        base_path: 기본 경로 (기본값: Desktop)
        template: 프로젝트 템플릿
        auto_init: 자동 초기화 여부
    """
    # 구현 내용
```

### 2. flow_project_with_workflow() 개선
```python
def flow_project_with_workflow(
    project: str,
    create_if_not_exists: bool = False,  # 새 옵션
    template: str = "default",
    **kwargs
) -> Dict[str, Any]:
    """개선된 프로젝트 전환 함수"""
    
    project_path = find_project_path(project)
    
    if not project_path:
        if create_if_not_exists:
            # 새 프로젝트 자동 생성
            result = create_new_project(project, template=template)
            if result['ok']:
                project_path = result['data']['project']['path']
        else:
            return {"ok": False, "error": f"프로젝트를 찾을 수 없습니다: {project}"}
    
    # 기존 로직 계속...
```

### 3. 프로젝트 템플릿 시스템

```python
PROJECT_TEMPLATES = {
    "default": {
        "dirs": ["docs", "src", "test", "data"],
        "files": {
            "README.md": "# {project_name}\n\n## 프로젝트 개요\n",
            ".gitignore": "__pycache__/\n*.pyc\n.env\n",
            "requirements.txt": ""
        }
    },
    "ocr": {
        "dirs": ["docs", "src", "test", "data/input", "data/output", "logs"],
        "files": {
            "README.md": "# {project_name} - OCR Project\n",
            "requirements.txt": "pytesseract\neasyocr\nopencv-python\n"
        }
    },
    "web": {
        "dirs": ["docs", "src", "test", "logs/web_automation"],
        "files": {
            "README.md": "# {project_name} - Web Automation\n",
            "requirements.txt": "playwright\nbeautifulsoup4\n"
        }
    }
}
```

### 4. 구현 우선순위

1. **Phase 1** (즉시)
   - create_new_project() 함수 구현
   - 기본 템플릿 생성

2. **Phase 2** (단기)
   - flow_project_with_workflow()에 create_if_not_exists 옵션 추가
   - 템플릿 시스템 구현

3. **Phase 3** (장기)
   - 프로젝트 마이그레이션 도구
   - 프로젝트 백업/복원 기능

## 예상 효과

### Before (현재)
```python
h.flow_project_with_workflow("new_project")
# ❌ Error: 프로젝트를 찾을 수 없습니다
```

### After (개선 후)
```python
h.flow_project_with_workflow("new_project", create_if_not_exists=True)
# ✅ 새 프로젝트 생성 및 전환 완료
```

## 테스트 시나리오

1. 존재하지 않는 프로젝트 전환 → 자동 생성
2. 템플릿 적용 확인
3. Flow 시스템 등록 확인
4. list_projects()에 표시 확인

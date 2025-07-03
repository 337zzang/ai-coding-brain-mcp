# VSCode Python 자동 포맷팅 설정 가이드

이 가이드는 VSCode에서 Python 파일 저장 시 자동으로 포맷팅과 구문 검사를 수행하는 방법을 설명합니다.

## 1. 필요한 패키지 설치

```bash
# Black (코드 포맷터)
pip install black

# Ruff (빠른 Python 린터 및 포맷터)
pip install ruff

# 추가 도구들
pip install isort  # import 정렬
pip install flake8  # 추가 린팅
```

## 2. VSCode 확장 프로그램 설치

VSCode 확장 마켓플레이스에서 다음 확장 프로그램을 설치하세요:

- **Python** (Microsoft)
- **Pylance** (Microsoft)
- **Black Formatter** (Microsoft)
- **Ruff** (Astral Software)

## 3. VSCode 설정 (settings.json)

`.vscode/settings.json` 파일을 생성하고 다음 내용을 추가하세요:
```json
{
    // Python 기본 설정
    "python.linting.enabled": true,
    "python.linting.lintOnSave": true,
    
    // Black 설정 (코드 포맷팅)
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    },
    
    // Black 설정 옵션
    "black-formatter.args": [
        "--line-length=88",
        "--skip-string-normalization"
    ],
    
    // Ruff 설정 (빠른 린팅)
    "ruff.enable": true,
    "ruff.lint.run": "onSave",
    "ruff.fixAll": true,
    "ruff.organizeImports": true,
    
    // 추가 린팅 도구
    "python.linting.flake8Enabled": false,  // Ruff와 중복 방지
    "python.linting.pylintEnabled": false,   // Ruff 사용 시 비활성화
    
    // 자동 저장 설정 (선택사항)
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 1000
}
```

## 4. 프로젝트별 설정 파일

### pyproject.toml (Black 설정)

```toml
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
skip-string-normalization = true
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | __pycache__
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 88
```

### ruff.toml (Ruff 설정)

```toml
# Ruff 설정
line-length = 88
target-version = "py38"

[lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]  # 라인 길이는 Black이 처리

[format]
# Black 호환 설정
quote-style = "double"
indent-style = "space"
```

## 5. 사용 방법

1. **저장 시 자동 포맷팅**: 
   - `Ctrl+S` (Windows/Linux) 또는 `Cmd+S` (Mac)를 누르면 자동으로:
     - Black이 코드를 포맷팅
     - Ruff가 구문 오류와 스타일 문제를 수정
     - import 문이 정렬됨

2. **수동 포맷팅**:
   - 명령 팔레트 (`Ctrl+Shift+P`) → "Format Document"
   - 또는 `Shift+Alt+F` (Windows/Linux) / `Shift+Option+F` (Mac)

3. **린팅 결과 확인**:
   - Problems 패널 (`Ctrl+Shift+M`)에서 모든 경고와 오류 확인
   - 파일 내 빨간 밑줄과 노란 밑줄로 표시

## 6. 프로젝트에 통합하기

```bash
# 프로젝트 루트에서 실행
cd C:\Users\82106\Desktop\ai-coding-brain-mcp

# 설정 파일 생성
mkdir -p .vscode
# settings.json 복사

# 포맷터 설정 파일 생성
# pyproject.toml 생성
# ruff.toml 생성

# 테스트
python -m black . --check
python -m ruff check .
```

## 7. 팀 협업을 위한 pre-commit 설정 (선택사항)

`.pre-commit-config.yaml` 파일 생성:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.14
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

```bash
# pre-commit 설치 및 활성화
pip install pre-commit
pre-commit install
```

## 8. 문제 해결

1. **포맷팅이 작동하지 않는 경우**:
   - Python 인터프리터가 올바르게 선택되었는지 확인
   - 필요한 패키지가 설치되었는지 확인: `pip list | grep black`
   - VSCode를 재시작

2. **충돌하는 설정**:
   - 한 번에 하나의 포맷터만 사용 (Black 또는 Ruff 중 선택)
   - 프로젝트 설정이 사용자 설정을 덮어쓰도록 설정

3. **느린 성능**:
   - Ruff는 Rust로 작성되어 매우 빠름
   - 대용량 파일의 경우 `"editor.formatOnSaveTimeout": 5000` 추가

## 결론

이 설정으로 Python 파일을 저장할 때마다 자동으로:
- ✅ 코드가 일관된 스타일로 포맷팅됨
- ✅ 구문 오류가 즉시 표시됨
- ✅ import 문이 정리됨
- ✅ 일반적인 코드 품질 문제가 수정됨

더 이상 수동으로 코드 스타일을 맞추거나 구문 오류를 찾는 데 시간을 낭비하지 않아도 됩니다!

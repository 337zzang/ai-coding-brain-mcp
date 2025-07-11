# Git Helper 사용법

## 빠른 Push (권장)
```bash
python scripts/git_helper.py quick -m "feat: 새 기능 추가"
```

## 개별 명령
```bash
# 상태 확인
python scripts/git_helper.py status

# 파일 추가
python scripts/git_helper.py add
python scripts/git_helper.py add -f "specific_file.py"

# 커밋
python scripts/git_helper.py commit -m "커밋 메시지"

# Push
python scripts/git_helper.py push
python scripts/git_helper.py push -r origin -b develop
```

## Python에서 사용
```python
from scripts.git_helper import GitHelper

git = GitHelper()

# 상태 확인
status = git.status()
print(f"변경 파일: {status['total_changes']}개")

# 빠른 push
result = git.quick_push("feat: 새 기능 추가")
```

## 특징
- Git 경로 자동 탐지
- Windows 인코딩 문제 해결
- Lock 파일 자동 처리
- 에러 메시지 한글 지원

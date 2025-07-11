# Git 처리 문제점 종합 분석

## 1. 🔴 주요 문제점들

### 1.1 작업 디렉토리 문제
**문제**: Git 명령이 잘못된 디렉토리(홈 디렉토리)에서 실행됨
```
On branch backup-before-rollback-20250703
Untracked files:
  ../../../../.anaconda/
  ../../../../.android/
  ... (전체 홈 디렉토리 파일들)
```
**원인**: 
- 작업 디렉토리 변경이 제대로 적용되지 않음
- subprocess나 명령 실행 시 cwd 파라미터 누락

**해결책**:
```python
# 명시적 작업 디렉토리 지정
subprocess.run(cmd, cwd='C:\Users\82106\Desktop\ai-coding-brain-mcp')
```

### 1.2 Git 실행 파일 경로 문제
**문제**: 'git'은(는) 내부 또는 외부 명령... 오류
**원인**: 
- PATH 환경변수에 Git이 없음
- shell=True 사용 시 Git 경로를 찾지 못함

**해결책**:
```python
# Git 전체 경로 사용
git_path = "C:\Program Files\Git\cmd\git.exe"
subprocess.run(f'"{git_path}" status')
```

### 1.3 인코딩 문제
**문제**: UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb7
**원인**: 
- Windows 한국어 환경에서 cp949 인코딩 사용
- subprocess 기본 인코딩이 utf-8

**해결책**:
```python
subprocess.run(cmd, encoding='cp949')  # Windows 한국어
```

### 1.4 Git Lock 파일 문제
**문제**: Unable to create '.git/index.lock': File exists
**원인**: 
- 이전 Git 프로세스가 비정상 종료
- 동시에 여러 Git 명령 실행

**해결책**:
```python
if os.path.exists('.git/index.lock'):
    os.remove('.git/index.lock')
```

### 1.5 AI Coding Brain MCP의 제한사항
**문제**: helpers에 git_add, git_push 등 메서드 없음
**현재 가능한 Git 메서드**:
- helpers.git_status()
- helpers.git_commit()
- helpers.git_log()

**없는 메서드**:
- git_add (❌)
- git_push (❌)
- git_branch (❌)
- git_checkout (❌)

## 2. 🟡 부가적 문제점들

### 2.1 PowerShell vs CMD 차이
**문제**: PowerShell에서 && 연산자 인식 못함
```powershell
# 실패
cd path && git status

# 성공 (분리 실행)
cd path
git status
```

### 2.2 권한 문제
**문제**: Permission denied 경고들
```
warning: could not open directory 'Application Data/': Permission denied
```
**원인**: Windows 시스템 폴더 접근 시도

### 2.3 모듈 임포트 문제
**문제**: Python 모듈 임포트 시 상대/절대 경로 혼재
```python
# 문제
from ai_helpers.search import ...  # 절대 임포트
# 해결
from .search import ...  # 상대 임포트
```

## 3. 💚 성공적인 해결 방법

### 3.1 최종 작동 코드
```python
# 1. Git 실행 파일 찾기
git_paths = [
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files (x86)\Git\cmd\git.exe",
]
git_path = next((p for p in git_paths if os.path.exists(p)), None)

# 2. Git 명령 실행
def run_git(args):
    cmd = f'"{git_path}" {args}'
    return subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        encoding='cp949',  # Windows 한국어
        cwd=os.getcwd()    # 명시적 작업 디렉토리
    )

# 3. Git 작업 수행
run_git('add .')
run_git('commit -m "message"')
run_git('push origin master')
```

### 3.2 Desktop Commander 활용
```python
# 대안: Desktop Commander 사용
desktop_commander:execute_command(
    command='git add .',
    shell='cmd'  # PowerShell 대신 CMD 사용
)
```

## 4. 🔧 개선 제안사항

### 4.1 AI Coding Brain MCP 개선
```python
# helpers에 추가되면 좋을 메서드들
helpers.git_add(files='.')
helpers.git_push(branch='master', remote='origin')
helpers.git_pull()
helpers.git_branch(name='feature/new')
helpers.git_checkout(branch='develop')
helpers.git_merge(branch='feature/done')
helpers.git_stash_save(message='WIP')
helpers.git_stash_pop()
```

### 4.2 통합 Git 워크플로우
```python
class GitWorkflow:
    """통합 Git 작업 클래스"""

    def __init__(self):
        self.git_path = self._find_git()
        self.encoding = 'cp949' if os.name == 'nt' else 'utf-8'

    def _find_git(self):
        """Git 실행 파일 자동 탐색"""
        # 구현...

    def add_commit_push(self, message):
        """한 번에 add, commit, push"""
        self.run('add .')
        self.run(f'commit -m "{message}"')
        self.run('push')
```

### 4.3 에러 처리 개선
```python
def safe_git_operation(operation):
    """안전한 Git 작업 실행"""
    try:
        # Lock 파일 확인
        remove_lock_if_exists()

        # 작업 디렉토리 확인
        ensure_in_git_repo()

        # Git 실행
        result = operation()

        return result
    except GitNotFoundError:
        return install_git_instructions()
    except EncodingError:
        return try_different_encoding()
```

## 5. 📋 체크리스트

Git 작업 전 확인사항:
- [ ] 올바른 작업 디렉토리인가?
- [ ] Git이 PATH에 있는가?
- [ ] Lock 파일이 없는가?
- [ ] 인코딩 설정이 맞는가?
- [ ] 적절한 권한이 있는가?

## 6. 🚀 권장 워크플로우

1. **AI Coding Brain MCP 우선 사용**
   ```python
   helpers.git_status()  # 가능
   helpers.git_commit()  # 가능
   ```

2. **부족한 부분은 subprocess로 보완**
   ```python
   run_git_command('add .')
   run_git_command('push')
   ```

3. **복잡한 작업은 Desktop Commander**
   ```python
   desktop_commander:execute_command('git rebase -i HEAD~3')
   ```

4. **최후의 수단: 수동 실행 안내**
   ```
   Git Bash를 열고 다음 명령을 실행하세요:
   $ git add .
   $ git commit -m "message"
   $ git push
   ```

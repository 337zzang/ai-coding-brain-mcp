# Context System 환경변수 설정 가이드

## Windows (Command Prompt)
```cmd
set CONTEXT_SYSTEM=on
```

## Windows (PowerShell)
```powershell
$env:CONTEXT_SYSTEM="on"
```

## Linux/Mac
```bash
export CONTEXT_SYSTEM=on
```

## 영구 설정

### Windows
시스템 환경변수에 추가:
1. 시스템 속성 > 고급 > 환경 변수
2. 새로 만들기: CONTEXT_SYSTEM = on

### Linux/Mac
`.bashrc` 또는 `.zshrc`에 추가:
```bash
export CONTEXT_SYSTEM=on
```

## 확인 방법
```python
import os
print(os.environ.get('CONTEXT_SYSTEM', 'off'))
```

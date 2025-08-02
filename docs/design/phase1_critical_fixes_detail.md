# 📋 Phase 1: 치명적 오류 수정 상세 설계

## 🎯 목표
즉시 시스템 안정성을 확보하기 위한 치명적 오류 수정

## 📊 작업 범위 및 영향 분석

### 1. `.h.append` 오류 수정

#### 1.1 영향 파일 및 위치
**project.py (1개 위치)**
- Line 34: `lines.h.append(line)` → `lines.append(line)`
- 함수: `_read_if_exists()`

**code.py (6개 위치)**
- Line 82: `self._current_class['methods'].h.append(func_info)` → `.append()`
- Line 84: `self.functions.h.append(func_info)` → `.append()`
- Line 99: `self.classes.h.append(class_info)` → `.append()`
- Line 108: `self.imports.h.append(alias.name)` → `.append()`
- Line 112: `self.imports.h.append(node.module)` → `.append()`
- Line 118: `self.globals.h.append({...})` → `.append()`
- 함수: `ASTCollector` 클래스의 여러 메서드

**utils/safe_wrappers.py (4개 위치)**
- Line 63: `safe_functions.h.append({...})` → `.append()`
- Line 94: `matching.h.append(func)` → `.append()`
- Line 134: `results.h.append({...})` → `.append()`
- Line 136: `errors.h.append({...})` → `.append()`

#### 1.2 수정 방법
```python
# 잘못된 코드 패턴
list_obj.h.append(item)  # AttributeError!

# 올바른 코드
list_obj.append(item)
```

#### 1.3 검증 계획
- 각 파일 import 테스트
- 관련 함수 단위 테스트 실행
- AST 파싱 기능 통합 테스트

### 2. flow() 함수 반환값 표준화

#### 2.1 현재 문제점
- 일부 명령어 경로에서 return 문 누락
- 반환 형식 불일치 (dict vs None)
- 오류 처리 시 일관성 없는 응답

#### 2.2 수정 방안
```python
# 표준 응답 형식
def flow(command: str = "") -> Dict[str, Any]:
    try:
        # 명령어 처리
        result = process_command(command)
        
        # 항상 표준 형식으로 반환
        return {
            'ok': True,
            'data': result,
            'msg': f'명령 실행 완료: {command}'
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e),
            'msg': f'명령 실행 실패: {command}'
        }
```

#### 2.3 수정 대상 명령어
- `/status` - 상태 확인
- `/list` - Plan 목록
- `/create` - Plan 생성
- `/select` - Plan 선택
- `/task` - Task 관리
- `/delete` - Plan 삭제
- `/project` - 프로젝트 관리
- `/help` - 도움말

### 3. 플랫폼 독립적 경로 처리

#### 3.1 현재 하드코딩된 경로
```python
# 문제 코드
desktop_paths = [
    Path.home() / "Desktop",     # macOS, Linux (영문)
    Path.home() / "바탕화면"      # Windows (한글)
]
```

#### 3.2 개선된 경로 처리
```python
import os
import platform
from pathlib import Path

def get_project_base_path() -> Path:
    """플랫폼 독립적인 프로젝트 기본 경로 반환"""
    
    # 1. 환경변수 우선 확인
    if env_path := os.environ.get('AI_PROJECT_BASE'):
        return Path(env_path)
    
    # 2. 플랫폼별 기본 경로
    system = platform.system()
    
    if system == 'Windows':
        # Windows: Desktop 폴더 자동 탐색
        import winreg
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            ) as key:
                desktop = winreg.QueryValueEx(key, 'Desktop')[0]
                return Path(desktop)
        except:
            pass
    
    # 3. 일반적인 Desktop 경로 시도
    common_paths = [
        Path.home() / "Desktop",
        Path.home() / "바탕화면",
        Path.home() / "桌面",  # 중국어
        Path.home() / "Рабочий стол",  # 러시아어
    ]
    
    for path in common_paths:
        if path.exists():
            return path
    
    # 4. 최종 폴백: 홈 디렉토리
    return Path.home() / "projects"
```

#### 3.3 마이그레이션 전략
- 기존 프로젝트 자동 탐색 기능 추가
- 사용자에게 경로 설정 안내 메시지

## 🔧 구현 계획

### TODO #1: .h.append 오류 전체 수정 (30분)
1. Git 브랜치 생성: `fix/critical-h-append-errors`
2. 각 파일별 수정:
   - `project.py`: 1개 위치
   - `code.py`: 6개 위치  
   - `utils/safe_wrappers.py`: 4개 위치
3. 총 11개 위치 수정
4. 각 파일 import 테스트

### TODO #2: flow() 반환값 표준화 (45분)
1. `simple_flow_commands.py` 분석
2. 표준 응답 래퍼 함수 생성
3. 각 명령어 처리 함수 수정
4. 오류 처리 통일
5. 반환값 테스트

### TODO #3: 플랫폼 독립적 경로 처리 (30분)
1. `get_project_base_path()` 함수 구현
2. `flow_project_with_workflow()` 수정
3. 환경변수 문서화
4. 다양한 플랫폼에서 테스트

### TODO #4: 통합 테스트 및 검증 (15분)
1. 수정된 파일들의 import 테스트
2. Flow 명령어 전체 테스트
3. 프로젝트 전환 테스트
4. Git 커밋 및 PR 준비

## ⚠️ 주의사항

### 1. 호환성 유지
- 기존 API 시그니처 변경 최소화
- 기존 동작 유지하면서 오류만 수정

### 2. 테스트 우선
- 수정 전 현재 상태 백업
- 각 수정 후 즉시 테스트
- 실패 시 즉시 롤백

### 3. 점진적 수정
- 한 번에 하나의 파일만 수정
- 각 수정 후 커밋
- 문제 발생 시 추적 가능

## 📊 예상 결과

### 즉각적 효과
1. **안정성**: AttributeError 제거로 모듈 정상 작동
2. **일관성**: flow() 명령어 안정적인 응답
3. **호환성**: 다양한 플랫폼 지원

### 검증 기준
- [ ] 모든 파일 import 성공
- [ ] flow() 모든 명령어 정상 응답
- [ ] Windows/Mac/Linux에서 프로젝트 전환 성공
- [ ] 기존 테스트 모두 통과

## 🚀 작업 시작 체크리스트
- [ ] 현재 상태 Git 커밋
- [ ] 작업 브랜치 생성
- [ ] 백업 파일 생성
- [ ] 테스트 환경 준비
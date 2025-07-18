
# python/ai_code_guide.py

import json
from typing import Dict, List, Any
from pathlib import Path

class AICodeGuide:
    """AI가 코드 수정 시 참고할 가이드 생성"""

    def __init__(self):
        self.project_patterns = self._load_project_patterns()

    def _load_project_patterns(self) -> Dict[str, Any]:
        """프로젝트의 코드 패턴 로드"""
        return {
            "python_helpers": {
                "naming": "snake_case",
                "return_type": "Dict[str, Any]",
                "error_pattern": "{'success': bool, 'error': str}",
                "docstring": "Google style",
                "example": """
def helper_function(param: str) -> Dict[str, Any]:
    """간단한 설명

    Args:
        param: 파라미터 설명

    Returns:
        Dict with success/error keys
    """
    try:
        # 로직
        return {'success': True, 'result': data}
    except Exception as e:
        return {'success': False, 'error': str(e)}
"""
            },
            "typescript": {
                "naming": "camelCase",
                "export": "named exports preferred",
                "types": "explicit type annotations",
                "example": """
export function processData(input: string): ProcessResult {
    try {
        // logic
        return { success: true, data: result };
    } catch (error) {
        return { success: false, error: error.message };
    }
}
"""
            }
        }

    def generate_ai_prompt(self, 
                          task: str,
                          target_file: str,
                          context: str = "") -> str:
        """AI에게 전달할 프롬프트 생성"""

        file_type = "python_helpers" if target_file.endswith('.py') else "typescript"
        pattern = self.project_patterns[file_type]

        prompt = f"""
## 코드 수정 작업

**작업**: {task}
**대상 파일**: {target_file}

### ⚠️ 필수 준수 사항:

1. **네이밍 규칙**: {pattern['naming']}
2. **반환 타입**: {pattern['return_type']}
3. **에러 처리**: {pattern['error_pattern']}
4. **문서화**: {pattern['docstring']}

### 📋 기존 코드 패턴 예시:
```
{pattern['example']}
```

### 🔍 참고할 컨텍스트:
{context}

### ✅ 체크리스트:
- [ ] 기존 헬퍼 함수 재사용 확인
- [ ] 네이밍 컨벤션 준수
- [ ] 타입 힌트/어노테이션 추가
- [ ] 에러 처리 패턴 일치
- [ ] 적절한 로깅 추가
- [ ] 단위 테스트 가능한 구조

**중요**: 새로운 패턴을 만들지 말고, 기존 프로젝트의 패턴을 따라주세요!
"""
        return prompt

    def create_modification_checklist(self, file_path: str) -> str:
        """수정 전 체크리스트 생성"""

        checklist = f"""
## 📋 {file_path} 수정 체크리스트

### 수정 전 확인사항:
- [ ] 비슷한 기능이 이미 구현되어 있는지 확인
  ```python
  # 검색 명령
  helpers.search_code(".", "유사기능키워드", "*.py")
  ```

- [ ] 현재 파일의 구조 파악
  ```python
  # 함수 목록 확인
  functions = helpers.parse_file("{file_path}")
  ```

- [ ] 의존성 확인
  ```python
  # import 구조 확인
  content = helpers.read_file("{file_path}")
  # import 라인 추출
  ```

### 수정 시 준수사항:
- [ ] 기존 함수와 동일한 네이밍 패턴
- [ ] 동일한 에러 처리 방식
- [ ] 일관된 타입 정의
- [ ] 기존 헬퍼 활용

### 수정 후 검증:
- [ ] 문법 오류 없음
- [ ] 기존 테스트 통과
- [ ] 새 기능 테스트 추가
"""
        return checklist

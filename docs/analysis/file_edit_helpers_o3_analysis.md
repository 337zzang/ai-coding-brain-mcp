아래 내용은 “파일 수정 헬퍼”를 직접 만들어 운영하는 것을 전제로,  
지금까지 불거진 문제(들여쓰기 깨짐, 멀티라인 치환, 탭/스페이스 혼용, 중첩 구조 탐색 난이도)를 체계적으로 해결하기 위한 설계·구현 가이드입니다.

──────────────────────────────────
1. 들여쓰기를 안전하게 보존하는 방법
──────────────────────────────────
1-1. “문자열 치환” 계층에서 할 수 있는 최소한의 방어  
  • 블록 인식용 정규식 작성 시 `(?m)^(?P<indent>[ \t]*)` 캡처 그룹을 항상 포함한다.  
    – 치환 템플릿에서는 `\g<indent>` 를 앞에 붙여 원래 들여쓰기를 그대로 재생성.  
  • 치환 문자열이 여러 줄일 때 `textwrap.indent()` 로 동적으로 들여쓰기 추가.  
  • 파일마다 dominant indent(탭/스페이스, 넓이)를 계산 → 치환 전 전체 문자열에 대해 `re.sub(r'^\t+', ...)` 같은 방식으로 통일한 뒤 작업 → 끝나면 다시 원본 스타일로 복원하는 방법도 가능.

1-2. CST 기반 계층(권장)  
  • libcst(Cement) 는 “Concrete” 트리를 제공하므로 들여쓰기를 별도로 관리할 필요가 없다.  
    – 노드 교체 시에도 `.with_changes()` 나 `cst.Replace()` 가 내부적으로 whitespace/token 을 유지.  
  • 다만 `parse_module(..., config=cst.Config(tab_size=4, default_indent="    "))` 로 파서 설정을 맞춰 주지 않으면, 혼용 파일에서 탭이 스페이스로 강제 변환될 수 있으므로 주의.  
  • 최종 출력 전에 `cst.Module.code` 호출 → 이후 black/ruff format on write 로 완전 정리.

1-3. diff/patch 계층  
  • `difflib.unified_diff()` 로 패치 스트링을 만들어 `patch` 라이브러리(‘python-patch’)로 적용하면, 원본과 대상 양쪽의 indentation 을 모두 그대로 둔 채 부분 치환이 가능.  
  • “edit_block” 스타일 구현 시 실제로 가장 단순한 방법 – 내부에서는 diff 만 생성하고, 적용은 patch 가 수행하므로 들여쓰기 걱정이 없음.

──────────────────────────────────
2. AST(CST) 기반 교체의 한계와 대안
──────────────────────────────────
2-1. 일반 ast 모듈의 한계  
  • 토큰/화이트스페이스/주석 소실 → 마이그레이션 스크립트용이면 OK, 포맷 보존 목적이면 부적합.  
  • 새 문법(패턴매칭 등) 반영이 파이썬 버전 종속적.

2-2. libcst의 한계  
  • 3.11+ 완전 지원까지 약간의 시차.  
  • 성능: 큰 파일(>10k LOC) 한 번 파싱+코드화에 수백 ms~수 s. 빈번한 대량 변경 작업에는 부담.  
  • 노드 좌표(line/col) 기반 편집은 가능하지만 token offset 은 노출하지 않음 → 외부 diff 와 섞기 어렵다.

2-3. 대안/보완  
  • parso: 토큰 보존, 속도가 libcst보다 빠르지만 명시적 변환 API 가 약함.  
  • RedBaron(=baron+parso 래퍼): 사용성은 좋으나 3.10+ 문법 지원이 더딤.  
  • refactor-code / facebook-codemod: libcst 위 thin-wrapper 로, 대량 코드베이스 변환 배치 작업에 특화.  
  • LSP/rope: 심볼 단위 refactoring(이름 바꾸기 등)에 좋음.  
⇒ 결론: “문법, 주석, 포맷을 100% 보존하면서 블록 단위 수정” 요구사항에는 여전히 libcst 가 가장 현실적.

──────────────────────────────────
3. 실용적인 개선 방안
──────────────────────────────────
A. API 레이어 분리
   ┌─────────────┐
   │ TextEngine  │  (정규식/간단치환)
   ├─────────────┤
   │ CSTEngine   │  (libcst 변환기 모음)
   ├─────────────┤
   │ PatchEngine │  (diff/patch, edit_block)
   └─────────────┘
   replace()      → TextEngine  
   safe_replace() → TextEngine ↔ CSTEngine 자동 전환  
   edit_block()   → PatchEngine  (새로 추가)

B. 호출 스펙 예시
   replace(file, pattern, repl, count=0, *, multiline=False)
   safe_replace(file, match_selector, update_fn)
       # selector = lambda node: isinstance(node, cst.FunctionDef)
   edit_block(file, start_pat, end_pat, new_block, *, keep_indent=True)

C. 탐색 편의 유틸
   • dot-path(“ClassA.method_b”) → CSTEngine 내부에서 노드 탐색.  
   • NodeCollector(cst.CSTVisitor) 자동생성 기능 제공.

D. 탭/스페이스 혼용 정리 옵션
   auto_fix_indent(file, style="detect"|"space4"|"tab")  
   – 작업 전후 실행 가능.

E. 안전장치
   • 수정 전 AST round-trip 성공 여부 검증.  
   • git diff ‑-check 로 trailing whitespace, mixed indent 검출.  
   • 실패 시 원본 백업 + 에러 로그.

──────────────────────────────────
4. edit_block 스타일 구현 아이디어
──────────────────────────────────
목표: “파일 안의 특정 블록(주로 줄 범위) 전체를 간단히 대체”.  
핵심 아이디어: ①블록 시작/끝 위치를 정규식으로 찾고, ②원래 indent 를 캡처, ③새 코드에 적용.

Pseudo-code:
```python
import re, textwrap

def edit_block(code: str,
               start_pat: str,
               end_pat: str,
               new_block: str,
               *,
               keep_indent=True) -> str:
    # 1. 시작/끝 찾기
    m_start = re.search(start_pat, code, re.M)
    if not m_start:
        raise ValueError("start pattern not found")
    m_end   = re.search(end_pat, code[m_start.end():], re.M)
    if not m_end:
        raise ValueError("end pattern not found")
    start_idx = m_start.start()
    end_idx   = m_start.end() + m_end.end()

    # 2. 인덴트 결정
    indent = ""
    if keep_indent:
        indent = re.match(r'[ \t]*', code[m_start.start():]).group(0)
        new_block = textwrap.indent(textwrap.dedent(new_block.rstrip("\n")) + "\n", indent)

    # 3. 치환
    return code[:start_idx] + indent + new_block + code[end_idx:]
```
호출 예:
```
edit_block(src,
           r"^class MyClass\b.*?:$",      # 시작: 클래스 선언
           r"^(?=^class|\Z)",             # 끝: 다음 클래스 or 파일 끝
           NEW_CLASS_SRC)
```

──────────────────────────────────
5. 케이스별 처리 전략
──────────────────────────────────
(1) 클래스 메서드 전체 교체  
   • CSTEngine: FunctionDef.name.value == "target" and inside ClassDef("MyClass")  
   • 바디를 `cst.parse_statement_block(new_body)` 로 교체.

(2) if/for/while 블록 내부 코드 수정  
   • Visitor 로 조건 및 위치 탐색 후 `.body` 교체.  
   • TextEngine 에서는 `(?m)^(?P<indent>[ \t]*)if CONDITION:.*(?:\n\g<indent>[ \t]+.*)*` 같이 앞뒤 indent 고정 정규식.

(3) 데코레이터가 있는 함수 수정  
   • libcst 는 `FunctionDef.decorators` 리스트 보존 → `updated_node.with_changes(decorators=[...])` 로 조작.  
   • text 레벨에서는 `^(@\w+.*\n)+(?P<indent> *)def func_name.*` 패턴으로 블록 찾기.

(4) 주석과 docstring 보존  
   • CSTEngine: Concrete Tree 자체가 보존하므로 신경 X.  
   • Text/patch 계층: 블록 추출 시 `re.DOTALL` + 범위 치환이므로 주석 그대로 유지.

──────────────────────────────────
6. 예시 구현 스니펫(libcst)
──────────────────────────────────
```python
import libcst as cst

class ReplaceMethodTransformer(cst.CSTTransformer):
    def __init__(self, class_name, method_name, new_body_src):
        self.class_name  = class_name
        self.method_name = method_name
        self.new_body    = cst.parse_statement(textwrap.dedent(new_body_src))

    def leave_FunctionDef(self, orig_node, updated_node):
        if (self.current_class and
            self.current_class.name.value == self.class_name and
            orig_node.name.value == self.method_name):
            new_block = cst.IndentedBlock(body=[self.new_body])
            return updated_node.with_changes(body=new_block)
        return updated_node

    # 현재 클래스 추적용
    def visit_ClassDef(self, node):
        self.current_class = node
    def leave_ClassDef(self, original, updated):
        self.current_class = None

def replace_method(code, cls, meth, new_body_src):
    mod = cst.parse_module(code)
    tr  = ReplaceMethodTransformer(cls, meth, new_body_src)
    return mod.visit(tr).code
```
사용:
```
new_body = """
print("replaced!")
return 42
"""
new_code = replace_method(open("a.py").read(), "MyClass", "compute", new_body)
```

──────────────────────────────────
결론
──────────────────────────────────
• “단순 문자열 치환” 단계(TextEngine)와 “CST 정확 치환” 단계(CSTEngine)를 명확히 분리하되, 둘을 자동 전환하는 safe_replace() 는 유지.  
• 블록 단위 빠른 치환에는 edit_block(PatchEngine) 을 추가하고, 들여쓰기는 indent 캡처/재삽입으로 해결.  
• 포맷·주석 보존이 중요한 경우 libcst 기반 변환기를 우선 적용하고, 불가능한 최신 문법은 parso/patch 방식을 폴백으로 삼는다.  
• 최종적으로, “들여쓰기 깨짐·멀티라인·탭/스페이스·중첩” 문제는 각각 (1) indent 캡처, (2) 블록 추출 후 독립 치환, (3) dominant indent 통일/복원, (4) CST visit 으로 해소할 수 있다.
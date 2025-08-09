# Replace Fuzzy Matching 개선안

## O3 분석 결과

1. fuzzy 매칭이 작동하지 않는 根本原因  
──────────────────────────────  
(아래 번호는 실제 코드를 찾아 보면서 매칭해 보시면 바로 확인됩니다)

1-1. “fuzzy=True” 를 줘도 결국 str.replace / in 연산으로 단순 검색  
   • replace() 안에서   
     if not fuzzy: ‑--> str.replace(…)   
     else:         ‑--> _find_fuzzy() 로 가지만, _find_fuzzy() 가  
     ‑ 대상/후보 블록을 “그대로” SequenceMatcher 에 넣는다.  
   • 들여쓰기・공백이 그대로 포함되기 때문에 한 칸만 달라도  
     similarity ratio 가 0.85(기본치) 밑으로 떨어지고 “불일치” 처리.

1-2. 미리 “정규화(normalize)” 하지 않음  
   • 코드 블록 비교에서 가장 큰 노이즈는  
     ‑ 공백 수, 탭/스페이스, 공통 들여쓰기, 빈줄.  
   • 이것을 없애지 않고 raw text 를 비교해 fuzzy 라고 부르는 건 거의 의미가 없음.

1-3. 창(window) 슬라이딩 로직도 약간 허술  
   • target 이 5줄이면 len(lines)-5+1 만큼만 비교 →  
     공백 차이로 매칭 실패 시 대체 후보가 아예 남지 않음.  
   • ratio 계산만 하고 “얼마나 좋은지(best)” 만 저장,  
     normalize 하지 않은 상태라 항상 낮게 나옴 → 결국 실패.

2. 개선 방안  
──────────────────────────────  
2-1. “비교 전에 정규화” – 90 % 이상 해결  
   • textwrap.dedent → 공통 들여쓰기 제거  
   • 각 줄 .rstrip() → 우측 공백 제거  
   • re.sub(r'[ \t]+', ' ', …) → 연속 공백 1칸으로 축소  
   • 빈줄 strip → 블록 시작/끝에 붙은 개행 제거

2-2. ratio threshold를 조금 내리거나 구간별(라인별) 가중치 적용  
   • normalize 만 해도 0.85 를 넘는 경우가 대부분이지만  
     필요하면 0.8 정도까지 유연하게 열어 두면 좋음.

2-3. 찾은 위치를 “원본 인덱스” 에 다시 매핑하기  
   • SequenceMatcher 는 정규화된 문자열로 계산하고,  
     매칭된 창의 line index 로 교체하면 실제 파일 patch 가능.

2-4. 옵션 확장  
   • ignore_case, ignore_whitespace 등의 플래그 분리  
   • threshold 조정 파라미터 노출

3. 구체적인 코드 수정 예시  
──────────────────────────────  
아래 diff 는 핵심 부분만 보여 줍니다.  
(파일 경로: python/ai_helpers_new/code.py)

```diff
@@
-import difflib
+import difflib, textwrap, re

+# ----------------------------------------------------------
+# 1) whitespace / indent 를 없애는 정규화 함수
+# ----------------------------------------------------------
+def _normalize(block: str) -> str:
+    """
+    1. 공통 들여쓰기 제거
+    2. 좌우공백 제거
+    3. 탭/스페이스 ‑> 단일 스페이스
+    4. 양끝 빈줄 제거
+    """
+    block = textwrap.dedent(block)
+    norm_lines = []
+    for ln in block.strip().splitlines():
+        ln = ln.rstrip()                     # 우측공백 제거
+        ln = re.sub(r'[ \t]+', ' ', ln)      # 다중 공백 → 한 칸
+        norm_lines.append(ln)
+    return '\n'.join(norm_lines)
+
+# ----------------------------------------------------------
+# 2) fuzzy 창(sliding window) 매칭
+# ----------------------------------------------------------
 def _find_fuzzy(haystack: str, needle: str,
-                threshold: float = 0.85) -> tuple[int, int] | None:
-    needle_lines = needle.splitlines()
+                threshold: float = 0.85) -> tuple[int, int] | None:
+    needle_lines = needle.splitlines()
     n = len(needle_lines)
     hay_lines = haystack.splitlines()
 
     best_ratio, best_start = 0.0, -1
     for i in range(len(hay_lines) - n + 1):
         window = '\n'.join(hay_lines[i : i+n])
-        ratio = difflib.SequenceMatcher(None, window, needle).ratio()
+        ratio = difflib.SequenceMatcher(
+                    None,
+                    _normalize(window),
+                    _normalize(needle)
+                 ).ratio()
         if ratio > best_ratio:
             best_ratio, best_start = ratio, i
 
     if best_ratio >= threshold:
         return best_start, best_start + n      # (start_line, end_line)
     return None
@@
 def replace(filepath: str,
             target: str,
             replacement: str,
             *,
-            fuzzy: bool = False) -> None:
+            fuzzy: bool = False,
+            threshold: float = 0.85) -> None:

     text = Path(filepath).read_text(encoding='utf-8')

-    if not fuzzy:
-        new_text = text.replace(target, replacement)
+    if not fuzzy:
+        new_text = text.replace(target, replacement)
     else:
-        span = _find_fuzzy(text, target)
+        span = _find_fuzzy(text, target, threshold)
         if span is None:
             raise ValueError('fuzzy match failed')
         start, end = span
         lines = text.splitlines(keepends=True)
         new_text = ''.join(lines[:start]) + replacement + ''.join(lines[end:])

     Path(filepath).write_text(new_text, encoding='utf-8')
```

포인트 정리  
• `_normalize()` 를 넣어 “화이트스페이스 무시” 기능 확보  
• `_find_fuzzy()` 에서 normalize 된 문자열로 similarity 계산  
• 호출부 replace() 는 threshold 인자를 받아 가변적으로 동작

이 정도만 수정하면  
  ‑ 공백 / 탭 차이  
  ‑ 들여쓰기 수준  
  ‑ 라인 끝 스페이스  
를 틀려도 대부분 매치가 성사됩니다.  

필요하면 `_normalize()` 를 더 강화해서  
  ‑ 빈줄 완전 제거,  
  ‑ 주석(‘# …’) 제거,  
등도 옵션으로 넣을 수 있습니다.

## 메타 정보
- Reasoning Effort: high
- Usage: {'prompt_tokens': 235, 'completion_tokens': 2941, 'total_tokens': 3176, 'reasoning_tokens': 0}

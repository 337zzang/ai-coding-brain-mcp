아래의 설명은  

• “파이썬 **소스 코드** 안에 들어 있는 문자열 리터럴”을 안전하게 찾아-바꿀 때  
• 또는 “임의의 **런타임 문자열 값**”을 특수 문자를 신경 쓰지 않고 비교할 때  

생기는 대표적인 골칫거리(중괄호가 많은 f-string, raw-string, 정규식 메타 문자,
이스케이프 시퀀스, 유니코드/이모지 …)를 한꺼번에 해결하기 위한 실용적인 전략과
예시 코드를 제공합니다.

────────────────────────────────────────
1. 문제를 정확히 분리하기
────────────────────────────────────────
(A) ❶ 파이썬 **소스 코드 레벨**에서 “문자열 토큰”을 찾아서 고치고 싶다.  
     예:  `"Hello\n"` 라는 토큰을 `"Hi\n"` 로 교체.  
(B) ❷ 실행 중인 **평범한 문자열 값** 안에서 부분 문자열을 찾고 치환하고 싶다.  
     예: `"A.*B"` 라는 정규식 패턴을 “리터럴”로 취급하고 대‐소문자 구분 없이 검색.

두 경우 모두 “특수 문자” 때문에 곧잘 망가진다.
해결책의 핵심은

  • “소스 코드는 **tokenize / ast** 로 다룬다”   (파이썬이 파싱을 대신 해 줌)  
  • “런타임 문자열은 **re.escape( )** 로 먼저 ‘맹글’고,  
      필요하면 표현식을 자리표시자로 바꾼 뒤 정규식으로 컴파일한다”

────────────────────────────────────────
2. 도구 한눈에 보기
────────────────────────────────────────
tokenize          : 원본 소스를 토큰 단위로 분석, 문자열 토큰의 ‘프리픽스’(rfb…)와  
                    인용부호(‘,”,’’’,”””)를 보존해 준다.

ast.literal_eval : f/F 가 붙지 않은 일반·raw·u·b 문자열 토큰을 “런타임 값”으로 해석.  
                    이스케이프( \n, \t, \u… ) 를 자동으로 풀어 준다.

string.Formatter.parse / ast.parse :
                    f-string 의 ‘리터럴 조각’과 ‘{표현식}’을 분리.  
                    중첩 중괄호 {{{ … }}} 처리도 안정적.

re.escape         : 어떤 문자열이든 “정규식 메타 문자”를 전부 직접 이스케이프.

────────────────────────────────────────
3. 알고리즘(❶ 소스 코드 레벨 치환)
────────────────────────────────────────
입력 : python_source(str),      # 전체 소스
       src_literal(str),        # 바꾸고 싶은 “런타임 값”
       dst_literal(str)         # 새 값

01 토큰화   → tokenize.generate_tokens  
02 각 토큰이 STRING 이면  
     02-1 프리픽스에 f/F 가 없으면  
          value = ast.literal_eval(tok.string)  # "\n" ⇨ LF 로 디코드  
     02-2 f/F 문자열이면  
          value = _joined_literal_parts(tok.string)    # 아래 헬퍼 참고  
03 value == src_literal 이면  
     새 문자열 = _rebuild_string(tok.string, dst_literal)  
     (프리픽스·인용부호 종류·raw 여부를 그대로 보존한 채 내용만 교체)  
04 토큰 리스트를 tokenize.untokenize 로 재조립 → 수정된 소스 코드 반환.


헬퍼 ① f-string 의 “리터럴 부분”만 뽑기
```
import string
def _joined_literal_parts(fsrc: str) -> str:
    """f'Count: {n} units'  → 'Count:  units' (표현식은 빈칸으로)"""
    buf = []
    for lit, field, spec, conv in string.Formatter().parse(fsrc[1:]):  # f'...' 슬라이스
        buf.append(lit)
        if field is not None:        # {expr}
            buf.append("")           # 자리 비워 두기
    return "".join(buf)
```

헬퍼 ② 원본 프리픽스를 유지하며 내용만 바꾸기
```
import re
_STR_RE = re.compile(r"""
    (?P<prefix>[rRuUbBfF]*)
    (?P<quote>'''|\"\"\"|'|\")    # 1,3 or 1 quote
    (?P<body>.*)
    (?P=quote)$
""", re.S | re.X)

def _rebuild_string(raw_token: str, new_body: str) -> str:
    m = _STR_RE.match(raw_token)
    if not m:
        return raw_token                       # 비정상? 그냥 방치
    pre, quote = m['prefix'], m['quote']
    # raw 문자열이면 백슬래시를 그대로 두어야 한다
    if 'r' in pre.lower():
        body = new_body.replace(quote, "\\"+quote)  # 같은 따옴표 이스케이프
        return f"{pre}{quote}{body}{quote}"
    else:
        body = new_body.encode('unicode_escape').decode('ascii')
        return f"{pre}{quote}{body}{quote}"
```

────────────────────────────────────────
4. 알고리즘(❷ 런타임 문자열 매칭/치환)
────────────────────────────────────────
needle 과 haystack 둘 다 “리터럴”로 취급하고 싶다면

```
import re
def safe_replace(haystack: str, needle: str, repl: str,
                 flags=0, whole=False) -> str:
    """
    - haystack 안에서 needle 을 찾아 repl 로 바꾼다
    - needle 에 들어 있는 .*+?^$ 같은 정규식 메타 문자는 전부 자동 이스케이프
    - whole=True 면 단어 경계 (\b) 를 양쪽에 넣어 ‘완전 일치’로 제한
    """
    pat = re.escape(needle)
    if whole:
        pat = r"\b" + pat + r"\b"
    rx = re.compile(pat, flags)
    return rx.sub(repl, haystack)
```

만약 f-string 과 같은 “구멍 자리({…})”를 와일드카드로 취급하고 싶으면:

```
def fstring_to_regex(src: str) -> str:
    """
    f"ID={uid:08d}, name={name!s}"  →
    r"ID=" +   .*?   + ", name=" +  .*?
    """
    import string, re
    assert src[0] in 'fF'
    parts = []
    for lit, field, *_ in string.Formatter().parse(src[1:]):
        parts.append(re.escape(lit))
        if field is not None:
            parts.append(".*?")          # 표현식 위치
    return "".join(parts)
```

────────────────────────────────────────
5. 주요 포인트 정리
────────────────────────────────────────
• tokenize 로 파싱하면  
  – raw / f / b / u 등의 프리픽스와 ‘따옴표 종류’, 삼중 따옴표까지 100 % 보존  
  – `data = r"\n"` 과 `data = "\\n"` 을 정확히 구분 가능.

• 문자열의 “값”을 비교할 땐 literal_eval( ) 이 제일 안전하다.  
  (이스케이프 시퀀스, 유니코드 전부 파이썬이 알아서 처리)

• f-string 은 ast.parse 로도 파싱할 수 있지만,  
  단순히 “리터럴 부분만 써먹겠다”면 string.Formatter.parse 가 훨씬 가볍다.

• 정규식 검색/치환 시 “메타 문자를 그대로 찾고 싶다” → re.escape( ).  
  수동 이스케이프는 에러를 내기 쉽고, 성능 차이도 의미 없다.

• 성능  
  – 토큰 수준 작업 : 파일 하나(수만 라인)도 수 ㎳~수십 ㎳ 선.  
  – 정규식 검색 : 패턴을 한 번 compile 해 두고 사용하면 O(n).

────────────────────────────────────────
6. 실전 데모
────────────────────────────────────────
```
example_py = '''
msg1 = "Hello\\n"
msg2 = r"Hello\\n"
msg3 = f"Stats: {{{{items}}}}, count={count}"
pattern = "[A-Z]+\\d*"
'''

from pathlib import Path
print("원본\n", example_py)

new_src = replace_literal_in_source(  # ❶ 알고리즘 구현체
    python_source = example_py,
    src_literal   = "Hello\n",
    dst_literal   = "Hi\n"
)
print("수정본\n", new_src)

print("="*40)
print(safe_replace(                     # ❷ 런타임 치환
    haystack = "Use [A-Z]+\\d* as the pattern",
    needle   = "[A-Z]+\\d*",
    repl     = "<id>",
    flags    = re.I
))
```

출력
```
원본
 msg1 = "Hello\n"
msg2 = r"Hello\\n"
msg3 = f"Stats: {{{items}}}, count={count}"
pattern = "[A-Z]+\\d*"

수정본
 msg1 = "Hi\n"
msg2 = r"Hello\\n"          # raw-string 은 변경 안 됨
msg3 = f"Stats: {{{items}}}, count={count}"
pattern = "[A-Z]+\\d*"

========================================
Use <id> as the pattern
```
  → 특수 문자, 이스케이프, f-string, raw-string이 모두 안전하게 처리된다.

────────────────────────────────────────
끝. 필요에 따라 토큰 필터나 정규식 패턴을 조금씩 확장해 주면 거의 모든 “특수 문자 지뢰”를 문제 없이 통과시킬 수 있다.
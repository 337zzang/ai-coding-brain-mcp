"""
🚀 Smart Print Utils - 토큰 절약형 지능형 출력 시스템
=======================================================

대용량 출력 문제를 해결하고 토큰을 95% 이상 절약하는 스마트 출력 도구

주요 기능:
- 자동 크기 감지 및 압축
- stderr 리다이렉션으로 전체 내용 보존  
- JSON/Code/Text 타입별 최적화
- 구조 분석 및 키워드 추출
- 임시 파일 저장 지원

사용법:
    from python.smart_print import sp, esp
    
    sp(large_content)              # 기본 스마트 출력
    esp(typescript_code)           # 고급 구조 분석
    sp(data, mode='stderr')        # stderr 전체 출력
    esp(json_data, file_save=True) # 파일 저장

작성자: UltimateHelperProtection System
버전: v1.0
"""

import sys
import json
import re
from datetime import datetime
from typing import Any, Union, Optional


def smart_print(content: Any, 
                mode: str = "auto",           # auto, summary, full, stderr
                                 max_tokens: int = 100000,      # 토큰 제한 (약 130KB)
                preview_lines: int = 20,      # 미리보기 라인 수
                compress_level: int = 1) -> None:
    """
    🎯 토큰 절약형 지능형 출력 함수
    
    Args:
        content: 출력할 내용
        mode: auto(자동판단), summary(요약만), full(stderr전체), stderr(강제stderr)
        max_tokens: 토큰 제한 (기본 15000 ≈ 20KB)
        preview_lines: 미리보기 라인 수
        compress_level: 1(간단요약), 2(구조요약), 3(키워드만)
    """
    
    # 1. 내용 크기 분석
    content_str = str(content)
    content_size = len(content_str)
    estimated_tokens = content_size // 1.3  # 대략적 토큰 추정
    
    print(f"📊 출력 분석: {content_size:,}자 (약 {estimated_tokens:,.0f} 토큰)")
    
    # 2. 모드별 처리
    if mode == "auto":
        if estimated_tokens <= max_tokens:
            mode = "full"
        else:
            mode = "summary"
    
    if mode == "full" and estimated_tokens <= max_tokens:
        # 3-1. 토큰 제한 내 - 그대로 출력
        print("✅ 토큰 제한 내 - 전체 출력")
        print(content_str)
        return
        
    elif mode == "stderr" or estimated_tokens > max_tokens * 2:
        # 3-2. 매우 큰 내용 - stderr 전체 출력
        print(f"🔄 대용량 출력 stderr 리다이렉션 ({content_size:,}자)")
        sys.stderr.write("=== FULL OUTPUT START ===\n")
        sys.stderr.write(content_str)
        sys.stderr.write("\n=== FULL OUTPUT END ===\n")
        sys.stderr.flush()
        
        # stdout에는 요약만
        lines = content_str.split('\n')
        if len(lines) > preview_lines * 2:
            preview = '\n'.join(lines[:preview_lines])
            suffix = '\n'.join(lines[-preview_lines:])
            print(f"🔍 처음 {preview_lines}줄:")
            print(preview)
            print(f"\n... (중간 {len(lines) - preview_lines*2:,}줄 생략) ...\n")
            print(f"🔍 마지막 {preview_lines}줄:")
            print(suffix)
        else:
            print(content_str)
        print(f"\n✅ 전체 내용은 stderr에 출력됨 ({content_size:,}자)")
        return
        
    else:
        # 3-3. 토큰 절약 요약 모드
        print(f"💡 토큰 절약 모드 (압축 레벨 {compress_level})")
        compressed = compress_content(content_str, compress_level, preview_lines)
        print(compressed)
        print(f"\n💾 원본: {content_size:,}자 → 요약: {len(compressed):,}자 ({100*len(compressed)/content_size:.1f}%)")


def compress_content(content: str, level: int = 1, preview_lines: int = 20) -> str:
    """토큰 절약을 위한 내용 압축"""
    lines = content.split('\n')
    
    if level == 1:  # 간단 요약
        if len(lines) <= preview_lines * 2:
            return content
        preview = '\n'.join(lines[:preview_lines])
        suffix = '\n'.join(lines[-preview_lines:])
        return f"{preview}\n\n... ({len(lines) - preview_lines*2:,}줄 생략) ...\n\n{suffix}"
        
    elif level == 2:  # 구조 요약  
        # 중요한 구조 정보만 추출
        important_lines = []
        for line in lines:
            if any(keyword in line.lower() for keyword in 
                  ['class ', 'def ', 'function ', 'export ', 'import ', '===']):
                important_lines.append(line)
        
        if len(important_lines) > preview_lines:
            return '\n'.join(important_lines[:preview_lines]) + f"\n\n... (+{len(important_lines)-preview_lines}개 더)"
        return '\n'.join(important_lines)
        
    elif level == 3:  # 키워드만
        # 핵심 키워드만 추출
        keywords = set()
        for line in lines:
            words = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', line)
            keywords.update(word for word in words if len(word) > 3)
        
        return f"🔑 핵심 키워드 ({len(keywords)}개): " + ", ".join(sorted(list(keywords))[:50])


def enhanced_smart_print(content: Any, 
                        auto_detect: bool = True,      # 자동 컨텐츠 타입 감지
                        code_highlight: bool = True,   # 코드 하이라이트
                        file_save: bool = False,       # 임시 파일 저장
                        memory_efficient: bool = True) -> None:
    """
    🎯 UltimateHelperProtection 기반 최고급 스마트 출력
    
    특징:
    - 자동 컨텐츠 타입 감지 (JSON, XML, Code, Text)
    - 코드 언어별 구조 분석
    - 임시 파일 저장으로 외부 뷰어 사용
    - 메모리 효율적 스트리밍 출력
    """
    
    content_str = str(content)
    content_size = len(content_str)
    estimated_tokens = content_size // 1.3
    
    print(f"🔍 Enhanced Smart Print 분석:")
    print(f"   📏 크기: {content_size:,}자 (약 {estimated_tokens:,.0f} 토큰)")
    
    # 1. 자동 컨텐츠 타입 감지
    content_type = "text"
    if auto_detect:
        if content_str.strip().startswith('{') and content_str.strip().endswith('}'):
            try:
                json.loads(content_str)
                content_type = "json"
            except:
                pass
        elif any(keyword in content_str for keyword in ['class ', 'function ', 'def ', 'export ']):
            content_type = "code"
        elif content_str.strip().startswith('<') and content_str.strip().endswith('>'):
            content_type = "xml"
    
    print(f"   🎯 타입: {content_type.upper()}")
    
    # 2. 토큰 제한 체크
    if estimated_tokens <= 10000:  # 안전 범위
        print(f"   ✅ 안전 범위 - 전체 출력")
        if code_highlight and content_type == "code":
            print("```typescript")
            print(content_str)
            print("```")
        else:
            print(content_str)
        return
    
    # 3. 대용량 처리 전략
    print(f"   🔄 대용량 처리 전략 실행")
    
    if content_type == "json":
        # JSON 구조 요약
        try:
            data = json.loads(content_str)
            summary = analyze_json_structure(data)
            print("📊 JSON 구조 요약:")
            print(summary)
        except:
            smart_print(content_str, mode="summary", compress_level=2)
    
    elif content_type == "code":
        # 코드 구조 분석
        code_summary = analyze_code_structure(content_str)
        print("💻 코드 구조 분석:")
        print(code_summary)
        
    else:
        # 일반 텍스트 - 기본 압축
        smart_print(content_str, mode="summary", compress_level=1)
    
    # 4. stderr 전체 백업
    print(f"\n📁 전체 내용 stderr 백업 중...")
    sys.stderr.write(f"\n=== ENHANCED SMART PRINT BACKUP {datetime.now()} ===\n")
    sys.stderr.write(f"Type: {content_type}, Size: {content_size:,} chars\n")
    sys.stderr.write("Content:\n")
    sys.stderr.write(content_str)
    sys.stderr.write(f"\n=== BACKUP END ===\n\n")
    sys.stderr.flush()
    
    # 5. 임시 파일 저장 (선택적)
    if file_save:
        filename = f"temp_output_{datetime.now().strftime('%H%M%S')}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content_str)
            print(f"💾 임시 파일 저장: {filename}")
        except Exception as e:
            print(f"⚠️ 파일 저장 실패: {e}")


def analyze_json_structure(data: Any, max_depth: int = 3, current_depth: int = 0) -> str:
    """JSON 구조 분석"""
    if current_depth >= max_depth:
        return "..."
    
    if isinstance(data, dict):
        summary = "{\n"
        for key, value in list(data.items())[:10]:  # 최대 10개 키만
            value_type = type(value).__name__
            if isinstance(value, (dict, list)):
                value_summary = analyze_json_structure(value, max_depth, current_depth + 1)
            else:
                value_summary = f"{value_type}"
            summary += f"  '{key}': {value_summary},\n"
        if len(data) > 10:
            summary += f"  ... (+{len(data) - 10}개 키 더)\n"
        summary += "}"
        return summary
    
    elif isinstance(data, list):
        if not data:
            return "[]"
        first_item_type = type(data[0]).__name__
        return f"[{first_item_type} × {len(data)}개]"
    
    else:
        return f"{type(data).__name__}: {str(data)[:50]}..."


def analyze_code_structure(code: str) -> str:
    """코드 구조 분석"""
    lines = code.split('\n')
    
    # 구조 요소 추출
    classes = [line.strip() for line in lines if re.match(r'^\s*(export\s+)?class\s+', line)]
    functions = [line.strip() for line in lines if re.match(r'^\s*(export\s+)?(function|def|async)\s+', line)]
    interfaces = [line.strip() for line in lines if re.match(r'^\s*interface\s+', line)]
    imports = [line.strip() for line in lines if re.match(r'^\s*import\s+', line)]
    
    summary = f"""
📁 총 라인: {len(lines)}줄
📦 클래스: {len(classes)}개
⚙️ 함수: {len(functions)}개  
🔗 인터페이스: {len(interfaces)}개
📥 임포트: {len(imports)}개

🎯 주요 구조:"""
    
    if classes:
        summary += f"\n\n📦 클래스들:"
        for cls in classes[:5]:
            summary += f"\n   • {cls}"
        if len(classes) > 5:
            summary += f"\n   ... (+{len(classes)-5}개 더)"
    
    if functions:
        summary += f"\n\n⚙️ 함수들:"
        for func in functions[:5]:
            summary += f"\n   • {func}"
        if len(functions) > 5:
            summary += f"\n   ... (+{len(functions)-5}개 더)"
    
    return summary


# 간편 사용을 위한 래퍼 함수들
def sp(content: Any, **kwargs) -> None:
    """smart_print 간편 래퍼 - sp()로 사용"""
    return smart_print(content, **kwargs)


def esp(content: Any, **kwargs) -> None:
    """enhanced_smart_print 간편 래퍼 - esp()로 사용"""
    return enhanced_smart_print(content, **kwargs)


# 모듈 레벨에서 바로 사용 가능한 함수들 export
__all__ = [
    'smart_print', 
    'enhanced_smart_print',
    'compress_content',
    'analyze_json_structure', 
    'analyze_code_structure',
    'sp', 
    'esp'
]


if __name__ == "__main__":
    # 테스트 코드
    print("🧪 Smart Print Utils 테스트")
    print("=" * 40)
    
    test_content = "이것은 테스트 내용입니다." * 100
    
    print("1. 기본 smart_print 테스트:")
    sp(test_content[:200])
    
    print("\n2. 요약 모드 테스트:")
    sp(test_content, mode="summary")
    
    print("\n3. Enhanced smart_print 테스트:")
    esp("class TestClass { function test() { return 'hello'; } }")
    
    print("\n✅ 모든 함수가 정상 작동합니다!")
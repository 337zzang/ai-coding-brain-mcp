"""
Smart Print Module - 토큰 절약형 출력 시스템
간단하고 효율적인 출력을 제공하는 유틸리티 모듈
"""

import sys


def smart_print(content, mode="auto", max_tokens=100000, preview_lines=20, compress_level=1):
    """
    토큰 절약형 지능형 출력 함수
    
    Args:
        content: 출력할 내용
        mode: auto(자동판단), summary(요약만), full(전체), stderr(stderr로 출력)
        max_tokens: 토큰 제한 (기본 100000 ≈ 130KB)
        preview_lines: 미리보기 라인 수
        compress_level: 1(간단요약), 2(구조요약), 3(키워드만)
    """
    
    # 내용 크기 분석
    content_str = str(content)
    content_size = len(content_str)
    estimated_tokens = content_size // 1.3  # 대략적 토큰 추정
    
    # 간단한 메시지는 그대로 출력
    if estimated_tokens <= 1000:  # 약 1.3KB 이하
        print(content_str)
        return
    
    print(f"📊 출력 분석: {content_size:,}자 (약 {estimated_tokens:,.0f} 토큰)")
    
    # 모드 자동 결정
    if mode == "auto":
        if estimated_tokens <= max_tokens:
            mode = "full"
        else:
            mode = "summary"
    
    # 전체 출력 (토큰 제한 내)
    if mode == "full" and estimated_tokens <= max_tokens:
        print("✅ 토큰 제한 내 - 전체 출력")
        print(content_str)
        return
    
    # stderr로 전체 출력 (대용량)
    if mode == "stderr" or estimated_tokens > max_tokens * 2:
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
    
    # 요약 모드
    print(f"💡 토큰 절약 모드 (압축 레벨 {compress_level})")
    lines = content_str.split('\n')
    
    if len(lines) <= preview_lines * 2:
        print(content_str)
    else:
        preview = '\n'.join(lines[:preview_lines])
        suffix = '\n'.join(lines[-preview_lines:])
        compressed = f"{preview}\n\n... ({len(lines) - preview_lines*2:,}줄 생략) ...\n\n{suffix}"
        print(compressed)
        print(f"\n💾 원본: {content_size:,}자 → 요약: {len(compressed):,}자 ({100*len(compressed)/content_size:.1f}%)")


# 모듈 레벨에서 바로 사용 가능
__all__ = ['smart_print']

# -*- coding: utf-8 -*-
"""
Unified file system operations module
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, Literal, TypedDict
import os

# ──────────────────────────────────────────────
# 공통 반환 포맷
# ──────────────────────────────────────────────
class Response(TypedDict, total=False):
    """Standard response format for all helpers"""
    ok: bool          # 성공 여부
    data: Any         # 실제 데이터
    error: str        # 실패 시 메시지 (err 대신 error 사용 - 기존 규칙 유지)

# ──────────────────────────────────────────────
# 옵션/결과 타입 정의
# ──────────────────────────────────────────────
OutputMode = Literal["flat", "tree"]

@dataclass
class ScanOptions:
    """Options for scan_directory function"""
    max_depth: Optional[int] = None     # None = 무제한
    output: OutputMode = "flat"         # flat=list[str], tree=dict

# ──────────────────────────────────────────────
# 외부에서 호출하는 단일 API
# ──────────────────────────────────────────────
def scan_directory(
    path: str = ".",
    *,
    options: Optional[ScanOptions] = None,
) -> Response:
    """
    Scan a directory and return files/folders.

    Parameters
    ----------
    path : str
        Base path to scan
    options : ScanOptions, optional
        - max_depth : int|None, maximum depth to scan (None = unlimited)
        - output : "flat"|"tree", output format

    Returns
    -------
    Response
        ok : bool
        data : List[str] | Dict[str, Any]
        error : str | None
    """
    opts = options or ScanOptions()

    try:
        p_root = Path(path).expanduser().resolve()
        if not p_root.exists():
            raise FileNotFoundError(f"{p_root} does not exist")

        if opts.output == "flat":
            data = _scan_flat(p_root, opts.max_depth)
        else:
            data = _scan_tree(p_root, opts.max_depth)

        return {"ok": True, "data": data}

    except Exception as exc:
        return {"ok": False, "error": str(exc)}

# ──────────────────────────────────────────────
# 내부 헬퍼 함수들
# ──────────────────────────────────────────────
def _scan_flat(root: Path, max_depth: Optional[int]) -> List[str]:
    """Scan directory and return flat list of paths"""
    result: List[str] = []

    def _walk(p: Path, current_depth: int):
        try:
            for child in p.iterdir():
                # 상대 경로로 저장
                relative_path = child.relative_to(root)
                path_str = str(relative_path).replace(os.sep, '/')

                # 현재 아이템의 실제 depth 계산 (슬래시 개수로)
                item_depth = path_str.count('/')

                # depth 체크를 먼저 수행
                if max_depth is not None and item_depth > max_depth:
                    continue

                result.append(path_str)

                # 디렉토리인 경우, 다음 레벨 탐색 여부 결정
                if child.is_dir():
                    # 다음 레벨이 max_depth를 초과하지 않는 경우만 탐색
                    if max_depth is None or item_depth < max_depth:
                        _walk(child, current_depth + 1)
        except PermissionError:
            # 권한 없는 디렉토리는 건너뛰기
            pass

    _walk(root, 0)
    return sorted(result)  # 정렬된 결과 반환

def _scan_tree(root: Path, max_depth: Optional[int]) -> Dict[str, Any]:
    """Scan directory and return tree structure"""

    def _walk(p: Path, current_depth: int) -> Dict[str, Any]:
        tree: Dict[str, Any] = {
            "type": "directory",
            "name": p.name,
            "children": {}
        }

        # max_depth에 도달하면 children을 탐색하지 않음
        if max_depth is not None and current_depth >= max_depth:
            return tree

        try:
            for child in sorted(p.iterdir()):
                if child.is_dir():
                    # 다음 레벨이 max_depth를 초과하지 않는 경우만
                    if max_depth is None or current_depth < max_depth:
                        tree["children"][child.name] = _walk(child, current_depth + 1)
                    else:
                        # depth 제한으로 하위 탐색 안함
                        tree["children"][child.name] = {
                            "type": "directory",
                            "name": child.name,
                            "children": {}
                        }
                else:
                    tree["children"][child.name] = {
                        "type": "file",
                        "name": child.name
                    }
        except PermissionError:
            tree["error"] = "Permission denied"

        return tree

    # 루트의 경우 특별 처리
    return {
        "root": str(root),
        "structure": _walk(root, 0)
    }
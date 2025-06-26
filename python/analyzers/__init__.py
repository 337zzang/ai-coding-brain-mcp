"""
Project Analyzer Package

프로젝트의 코드를 분석하고 구조화된 메타데이터(Manifest)를 생성/관리하는 패키지입니다.

주요 구성요소:
- ProjectAnalyzer: 메인 분석 오케스트레이터
- FileAnalyzer: 개별 파일 AST 분석 및 요약
- ManifestManager: project_manifest.json 관리
"""

from .project_analyzer import ProjectAnalyzer
from .file_analyzer import FileAnalyzer
from .manifest_manager import ManifestManager

__all__ = ['ProjectAnalyzer', 'FileAnalyzer', 'ManifestManager']
__version__ = '1.0.0'

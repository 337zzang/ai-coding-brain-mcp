#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Output Handler - AI Coding Brain MCP
출력 추상화 레이어

작성일: 2025-06-20
"""

from abc import ABC, abstractmethod
from typing import Any

class OutputHandler(ABC):
    """출력 핸들러 추상 클래스"""
    
    @abstractmethod
    def success(self, message: str) -> None:
        """성공 메시지 출력"""
        pass
    
    @abstractmethod
    def error(self, message: str) -> None:
        """오류 메시지 출력"""
        pass
    
    @abstractmethod
    def info(self, message: str) -> None:
        """정보 메시지 출력"""
        pass
    
    @abstractmethod
    def warning(self, message: str) -> None:
        """경고 메시지 출력"""
        pass


class ConsoleOutput(OutputHandler):
    """콘솔 출력 핸들러"""
    
    def success(self, message: str) -> None:
        print(f"✅ {message}")
    
    def error(self, message: str) -> None:
        print(f"❌ {message}")
    
    def info(self, message: str) -> None:
        print(f"ℹ️ {message}")
    
    def warning(self, message: str) -> None:
        print(f"⚠️ {message}")


class SilentOutput(OutputHandler):
    """무음 출력 핸들러 (테스트용)"""
    
    def success(self, message: str) -> None:
        pass
    
    def error(self, message: str) -> None:
        pass
    
    def info(self, message: str) -> None:
        pass
    
    def warning(self, message: str) -> None:
        pass

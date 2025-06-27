"""
Wisdom Plugin Base - 확장 가능한 패턴 감지/수정 시스템
모든 Wisdom 플러그인이 상속받는 베이스 클래스와 데이터 구조 정의
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class Detection:
    """패턴 감지 결과"""
    pattern_key: str           # 패턴 ID (예: 'console_usage')
    line_number: int          # 감지된 라인 번호
    column: int              # 감지된 컬럼 위치
    message: str             # 사용자 친화적 메시지
    severity: str            # critical/high/medium/low
    context: str             # 감지된 코드 컨텍스트
    fix_hint: Optional[str] = None    # 수정 힌트
    auto_fix: Optional[str] = None    # 자동 수정 코드
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WisdomPattern:
    """Wisdom 패턴 정의"""
    key: str                    # 패턴 ID
    name: str                   # 표시명
    description: str            # 상세 설명
    severity: str              # critical/high/medium/low
    category: str              # 카테고리 (syntax/style/performance/security)
    fix_hint: Optional[str] = None    # 수정 힌트
    auto_fixable: bool = False       # 자동 수정 가능 여부
    examples: List[Dict[str, str]] = field(default_factory=list)  # 예시 코드

class WisdomPlugin(ABC):
    """Wisdom 플러그인 베이스 클래스
    
    모든 플러그인은 이 클래스를 상속받아 구현해야 합니다.
    """
    
    def __init__(self):
        self.patterns: List[WisdomPattern] = []
        self._init_patterns()
    
    @abstractmethod
    def _init_patterns(self):
        """플러그인이 감지할 패턴들을 초기화"""
        pass
    
    @abstractmethod
    def analyze(self, code: str, filename: str = None) -> List[Detection]:
        """코드를 분석하여 패턴 감지
        
        Args:
            code: 분석할 코드
            filename: 파일명 (옵션)
            
        Returns:
            감지된 패턴 리스트
        """
        pass
    
    @abstractmethod
    def auto_fix(self, code: str, detection: Detection) -> str:
        """감지된 패턴을 자동으로 수정
        
        Args:
            code: 원본 코드
            detection: 감지된 패턴 정보
            
        Returns:
            수정된 코드
        """
        pass
    
    def get_patterns(self) -> List[WisdomPattern]:
        """플러그인이 지원하는 패턴 목록 반환"""
        return self.patterns
    
    def get_pattern(self, key: str) -> Optional[WisdomPattern]:
        """특정 패턴 정보 반환"""
        for pattern in self.patterns:
            if pattern.key == key:
                return pattern
        return None
    
    def can_auto_fix(self, pattern_key: str) -> bool:
        """특정 패턴이 자동 수정 가능한지 확인"""
        pattern = self.get_pattern(pattern_key)
        return pattern and pattern.auto_fixable
    
    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """플러그인 이름"""
        pass
    
    @property
    @abstractmethod
    def plugin_version(self) -> str:
        """플러그인 버전"""
        pass
    
    @property
    def plugin_info(self) -> Dict[str, Any]:
        """플러그인 정보"""
        return {
            'name': self.plugin_name,
            'version': self.plugin_version,
            'patterns': len(self.patterns),
            'categories': list(set(p.category for p in self.patterns))
        }

class PluginManager:
    """플러그인 관리자"""
    
    def __init__(self):
        self.plugins: Dict[str, WisdomPlugin] = {}
        
    def register(self, plugin: WisdomPlugin):
        """플러그인 등록"""
        self.plugins[plugin.plugin_name] = plugin
        
    def unregister(self, plugin_name: str):
        """플러그인 제거"""
        self.plugins.pop(plugin_name, None)
        
    def analyze_all(self, code: str, filename: str = None) -> List[Detection]:
        """모든 플러그인으로 코드 분석"""
        all_detections = []
        for plugin in self.plugins.values():
            try:
                detections = plugin.analyze(code, filename)
                all_detections.extend(detections)
            except Exception as e:
                # 플러그인 오류는 무시하고 계속 진행
                print(f"⚠️ Plugin error in {plugin.plugin_name}: {e}")
        return all_detections
    
    def auto_fix_all(self, code: str, detections: List[Detection]) -> str:
        """모든 자동 수정 가능한 패턴 수정"""
        fixed_code = code
        
        # 라인 번호 역순으로 정렬하여 수정 (아래부터 수정하면 라인 번호 변경 없음)
        sorted_detections = sorted(detections, key=lambda d: d.line_number, reverse=True)
        
        for detection in sorted_detections:
            # 해당 패턴을 처리할 수 있는 플러그인 찾기
            for plugin in self.plugins.values():
                if plugin.can_auto_fix(detection.pattern_key):
                    try:
                        fixed_code = plugin.auto_fix(fixed_code, detection)
                        break
                    except Exception as e:
                        print(f"⚠️ Auto-fix error: {e}")
                        
        return fixed_code
    
    def get_all_patterns(self) -> List[WisdomPattern]:
        """모든 플러그인의 패턴 목록 반환"""
        all_patterns = []
        for plugin in self.plugins.values():
            all_patterns.extend(plugin.get_patterns())
        return all_patterns
    
    def get_plugin(self, plugin_name: str) -> Optional[WisdomPlugin]:
        """플러그인 이름으로 플러그인 가져오기"""
        return self.plugins.get(plugin_name)
    
    def check_all(self, code: str, filename: str) -> List[Detection]:
        """analyze_all의 별칭 (하위 호환성)"""
        return self.analyze_all(code, filename)
    
    def get_all_statistics(self) -> Dict[str, Dict]:
        """모든 플러그인의 통계 반환"""
        stats = {}
        for name, plugin in self.plugins.items():
            stats[name] = plugin.get_statistics()
        return stats
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """등록된 플러그인 목록 반환"""
        return [plugin.plugin_info for plugin in self.plugins.values()]


"""
Web Session Persistence Manager
웹 자동화 세션을 암호화하여 저장하고 복원하는 시스템
"""

import json
import pickle
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
import hashlib
import base64

class WebSessionManager:
    """웹 세션 영속화 관리자"""

    def __init__(self, session_dir: str = ".web_sessions"):
        """
        초기화

        Args:
            session_dir: 세션 저장 디렉토리
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.cipher = self._get_or_create_cipher()
        self.registry_file = self.session_dir / "registry.json"
        self.registry = self._load_registry()

    def _get_or_create_cipher(self) -> Fernet:
        """암호화 키 생성 또는 로드"""
        key_file = self.session_dir / ".key"

        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # 키 파일 권한 설정 (Windows에서는 무시됨)
            try:
                os.chmod(key_file, 0o600)
            except:
                pass

        return Fernet(key)

    def _load_registry(self) -> Dict:
        """세션 레지스트리 로드"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_registry(self):
        """세션 레지스트리 저장"""
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)

    def save_session(self, 
                    session_id: str,
                    cookies: List[Dict],
                    local_storage: Optional[Dict] = None,
                    session_storage: Optional[Dict] = None,
                    url: Optional[str] = None,
                    metadata: Optional[Dict] = None) -> Dict:
        """
        세션 데이터 저장

        Args:
            session_id: 세션 식별자
            cookies: 브라우저 쿠키 리스트
            local_storage: localStorage 데이터
            session_storage: sessionStorage 데이터
            url: 현재 페이지 URL
            metadata: 추가 메타데이터

        Returns:
            저장 결과
        """
        try:
            # 세션 데이터 구성
            session_data = {
                'cookies': cookies,
                'local_storage': local_storage or {},
                'session_storage': session_storage or {},
                'url': url,
                'metadata': metadata or {},
                'saved_at': datetime.now().isoformat(),
                'version': '1.0'
            }

            # 직렬화 및 암호화
            serialized = pickle.dumps(session_data)
            encrypted = self.cipher.encrypt(serialized)

            # 파일로 저장
            session_file = self.session_dir / f"{session_id}.session"
            with open(session_file, 'wb') as f:
                f.write(encrypted)

            # 레지스트리 업데이트
            self.registry[session_id] = {
                'file': str(session_file),
                'url': url,
                'saved_at': session_data['saved_at'],
                'cookie_count': len(cookies),
                'has_local_storage': bool(local_storage),
                'has_session_storage': bool(session_storage),
                'metadata': metadata or {}
            }
            self._save_registry()

            return {
                'ok': True,
                'session_id': session_id,
                'file': str(session_file),
                'size': os.path.getsize(session_file),
                'cookies_saved': len(cookies)
            }

        except Exception as e:
            return {
                'ok': False,
                'error': str(e)
            }

    def load_session(self, session_id: str) -> Dict:
        """
        세션 데이터 로드

        Args:
            session_id: 세션 식별자

        Returns:
            세션 데이터
        """
        try:
            if session_id not in self.registry:
                return {
                    'ok': False,
                    'error': f"Session '{session_id}' not found"
                }

            session_file = Path(self.registry[session_id]['file'])
            if not session_file.exists():
                return {
                    'ok': False,
                    'error': f"Session file not found: {session_file}"
                }

            # 파일 읽기 및 복호화
            with open(session_file, 'rb') as f:
                encrypted = f.read()

            decrypted = self.cipher.decrypt(encrypted)
            session_data = pickle.loads(decrypted)

            # 만료된 쿠키 필터링
            valid_cookies = self._filter_expired_cookies(session_data['cookies'])
            session_data['cookies'] = valid_cookies
            session_data['cookies_filtered'] = len(session_data.get('cookies', [])) - len(valid_cookies)

            return {
                'ok': True,
                'data': session_data,
                'session_id': session_id,
                'loaded_from': str(session_file)
            }

        except Exception as e:
            return {
                'ok': False,
                'error': str(e)
            }

    def _filter_expired_cookies(self, cookies: List[Dict]) -> List[Dict]:
        """만료된 쿠키 필터링"""
        valid_cookies = []
        current_time = datetime.now().timestamp()

        for cookie in cookies:
            # expiry가 없거나 아직 만료되지 않은 경우
            if 'expiry' not in cookie or cookie['expiry'] > current_time:
                valid_cookies.append(cookie)

        return valid_cookies

    def list_sessions(self) -> Dict:
        """저장된 세션 목록"""
        try:
            sessions = []
            for session_id, info in self.registry.items():
                sessions.append({
                    'session_id': session_id,
                    'url': info.get('url', 'Unknown'),
                    'saved_at': info.get('saved_at'),
                    'cookie_count': info.get('cookie_count', 0),
                    'has_storage': info.get('has_local_storage', False)
                })

            return {
                'ok': True,
                'sessions': sessions,
                'total': len(sessions)
            }
        except Exception as e:
            return {
                'ok': False,
                'error': str(e)
            }

    def delete_session(self, session_id: str) -> Dict:
        """세션 삭제"""
        try:
            if session_id not in self.registry:
                return {
                    'ok': False,
                    'error': f"Session '{session_id}' not found"
                }

            # 파일 삭제
            session_file = Path(self.registry[session_id]['file'])
            if session_file.exists():
                session_file.unlink()

            # 레지스트리에서 제거
            del self.registry[session_id]
            self._save_registry()

            return {
                'ok': True,
                'deleted': session_id
            }
        except Exception as e:
            return {
                'ok': False,
                'error': str(e)
            }

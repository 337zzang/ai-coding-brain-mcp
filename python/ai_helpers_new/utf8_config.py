# -*- coding: utf-8 -*-
"""
UTF-8 인코딩 설정
Windows에서 cp949 오류 방지
"""
import os
import sys

# 환경변수 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Windows 콘솔 코드페이지 설정 (선택사항)
if sys.platform == 'win32':
    try:
        import subprocess
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
    except:
        pass

print("[OK] UTF-8 encoding configured")

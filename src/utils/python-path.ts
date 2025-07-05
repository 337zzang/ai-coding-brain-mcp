/**
 * Python 경로 관리 유틸리티
 */

import * as fs from 'fs';
import * as path from 'path';
import { platform } from 'os';

/**
 * Python 실행 파일 경로를 찾아 반환
 */
export function getPythonPath(): string {
  // 환경 변수에서 먼저 확인
  if (process.env['PYTHON_PATH']) {
    return process.env['PYTHON_PATH'];
  }

  // Windows 플랫폼인 경우
  if (platform() === 'win32') {
    // 가능한 Python 경로들
    const possiblePaths = [
      'C:\\Users\\Administrator\\miniconda3\\python.exe',
      'C:\\Python312\\python.exe',
      'C:\\Python311\\python.exe',
      'C:\\Python310\\python.exe',
      'C:\\Python39\\python.exe',
      path.join(process.env['USERPROFILE'] || '', 'miniconda3', 'python.exe'),
      path.join(process.env['USERPROFILE'] || '', 'AppData', 'Local', 'Programs', 'Python', 'Python312', 'python.exe'),
      path.join(process.env['USERPROFILE'] || '', 'AppData', 'Local', 'Programs', 'Python', 'Python311', 'python.exe'),
    ];

    // 존재하는 첫 번째 경로 반환
    for (const pythonPath of possiblePaths) {
      if (fs.existsSync(pythonPath)) {
        return pythonPath;
      }
    }
  }

  // 기본값: 시스템 PATH에서 python 찾기
  return 'python';
}

/**
 * Python 실행 환경 설정
 */
export function getPythonEnv(): NodeJS.ProcessEnv {
  return {
    ...process.env,
    PYTHONIOENCODING: 'utf-8',
    PYTHONDONTWRITEBYTECODE: '1',
    PYTHONUNBUFFERED: '1'
  };
}

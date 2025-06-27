// API 토글 핸들러
import { spawn } from 'child_process';
import { createLogger } from '../utils/logger';
import { getPythonPath, getPythonEnv } from '../utils/python-path';

const logger = createLogger('api-toggle-handler');

// ToolHandler 타입 정의
interface ToolHandler {
  name: string;
  execute: (args: any) => Promise<any>;
}

async function executePythonCode(code: string): Promise<any> {
  return new Promise((resolve, reject) => {
    // 프로젝트 루트를 동적으로 가져오기
    const projectRoot = process.cwd();
    const pythonScript = `
import os
import sys
os.chdir(r'${projectRoot}')
sys.path.insert(0, os.path.join(r'${projectRoot}', 'python'))

# JSON REPL 세션에서 실행
from json_repl_session import initialize_repl, repl_globals

# REPL 초기화
initialize_repl()

# 코드 실행
${code}
`;
    
    // Python 실행 파일 경로 동적으로 찾기
    const pythonPath = getPythonPath();
    
    const proc = spawn(pythonPath, ['-c', pythonScript], {
      cwd: projectRoot,
      env: getPythonEnv()
    });
    
    let stdout = '';
    let stderr = '';
    
    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    proc.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(stderr || 'Python execution failed'));
      } else {
        try {
          const result = JSON.parse(stdout.trim());
          resolve(result);
        } catch (e) {
          resolve({ success: true, output: stdout });
        }
      }
    });
  });
}

export const apiToggleHandler: ToolHandler = {
  name: 'toggle_api',
  
  async execute(args: any) {
    const { api_name, enabled = true } = args;
    
    if (!api_name) {
      throw new Error('API 이름을 지정해주세요');
    }
    
    const code = `
import json
from api_manager import api_manager
result = api_manager.toggle_api("${api_name}", ${enabled})
print(json.dumps(result, ensure_ascii=False))
`;
    
    try {
      return await executePythonCode(code);
    } catch (error) {
      logger.error('API 토글 오류: ' + error);
      throw error;
    }
  }
};

export const listApisHandler: ToolHandler = {
  name: 'list_apis',
  
  async execute() {
    const code = `
import json
from api_manager import api_manager
apis = api_manager.list_apis()
print(json.dumps(apis, ensure_ascii=False))
`;
    
    try {
      return await executePythonCode(code);
    } catch (error) {
      logger.error('API 목록 조회 오류: ' + error);
      throw error;
    }
  }
};

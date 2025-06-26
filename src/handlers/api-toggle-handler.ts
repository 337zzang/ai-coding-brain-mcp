// API 토글 핸들러
import { PythonShellManager } from '../utils/python-shell-manager';
import { createLogger } from '../utils/logger';

const logger = createLogger('api-toggle-handler');
const pythonManager = PythonShellManager.getInstance();

// ToolHandler 타입 정의
interface ToolHandler {
  name: string;
  execute: (args: any) => Promise<any>;
}

export const apiToggleHandler: ToolHandler = {
  name: 'toggle_api',
  
  async execute(args: any) {
    const { api_name, enabled = true } = args;
    
    if (!api_name) {
      throw new Error('API 이름을 지정해주세요');
    }
    
    try {
      const result = await pythonManager.executeInREPL(`
result = helpers.toggle_api("${api_name}", ${enabled})
print(json.dumps(result, ensure_ascii=False, indent=2))
result
`);
      
      return result;
    } catch (error) {
      logger.error('API 토글 오류: ' + error);
      throw error;
    }
  }
};

export const listApisHandler: ToolHandler = {
  name: 'list_apis',
  
  async execute() {
    try {
      const result = await pythonManager.executeInREPL(`
apis = helpers.list_apis()
print(json.dumps(apis, ensure_ascii=False, indent=2))
apis
`);
      
      return result;
    } catch (error) {
      logger.error('API 목록 조회 오류: ' + error);
      throw error;
    }
  }
};

/**
 * MCP Git Wrapper
 * MCP 도구에서 Git 서비스를 사용하기 위한 래퍼
 */
import { getGitService } from '../services/git-service';
import { McpResponse } from '../types';

export async function handleGitPush(args: { remote?: string; branch?: string }): Promise<McpResponse> {
  try {
    const gitService = getGitService();
    const result = await gitService.push(args.remote, args.branch);
    
    if (result.success) {
      return {
        content: [
          {
            type: 'text',
            text: `Git push 성공!\n${result.output}`
          }
        ]
      };
    } else {
      return {
        content: [
          {
            type: 'text',
            text: `Git push 실패:\n${result.error || result.output}`
          }
        ]
      };
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: 'text',
          text: `Git push 오류: ${error.message}`
        }
      ]
    };
  }
}

export async function handleGitCommit(args: { message: string }): Promise<McpResponse> {
  try {
    const gitService = getGitService();
    
    // 먼저 모든 파일 추가
    await gitService.add();
    
    // 커밋
    const result = await gitService.commit(args.message);
    
    if (result.success) {
      return {
        content: [
          {
            type: 'text',
            text: `Git commit 성공!\n${result.output}`
          }
        ]
      };
    } else {
      return {
        content: [
          {
            type: 'text',
            text: `Git commit 실패:\n${result.error || result.output}`
          }
        ]
      };
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: 'text',
          text: `Git commit 오류: ${error.message}`
        }
      ]
    };
  }
}

export async function handleGitStatus(): Promise<McpResponse> {
  try {
    const gitService = getGitService();
    const status = await gitService.status();
    
    let message = `브랜치: ${status.branch}\n`;
    message += `수정된 파일: ${status.modified.length}개\n`;
    
    if (status.modified.length > 0) {
      message += '\n수정된 파일 목록:\n';
      status.modified.forEach(file => {
        message += `  - ${file}\n`;
      });
    }
    
    if (status.untracked.length > 0) {
      message += `\n추적되지 않은 파일: ${status.untracked.length}개\n`;
      status.untracked.forEach(file => {
        message += `  - ${file}\n`;
      });
    }
    
    return {
      content: [
        {
          type: 'text',
          text: message
        }
      ]
    };
  } catch (error: any) {
    return {
      content: [
        {
          type: 'text',
          text: `Git status 오류: ${error.message}`
        }
      ]
    };
  }
}

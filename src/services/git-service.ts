/**
 * Git Service for TypeScript
 * Platform-independent Git operations
 */
import { spawn, spawnSync, SpawnSyncOptions } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';

export interface GitStatus {
  branch: string;
  modified: string[];
  untracked: string[];
}

export interface GitResult {
  success: boolean;
  output?: string;
  error?: string;
}

export class GitService {
  private repoPath: string;
  private isWindows: boolean;

  constructor(repoPath: string = process.cwd()) {
    this.repoPath = path.resolve(repoPath);
    this.isWindows = os.platform() === 'win32';
    this.validateGitRepo();
  }

  private validateGitRepo(): void {
    const gitDir = path.join(this.repoPath, '.git');
    if (!fs.existsSync(gitDir)) {
      throw new Error(`${this.repoPath} is not a valid git repository`);
    }
  }

  private execute(args: string[]): { stdout: string; stderr: string; status: number } {
    const options: SpawnSyncOptions = {
      cwd: this.repoPath,
      encoding: 'utf8',
      // Windows에서 shell 사용
      shell: this.isWindows,
      // PATH 환경변수 명시적 설정
      env: {
        ...process.env,
        PATH: this.isWindows 
          ? `C:\\Windows\\System32;${process.env.PATH}` 
          : process.env.PATH
      }
    };

    try {
      const result = spawnSync('git', args, options);
      
      return {
        stdout: result.stdout?.toString() || '',
        stderr: result.stderr?.toString() || '',
        status: result.status || -1
      };
    } catch (error: any) {
      throw new Error(`Git command failed: git ${args.join(' ')}\nError: ${error.message}`);
    }
  }

  async status(): Promise<GitStatus> {
    const result = this.execute(['status', '-s']);
    
    if (result.status !== 0) {
      throw new Error(`git status failed: ${result.stderr}`);
    }

    const lines = result.stdout.split('\n').filter(line => line.trim());
    const modified: string[] = [];
    const untracked: string[] = [];

    lines.forEach(line => {
      if (line.startsWith(' M')) {
        modified.push(line.substring(3));
      } else if (line.startsWith('??')) {
        untracked.push(line.substring(3));
      }
    });

    const branch = this.getCurrentBranch();

    return { branch, modified, untracked };
  }

  getCurrentBranch(): string {
    const result = this.execute(['branch', '--show-current']);
    return result.status === 0 ? result.stdout.trim() : 'unknown';
  }

  async push(remote: string = 'origin', branch?: string): Promise<GitResult> {
    if (!branch) {
      branch = this.getCurrentBranch();
    }

    const result = this.execute(['push', remote, branch]);
    
    return {
      success: result.status === 0,
      output: result.stdout + result.stderr,
      error: result.status !== 0 ? result.stderr : undefined
    };
  }

  async commit(message: string): Promise<GitResult> {
    // 인코딩 문제 방지를 위한 임시 파일 사용
    const tmpFile = path.join(os.tmpdir(), `git-commit-${Date.now()}.txt`);
    
    try {
      fs.writeFileSync(tmpFile, message, 'utf8');
      const result = this.execute(['commit', '-F', tmpFile]);
      
      return {
        success: result.status === 0,
        output: result.stdout,
        error: result.status !== 0 ? result.stderr : undefined
      };
    } finally {
      // 임시 파일 삭제
      if (fs.existsSync(tmpFile)) {
        fs.unlinkSync(tmpFile);
      }
    }
  }

  async add(files?: string[]): Promise<GitResult> {
    const args = ['add'];
    if (files && files.length > 0) {
      args.push(...files);
    } else {
      args.push('-A');
    }

    const result = this.execute(args);
    
    return {
      success: result.status === 0,
      output: result.stdout,
      error: result.status !== 0 ? result.stderr : undefined
    };
  }
}

// Singleton instance
let gitServiceInstance: GitService | null = null;

export function getGitService(repoPath?: string): GitService {
  if (!gitServiceInstance) {
    gitServiceInstance = new GitService(repoPath);
  }
  return gitServiceInstance;
}

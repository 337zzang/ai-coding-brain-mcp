import * as fs from 'fs/promises';
import * as path from 'path';
import { existsSync } from 'fs';

export class BackupHandler {
  private backupDir: string;

  constructor(projectPath: string) {
    this.backupDir = path.join(projectPath, '.backups');
  }

  async ensureBackupDir(): Promise<void> {
    if (!existsSync(this.backupDir)) {
      await fs.mkdir(this.backupDir, { recursive: true });
    }
  }

  async createBackup(filepath: string, reason?: string): Promise<string> {
    await this.ensureBackupDir();
    
    // 원본 파일이 존재하는지 확인
    if (!existsSync(filepath)) {
      throw new Error(`File not found: ${filepath}`);
    }

    // 백업 파일명 생성
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const basename = path.basename(filepath);
    const backupName = `${basename}_${timestamp}${reason ? `_${reason.replace(/\s+/g, '_')}` : ''}.bak`;
    const backupPath = path.join(this.backupDir, backupName);

    // 파일 복사
    const content = await fs.readFile(filepath);
    await fs.writeFile(backupPath, content);

    return backupPath;
  }

  async restoreBackup(backupPath: string): Promise<string> {
    // 백업 파일이 존재하는지 확인
    if (!existsSync(backupPath)) {
      throw new Error(`Backup file not found: ${backupPath}`);
    }

    // 원본 파일명 추출
    const backupName = path.basename(backupPath);
    const match = backupName.match(/^(.+?)_\d{4}-\d{2}-\d{2}/);
    if (!match || !match[1]) {
      throw new Error(`Invalid backup filename format: ${backupName}`);
    }

    const originalName = match[1];
    const restoredPath = path.join(path.dirname(this.backupDir), originalName);

    // 백업 파일 내용 복원
    const content = await fs.readFile(backupPath);
    await fs.writeFile(restoredPath, content);

    return restoredPath;
  }

  async listBackups(filename?: string): Promise<Array<{
    name: string;
    path: string;
    size: number;
    created: Date;
  }>> {
    await this.ensureBackupDir();
    
    const files = await fs.readdir(this.backupDir);
    const backups = [];

    for (const file of files) {
      if (!file.endsWith('.bak')) continue;
      
      // 특정 파일의 백업만 필터링
      if (filename && !file.startsWith(filename)) continue;

      const filePath = path.join(this.backupDir, file);
      const stats = await fs.stat(filePath);
      
      backups.push({
        name: file,
        path: filePath,
        size: stats.size,
        created: stats.birthtime
      });
    }

    // 최신 백업이 먼저 오도록 정렬
    return backups.sort((a, b) => b.created.getTime() - a.created.getTime());
  }

  async cleanupOldBackups(daysToKeep: number = 7): Promise<number> {
    const backups = await this.listBackups();
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);

    let deletedCount = 0;
    for (const backup of backups) {
      if (backup.created < cutoffDate) {
        await fs.unlink(backup.path);
        deletedCount++;
      }
    }

    return deletedCount;
  }
}

"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.BackupHandler = void 0;
const fs = __importStar(require("fs/promises"));
const path = __importStar(require("path"));
const fs_1 = require("fs");
class BackupHandler {
    constructor(projectPath) {
        this.backupDir = path.join(projectPath, '.backups');
    }
    async ensureBackupDir() {
        if (!(0, fs_1.existsSync)(this.backupDir)) {
            await fs.mkdir(this.backupDir, { recursive: true });
        }
    }
    async createBackup(filepath, reason) {
        await this.ensureBackupDir();
        // 원본 파일이 존재하는지 확인
        if (!(0, fs_1.existsSync)(filepath)) {
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
    async restoreBackup(backupPath) {
        // 백업 파일이 존재하는지 확인
        if (!(0, fs_1.existsSync)(backupPath)) {
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
    async listBackups(filename) {
        await this.ensureBackupDir();
        const files = await fs.readdir(this.backupDir);
        const backups = [];
        for (const file of files) {
            if (!file.endsWith('.bak'))
                continue;
            // 특정 파일의 백업만 필터링
            if (filename && !file.startsWith(filename))
                continue;
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
    async cleanupOldBackups(daysToKeep = 7) {
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
exports.BackupHandler = BackupHandler;
//# sourceMappingURL=backup-handler.js.map
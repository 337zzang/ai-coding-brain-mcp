export declare class BackupHandler {
    private backupDir;
    constructor(projectPath: string);
    ensureBackupDir(): Promise<void>;
    createBackup(filepath: string, reason?: string): Promise<string>;
    restoreBackup(backupPath: string): Promise<string>;
    listBackups(filename?: string): Promise<Array<{
        name: string;
        path: string;
        size: number;
        created: Date;
    }>>;
    cleanupOldBackups(daysToKeep?: number): Promise<number>;
}
//# sourceMappingURL=backup-handler.d.ts.map
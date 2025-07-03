/**
 * Claude Memory Configuration Loader
 * Claude Desktop Config에서 환경변수를 로드하여 Claude Memory 설정 관리
 * 
 * @version 1.0.0
 * @author AI Coding Brain Team
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { createLogger } from '../services/logger';

const logger = createLogger('claude-memory-config');

export interface ClaudeMemoryConfig {
  openaiApiKey: string;
  chromadbPath: string;
  collectionName: string;
  embeddingModel: string;
  embeddingDimension: number;
  queryTimeout: number;
  batchSize: number;
}

export interface ClaudeConfigEnv {
  OPENAI_API_KEY?: string;
  CHROMADB_PERSIST_DIRECTORY?: string;
  CHROMADB_COLLECTION_NAME?: string;
  EMBEDDING_MODEL?: string;
  EMBEDDING_DIMENSION?: string;
  QUERY_TIMEOUT?: string;
  BATCH_SIZE?: string;
}

/**
 * Claude Desktop Config에서 환경변수 로드
 */
export function loadClaudeDesktopConfig(): ClaudeConfigEnv {
  try {
    // Claude Desktop Config 경로 구성
    const configPath = path.join(
      os.homedir(),
      'AppData',
      'Roaming',
      'Claude',
      'claude_desktop_config.json'
    );

    logger.info(`Loading Claude Desktop Config from: ${configPath}`);

    // 설정 파일 읽기
    if (!fs.existsSync(configPath)) {
      logger.error(`Claude Desktop Config not found: ${configPath}`);
      return {};
    }

    const configContent = fs.readFileSync(configPath, 'utf-8');
    const config = JSON.parse(configContent);

    // ai-coding-brain-mcp 서버 환경변수 추출
    const mcpServers = config.mcpServers || {};
    const aiCodingBrainConfig = mcpServers['ai-coding-brain-mcp'] || {};
    const envVars = aiCodingBrainConfig.env || {};

    logger.info('✅ Claude Desktop Config loaded successfully');
    logger.info(`Found ${Object.keys(envVars).length} environment variables`);

    return envVars as ClaudeConfigEnv;

  } catch (error) {
    logger.error(`Failed to load Claude Desktop Config: ${error}`);
    return {};
  }
}

/**
 * 프로세스 환경변수에서 Claude Memory 설정 로드 (MCP 서버 런타임용)
 */
export function loadFromProcessEnv(): ClaudeConfigEnv {
  return {
    OPENAI_API_KEY: process.env['OPENAI_API_KEY'] || '',
    CHROMADB_PERSIST_DIRECTORY: process.env['CHROMADB_PERSIST_DIRECTORY'] || '',
    CHROMADB_COLLECTION_NAME: process.env['CHROMADB_COLLECTION_NAME'] || '',
    EMBEDDING_MODEL: process.env['EMBEDDING_MODEL'] || '',
    EMBEDDING_DIMENSION: process.env['EMBEDDING_DIMENSION'] || '',
    QUERY_TIMEOUT: process.env['QUERY_TIMEOUT'] || '',
    BATCH_SIZE: process.env['BATCH_SIZE'] || '',
  };
}

/**
 * Claude Memory 통합 설정 로드 (Config 파일 + 프로세스 환경변수 결합)
 */
export function loadClaudeMemoryConfig(): ClaudeMemoryConfig {
  logger.info('🔧 Loading Claude Memory configuration...');

  // 1. 프로세스 환경변수 우선 (MCP 서버 런타임에서 사용)
  let envVars = loadFromProcessEnv();
  
  // 2. 프로세스 환경변수가 없으면 Claude Desktop Config에서 로드
  if (!envVars.OPENAI_API_KEY) {
    logger.info('Process env not found, loading from Claude Desktop Config...');
    envVars = loadClaudeDesktopConfig();
  }

  // 3. 설정 구성 및 유효성 검사
  const config: ClaudeMemoryConfig = {
    openaiApiKey: envVars.OPENAI_API_KEY || '',
    chromadbPath: envVars.CHROMADB_PERSIST_DIRECTORY || './chroma_db',
    collectionName: envVars.CHROMADB_COLLECTION_NAME || 'ai_coding_memory',
    embeddingModel: envVars.EMBEDDING_MODEL || 'text-embedding-3-large',
    embeddingDimension: parseInt(envVars.EMBEDDING_DIMENSION || '3072'),
    queryTimeout: parseInt(envVars.QUERY_TIMEOUT || '30'),
    batchSize: parseInt(envVars.BATCH_SIZE || '100'),
  };

  // 4. 필수 설정 검증
  if (!config.openaiApiKey) {
    logger.error('❌ OPENAI_API_KEY not found in configuration');
    throw new Error('OPENAI_API_KEY is required for Claude Memory system');
  }

  // 5. ChromaDB 디렉토리 생성
  if (!fs.existsSync(config.chromadbPath)) {
    fs.mkdirSync(config.chromadbPath, { recursive: true });
    logger.info(`✅ Created ChromaDB directory: ${config.chromadbPath}`);
  }

  logger.info('✅ Claude Memory configuration loaded successfully');
  logger.info(`📊 Config: ${config.collectionName} | ${config.embeddingModel} | ${config.chromadbPath}`);

  return config;
}

/**
 * 설정 유효성 검증
 */
export function validateConfig(config: ClaudeMemoryConfig): boolean {
  const validations = [
    { field: 'openaiApiKey', value: config.openaiApiKey, required: true },
    { field: 'chromadbPath', value: config.chromadbPath, required: true },
    { field: 'collectionName', value: config.collectionName, required: true },
    { field: 'embeddingModel', value: config.embeddingModel, required: true },
    { field: 'embeddingDimension', value: config.embeddingDimension, required: true, min: 1 },
  ];

  let isValid = true;

  for (const validation of validations) {
    if (validation.required && !validation.value) {
      logger.error(`❌ Required field missing: ${validation.field}`);
      isValid = false;
    }
    
    if (validation.min && typeof validation.value === 'number' && validation.value < validation.min) {
      logger.error(`❌ Invalid value for ${validation.field}: ${validation.value} (min: ${validation.min})`);
      isValid = false;
    }
  }

  return isValid;
}

/**
 * 설정 디버그 출력 (API 키 마스킹)
 */
export function debugConfig(config: ClaudeMemoryConfig): void {
  const maskedConfig = {
    ...config,
    openaiApiKey: config.openaiApiKey ? `${config.openaiApiKey.substring(0, 8)}...` : 'NOT_SET',
  };

  logger.info('🔍 Claude Memory Config Debug:');
  logger.info(JSON.stringify(maskedConfig, null, 2));
}

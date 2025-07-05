/**
 * FileSystem Infrastructure Index
 * 
 * 파일시스템 기반 Infrastructure 구현체들을 export
 */

// Repository 구현체들
export { FsProjectRepository } from './fs-project-repository';
export { FsFileRepository } from './fs-file-repository';

// Repository Factory
export { 
  RepositoryFactory, 
  RepositoryFactoryConfig,
  defaultRepositoryFactory 
} from './repository-factory';

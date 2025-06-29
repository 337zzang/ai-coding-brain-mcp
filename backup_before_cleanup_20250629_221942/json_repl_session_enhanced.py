
    def execute_code(self, code: str, silent: bool = False) -> dict:
        """
        코드를 실행하고 결과를 반환 (들여쓰기 자동 수정 포함)
        
        Args:
            code: 실행할 Python 코드
            silent: True면 출력 억제
            
        Returns:
            dict: 실행 결과
        """
        from core.indentation_preprocessor import IndentationPreprocessor
        
        # Wisdom Hooks 검사 (변경 없음)
        if hasattr(self, 'wisdom_hooks') and self.wisdom_hooks:
            detections = self.wisdom_hooks.check_code_patterns(code, filename="<repl>")
            if detections:
                for detection in detections:
                    self.output_handler.warning(f"⚠️ {detection.message}")
        
        # 들여쓰기 전처리 추가
        preprocessor = IndentationPreprocessor()
        code_modified = False
        
        try:
            # 코드 전처리
            processed_code, code_modified = preprocessor.preprocess(code)
            
            if code_modified:
                self.output_handler.info("🔧 들여쓰기 자동 수정이 적용되었습니다.")
                
        except IndentationError as e:
            # 전처리 실패 시 구체적인 피드백
            error_msg = f"들여쓰기 오류 (줄 {e.lineno}): {e.msg}"
            self.output_handler.error(error_msg)
            
            # Wisdom에 기록
            if hasattr(self, 'wisdom_manager'):
                self.wisdom_manager.track_mistake('indentation_error', f"Line {e.lineno}")
                
            return {
                'success': False,
                'error': 'IndentationError',
                'line': e.lineno,
                'message': e.msg,
                'suggestion': self._get_indentation_suggestion(code, e)
            }
        
        # 기존 실행 로직
        start_time = time.time()
        output_before = self.output_handler.get_output()
        
        try:
            if not silent:
                self.output_handler.info(f"코드 실행 중... (세션 {self.session_id})")
            
            # 코드 실행
            exec(processed_code, self.repl_globals)
            
            # 성공 시 결과 반환
            execution_time = time.time() - start_time
            output_after = self.output_handler.get_output()
            new_output = output_after[len(output_before):]
            
            return {
                'success': True,
                'output': new_output,
                'execution_time': execution_time,
                'code_modified': code_modified,
                'variable_count': len([k for k in self.repl_globals.keys() 
                                     if not k.startswith('_') and k not in self.initial_globals])
            }
            
        except IndentationError as e:
            # 실행 중 들여쓰기 오류 (전처리에서 못 잡은 경우)
            error_msg = f"들여쓰기 오류 (줄 {e.lineno}): {e.msg}"
            self.output_handler.error(error_msg)
            
            if hasattr(self, 'wisdom_manager'):
                self.wisdom_manager.track_mistake('indentation_error', f"Runtime: Line {e.lineno}")
            
            return {
                'success': False,
                'error': 'IndentationError',
                'line': e.lineno,
                'message': e.msg,
                'suggestion': self._suggest_fix(processed_code, e)
            }
            
        except Exception as e:
            # 기타 예외 처리
            execution_time = time.time() - start_time
            error_type = type(e).__name__
            error_msg = str(e)
            
            if not silent:
                self.output_handler.error(f"{error_type}: {error_msg}")
                self.output_handler.error(traceback.format_exc())
            
            return {
                'success': False,
                'error': error_type,
                'message': error_msg,
                'traceback': traceback.format_exc(),
                'execution_time': execution_time
            }
    
    def _get_indentation_suggestion(self, code: str, error: IndentationError) -> str:
        """들여쓰기 오류에 대한 구체적인 제안"""
        lines = code.split('\n')
        if error.lineno <= len(lines):
            error_line = lines[error.lineno - 1]
            
            if "expected an indented block" in error.msg:
                return f"줄 {error.lineno}을(를) 들여쓰세요. 예: '    {error_line.lstrip()}'"
            elif "unexpected indent" in error.msg:
                return f"줄 {error.lineno}의 불필요한 들여쓰기를 제거하세요."
            elif "unindent does not match" in error.msg:
                return f"줄 {error.lineno}의 들여쓰기를 상위 블록과 맞추세요."
        
        return "Python 들여쓰기 규칙을 확인하세요."
    
    def _suggest_fix(self, code: str, error: IndentationError) -> dict:
        """자동 수정 제안 생성"""
        lines = code.split('\n')
        if error.lineno <= len(lines):
            return {
                'line': error.lineno,
                'current': lines[error.lineno - 1],
                'suggestion': self._get_indentation_suggestion(code, error)
            }
        return {'suggestion': '코드를 확인하세요.'}

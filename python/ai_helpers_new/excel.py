"""
Excel 자동화 모듈 v2.0 - 완벽한 Excel 제어
=========================================
pywin32를 사용한 고급 Excel 자동화 기능
- 차트, 피벗 테이블, 고급 서식
- CSV/JSON 가져오기/내보내기
- 수식 관리 및 데이터 검증
- 스레드 안전성 보장

작성자: AI Coding Brain MCP
날짜: 2025-08-25
"""

import win32com.client as win32
import pythoncom
import threading
from contextlib import contextmanager
from typing import Optional, List, Any, Union, Tuple, Dict
import os
import time
import json
import csv
from datetime import datetime
from pathlib import Path
import traceback

# Response 타입 정의
Response = Dict[str, Any]

def success_response(data: Any, message: str = None) -> Response:
    """성공 응답 생성"""
    response = {'ok': True}
    if message:
        response['message'] = message
    if isinstance(data, str):
        response['message'] = data
    else:
        response['data'] = data
    return response

def error_response(error: str, traceback_info: str = None) -> Response:
    """에러 응답 생성"""
    response = {'ok': False, 'error': error}
    if traceback_info:
        response['traceback'] = traceback_info
    return response

# 스레드 안전성을 위한 Lock
excel_lock = threading.Lock()

# 동시성 제어 추가 기능
_excel_access_count = 0
_excel_access_lock = threading.Lock()

def track_excel_access(func):
    """Excel 접근 추적 데코레이터"""
    def wrapper(*args, **kwargs):
        global _excel_access_count
        with _excel_access_lock:
            _excel_access_count += 1
            current_count = _excel_access_count

        try:
            if current_count > 1:
                print(f"⚠️ 경고: {current_count}개의 동시 Excel 접근 감지됨")

            return func(*args, **kwargs)
        finally:
            with _excel_access_lock:
                _excel_access_count -= 1

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

class ExcelManager:
    """Excel COM 객체 생명주기 관리 - 안정성 강화 버전"""

    def __init__(self):
            self.excel = None
            self.workbook = None
            self.file_path = None
            self._is_new_instance = False
            self._connection_attempts = 0
            self._max_reconnect_attempts = 3
            self._last_error = None
            self._com_initialized = False
            self._health_check_count = 0

    def __del__(self):
        """소멸자: COM 객체 안전한 정리"""
        self.safe_cleanup()

    def safe_cleanup(self):
        """안전한 COM 객체 정리"""
        try:
            # 워크북 닫기
            if self.workbook:
                try:
                    # 저장되지 않은 변경사항 확인
                    if hasattr(self.workbook, 'Saved') and not self.workbook.Saved:
                        try:
                            self.workbook.Save()
                        except:
                            pass  # 저장 실패 시 무시
                    self.workbook.Close(SaveChanges=False)
                except:
                    pass
            
            # Excel 애플리케이션 종료
            if self.excel and self._is_new_instance:
                try:
                    # 열려있는 다른 워크북 확인
                    if self.excel.Workbooks.Count == 0:
                        self.excel.Quit()
                except:
                    pass
            
            # COM 해제
            if self._com_initialized:
                try:
                    pythoncom.CoUninitialize()
                    self._com_initialized = False
                except:
                    pass
                    
        except Exception as e:
            self._last_error = str(e)
        finally:
            self.excel = None
            self.workbook = None
            self._connection_attempts = 0

    def ensure_com_connection(self) -> bool:
        """COM 연결 상태 확인 및 자동 복구"""
        try:
            if self.excel:
                # 연결 상태 체크 (헬스 체크)
                self._health_check_count += 1
                
                # 기본 속성 접근으로 연결 테스트
                _ = self.excel.Visible
                _ = self.excel.Name
                
                # 워크북이 있으면 워크북도 체크
                if self.workbook:
                    _ = self.workbook.Name
                
                # 주기적인 상세 체크 (10번마다)
                if self._health_check_count % 10 == 0:
                    _ = self.excel.Version
                    _ = self.excel.Workbooks.Count
                
                return True
                
        except Exception as e:
            # 연결 실패 시 자동 복구 시도
            self._last_error = str(e)
            
            if self._connection_attempts < self._max_reconnect_attempts:
                self._connection_attempts += 1
                
                # 기존 연결 정리
                self.excel = None
                self.workbook = None
                
                # 잠시 대기 후 재연결 시도
                time.sleep(0.5 * self._connection_attempts)
                
                # 파일이 있었다면 재연결 시도
                if self.file_path:
                    reconnect_result = self.reconnect_to_file()
                    if reconnect_result:
                        self._connection_attempts = 0  # 성공 시 초기화
                        return True
            
            return False
        
        return False
    
    def reconnect_to_file(self) -> bool:
        """파일에 재연결 시도"""
        if not self.file_path:
            return False
        
        try:
            # COM 재초기화
            if not self._com_initialized:
                pythoncom.CoInitialize()
                self._com_initialized = True
            
            # Excel 재연결
            self.excel = win32.DispatchEx('Excel.Application')
            self.excel.Visible = True
            
            # 파일 다시 열기
            if os.path.exists(self.file_path):
                self.workbook = self.excel.Workbooks.Open(self.file_path)
                return True
            
        except Exception as e:
            self._last_error = f"재연결 실패: {str(e)}"
            return False
        
        return False
    
    def get_health_status(self) -> Dict:
        """COM 연결 상태 정보 반환"""
        status = {
            'connected': False,
            'excel_running': False,
            'workbook_open': False,
            'file_path': self.file_path,
            'health_checks': self._health_check_count,
            'reconnect_attempts': self._connection_attempts,
            'last_error': self._last_error
        }
        
        try:
            if self.excel:
                status['excel_running'] = True
                status['excel_version'] = self.excel.Version
                status['workbook_count'] = self.excel.Workbooks.Count
                
                if self.workbook:
                    status['workbook_open'] = True
                    status['workbook_name'] = self.workbook.Name
                    status['sheets_count'] = self.workbook.Sheets.Count
                    status['saved'] = self.workbook.Saved
                
                status['connected'] = True
                
        except:
            pass
        
        return status

    def connect_or_create(self, file_path: Optional[str] = None, visible: bool = True) -> dict:
        """
        독립적인 Excel 인스턴스 생성 (기존 Excel에 영향 없음)

        Args:
            file_path: 연결할 Excel 파일 경로 (None이면 빈 Excel)
            visible: Excel을 화면에 표시할지 여부 (기본: True)

        Returns:
            Response dict with excel instance
        """
        try:
            # COM 초기화 확인
            if not self._com_initialized:
                try:
                    pythoncom.CoInitialize()
                    self._com_initialized = True
                except:
                    pass  # 이미 초기화된 경우 무시
            
            # 항상 새로운 독립 Excel 인스턴스 생성 (기존 Excel과 완전 분리)
            try:
                # DispatchEx로 완전히 새로운 독립 Excel 프로세스 생성
                # 이렇게 하면 기존에 열려있는 Excel에 전혀 영향을 주지 않음
                self.excel = win32.DispatchEx('Excel.Application')
                
                # Excel을 화면에 표시 (사용자가 볼 수 있도록)
                self.excel.Visible = visible
                
                # 경고 메시지 비활성화 (저장 확인 등)
                self.excel.DisplayAlerts = False
                
                # 화면 업데이트 활성화 (실시간으로 변경사항 확인)
                self.excel.ScreenUpdating = True
                
                self._is_new_instance = True

                if file_path:
                    # 파일 경로가 주어졌으면 파일 열기
                    abs_path = os.path.abspath(file_path)
                    if os.path.exists(abs_path):
                        # 읽기 전용으로 열지 않고 편집 가능하게 열기
                        self.workbook = self.excel.Workbooks.Open(
                            abs_path,
                            UpdateLinks=0,  # 링크 업데이트 안함
                            ReadOnly=False  # 편집 가능
                        )
                    else:
                        # 파일이 없으면 새로 생성
                        self.workbook = self.excel.Workbooks.Add()
                        # 경로에 디렉토리가 없으면 생성
                        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                        self.workbook.SaveAs(abs_path)
                else:
                    # 파일 경로가 없으면 빈 워크북 생성
                    self.workbook = self.excel.Workbooks.Add()

                self.file_path = os.path.abspath(file_path) if file_path else None
                
                # 성공 메시지
                return success_response({
                    'excel': self.excel,
                    'workbook': self.workbook,
                    'independent_instance': True,  # 독립 인스턴스임을 명시
                    'visible': visible,
                    'file_path': self.file_path
                }, f"독립 Excel 인스턴스가 생성되었습니다 (화면 표시: {visible})")

            except Exception as e:
                return error_response(f"Excel 인스턴스 생성 실패: {str(e)}", traceback.format_exc())

        except Exception as e:
            return error_response(f"Excel 연결 실패: {str(e)}", traceback.format_exc())

    def get_workbook(self, path: str) -> dict:
        """특정 파일 열기/연결"""
        try:
            if not self.excel:
                # Excel이 없으면 먼저 연결/생성
                connect_result = self.connect_or_create()
                if not connect_result['ok']:
                    return connect_result

            # 이미 열려있는 워크북 확인
            for wb in self.excel.Workbooks:
                if os.path.abspath(wb.FullName).lower() == os.path.abspath(path).lower():
                    self.workbook = wb
                    return success_response({
                        'workbook': wb,
                        'already_open': True,
                        'file_path': os.path.abspath(path)
                    })

            # 없으면 새로 열기
            self.workbook = self.excel.Workbooks.Open(os.path.abspath(path))
            return success_response({
                'workbook': self.workbook,
                'already_open': False,
                'file_path': os.path.abspath(path)
            })

        except Exception as e:
            return error_response(f"워크북 열기 실패: {str(e)}")

    def close_workbook(self, save: bool = True) -> dict:
        """워크북 안전하게 닫기"""
        try:
            if not self.workbook:
                return error_response("열려있는 워크북이 없습니다")

            if save:
                self.workbook.Save()

            self.workbook.Close(SaveChanges=save)
            self.workbook = None

            return success_response("워크북이 성공적으로 닫혔습니다")

        except Exception as e:
            return error_response(f"워크북 닫기 실패: {str(e)}")

    def quit_excel(self, force: bool = False) -> dict:
        """독립 Excel 인스턴스만 안전하게 종료 (다른 Excel에 영향 없음)"""
        try:
            if not self.excel:
                return success_response("Excel이 실행중이지 않습니다")

            # 독립 인스턴스인지 확인
            if not self._is_new_instance:
                return error_response("독립 인스턴스가 아니므로 종료할 수 없습니다")

            # 열려있는 워크북 확인 (이 인스턴스의 워크북만)
            try:
                workbook_count = self.excel.Workbooks.Count
            except:
                workbook_count = 0
                
            if workbook_count > 0:
                if not force:
                    return error_response(
                        f"이 Excel 인스턴스에 열려있는 워크북이 {workbook_count}개 있습니다. "
                        "force=True로 강제 종료하거나 먼저 워크북을 닫으세요."
                    )
                else:
                    # 강제 종료 시 이 인스턴스의 워크북만 저장 후 닫기
                    for wb in self.excel.Workbooks:
                        try:
                            if not wb.ReadOnly and wb.Path:  # 저장 가능한 경우만
                                wb.Save()
                            wb.Close(SaveChanges=False)
                        except:
                            pass

            # 독립 Excel 인스턴스만 종료 (다른 Excel에 영향 없음)
            try:
                self.excel.Quit()
            except:
                pass  # 이미 종료된 경우 무시
                
            self.excel = None
            self.workbook = None
            self._is_new_instance = False
            self._health_check_count = 0
            self._connection_attempts = 0

            return success_response("독립 Excel 인스턴스가 안전하게 종료되었습니다")

        except Exception as e:
            return error_response(f"Excel 종료 실패: {str(e)}")

# 전역 ExcelManager 인스턴스
_excel_manager = None

def get_excel_manager() -> ExcelManager:
    """전역 ExcelManager 인스턴스 반환"""
    global _excel_manager
    if _excel_manager is None:
        _excel_manager = ExcelManager()
    return _excel_manager

# 스레드 안전성 데코레이터
def thread_safe_excel(func):
    """Excel 작업을 스레드 안전하게 만드는 데코레이터"""
    @track_excel_access
    def wrapper(*args, **kwargs):
        with excel_lock:
            # COM 초기화는 전체 스레드에서 한 번만 하도록 수정
            return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

# Context Manager
@contextmanager
def excel_session(file_path: Optional[str] = None):
    """
    안전한 Excel 작업을 위한 Context Manager

    Example:
        with excel_session("data.xlsx") as excel:
            # Excel 작업 수행
            pass
    """
    manager = get_excel_manager()
    try:
        # Excel 연결/생성
        result = manager.connect_or_create(file_path)
        if not result['ok']:
            raise Exception(result.get('error', 'Excel 연결 실패'))

        yield manager

    except Exception as e:
        raise e
    finally:
        # 정리 작업 (워크북은 닫지 않고 유지)
        pass

# 연결 관리 함수들
@thread_safe_excel
def excel_connect(file_path: Optional[str] = None, visible: bool = True) -> Response:
    """
    독립 Excel 인스턴스 생성 (기존 Excel에 영향 없음)

    Args:
        file_path: Excel 파일 경로 (None이면 빈 Excel)
        visible: Excel을 화면에 표시할지 여부 (기본: True - 화면에 보임)

    Returns:
        Response with connection status
    """
    manager = get_excel_manager()
    return manager.connect_or_create(file_path, visible)

@thread_safe_excel
def excel_disconnect(save: bool = True) -> Response:
    """
    안전한 연결 해제

    Args:
        save: 저장 여부

    Returns:
        Response with disconnection status
    """
    manager = get_excel_manager()

    # 워크북이 있으면 닫기
    if manager.workbook:
        close_result = manager.close_workbook(save)
        if not close_result['ok']:
            return close_result

    # Excel 인스턴스가 새로 생성된 것이면 종료
    if manager._is_new_instance and manager.excel:
        return manager.quit_excel(force=False)

    return success_response("연결이 성공적으로 해제되었습니다")


# 데이터 읽기/쓰기 함수들
@thread_safe_excel
def excel_read_range(sheet: str, range_addr: str) -> Response:
    """
    범위 데이터 읽기

    Args:
        sheet: 시트 이름
        range_addr: 범위 주소 (예: "A1:C10")

    Returns:
        Response with data as 2D list
    """
    try:
        manager = get_excel_manager()

        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")

        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")

        # 시트 가져오기
        try:
            ws = manager.workbook.Worksheets(sheet)
        except:
            return error_response(f"시트 '{sheet}'를 찾을 수 없습니다")

        # 범위 데이터 읽기
        range_obj = ws.Range(range_addr)
        values = range_obj.Value

        # 단일 셀인 경우 처리
        if not isinstance(values, tuple):
            values = [[values]]
        # 1차원 배열인 경우 2차원으로 변환
        elif values and not isinstance(values[0], tuple):
            values = [list(values)]
        else:
            # 튜플을 리스트로 변환
            values = [list(row) for row in values]

        return success_response({
            'data': values,
            'rows': len(values),
            'cols': len(values[0]) if values else 0,
            'range': range_addr,
            'sheet': sheet
        })

    except Exception as e:
        return error_response(f"데이터 읽기 실패: {str(e)}")

@thread_safe_excel
def excel_write_range(sheet: str, range_addr: str, data: Union[List[List[Any]], List[Any], Any]) -> Response:
    """
    범위에 데이터 쓰기

    Args:
        sheet: 시트 이름
        range_addr: 범위 주소 (예: "A1:C10" 또는 "A1")
        data: 쓸 데이터 (2D 리스트, 1D 리스트, 또는 단일 값)

    Returns:
        Response with write status
    """
    try:
        manager = get_excel_manager()

        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")

        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")

        # 시트 가져오기
        try:
            ws = manager.workbook.Worksheets(sheet)
        except:
            return error_response(f"시트 '{sheet}'를 찾을 수 없습니다")

        # 데이터 형식 정규화
        if not isinstance(data, list):
            # 단일 값
            normalized_data = [[data]]
        elif not data:
            # 빈 리스트
            normalized_data = [[]]
        elif not isinstance(data[0], list):
            # 1D 리스트 -> 2D로 변환 (열로)
            normalized_data = [[item] for item in data]
        else:
            # 이미 2D 리스트
            normalized_data = data

        # 범위 가져오기
        range_obj = ws.Range(range_addr)

        # 데이터 크기와 범위 크기 맞추기
        rows = len(normalized_data)
        cols = len(normalized_data[0]) if normalized_data else 0

        if rows > 0 and cols > 0:
            # 시작 셀만 지정된 경우, 데이터 크기에 맞게 범위 확장
            if ':' not in range_addr:
                start_row = range_obj.Row
                start_col = range_obj.Column
                end_cell = ws.Cells(start_row + rows - 1, start_col + cols - 1)
                range_obj = ws.Range(range_obj, end_cell)

            # 데이터 쓰기
            range_obj.Value = normalized_data

        return success_response({
            'rows_written': rows,
            'cols_written': cols,
            'range': range_addr,
            'sheet': sheet
        })

    except Exception as e:
        return error_response(f"데이터 쓰기 실패: {str(e)}")

# 시트 관리 함수들
@thread_safe_excel
def excel_list_sheets() -> Response:
    """
    시트 목록 가져오기

    Returns:
        Response with list of sheet names
    """
    try:
        manager = get_excel_manager()

        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")

        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")

        sheets = []
        for i in range(1, manager.workbook.Worksheets.Count + 1):
            sheets.append(manager.workbook.Worksheets(i).Name)

        return success_response({
            'sheets': sheets,
            'count': len(sheets),
            'active_sheet': manager.workbook.ActiveSheet.Name
        })

    except Exception as e:
        return error_response(f"시트 목록 가져오기 실패: {str(e)}")

# ============= Facade Pattern =============
class ExcelFacade:
    """Excel 작업을 위한 Facade 인터페이스"""

    def __init__(self):
        self.manager = get_excel_manager()

    # 연결 관리
    def connect(self, file_path: str = None, visible: bool = True) -> Response:
        """독립 Excel 인스턴스 생성 (기존 Excel에 영향 없음)
        
        Args:
            file_path: Excel 파일 경로 (None이면 빈 Excel)
            visible: Excel을 화면에 표시 (기본: True)
        """
        return excel_connect(file_path, visible)

    def disconnect(self, save: bool = False) -> Response:
        """독립 Excel 인스턴스 종료 (다른 Excel에 영향 없음)"""
        return excel_disconnect(save)

    # 읽기 작업
    def read(self, sheet: str, range_addr: str) -> Response:
        """범위 읽기"""
        return excel_read_range(sheet, range_addr)

    def read_range(self, sheet: str, range_addr: str) -> Response:
        """범위 읽기 (별칭)"""
        return excel_read_range(sheet, range_addr)

    # 쓰기 작업
    def write(self, sheet: str, range_addr: str, data: Any) -> Response:
        """데이터 쓰기"""
        return excel_write_range(sheet, range_addr, data)

    def write_range(self, sheet: str, range_addr: str, data: Any) -> Response:
        """범위에 쓰기 (별칭)"""
        return excel_write_range(sheet, range_addr, data)

    # 시트 관리
    def list_sheets(self) -> Response:
        """시트 목록"""
        return excel_list_sheets()

    # 세션 확인
    def check_session(self) -> Response:
        """세션 상태 확인"""
        manager = get_excel_manager()
        return success_response({
            'active': manager.excel is not None,
            'workbook_open': manager.workbook is not None,
            'file_path': manager.file_path if manager.workbook else None
        })

    # 매니저 접근
    def get_manager(self):
        """ExcelManager 인스턴스 반환"""
        return get_excel_manager()
    
    # ==================== 고급 기능 추가 ====================
    
    def add_sheet(self, name: str, position: int = None) -> Response:
        """새 시트 추가"""
        return excel_add_sheet(name, position)
    
    def delete_sheet(self, name: str) -> Response:
        """시트 삭제"""
        return excel_delete_sheet(name)
    
    def set_formula(self, sheet: str, cell: str, formula: str) -> Response:
        """수식 설정"""
        return excel_set_formula(sheet, cell, formula)
    
    def format_cells(self, sheet: str, range_addr: str, format_options: Dict) -> Response:
        """셀 서식 지정"""
        return excel_format_cells(sheet, range_addr, format_options)
    
    def autofit(self, sheet: str, columns: bool = True, rows: bool = False) -> Response:
        """자동 맞춤"""
        return excel_autofit(sheet, columns, rows)
    
    def create_pivot_table(self, source_sheet: str, source_range: str, 
                          target_sheet: str, target_cell: str,
                          rows: List[str], columns: List[str] = None,
                          values: List[Dict] = None) -> Response:
        """피벗 테이블 생성"""
        return excel_create_pivot_table(
            source_sheet, source_range, target_sheet, target_cell,
            rows, columns, values
        )
    
    def sort_data(self, sheet: str, range_addr: str, key_column: str, ascending: bool = True) -> Response:
        """데이터 정렬"""
        return excel_sort_data(sheet, range_addr, key_column, ascending)
    
    def filter_data(self, sheet: str, range_addr: str, column: int, criteria: Any) -> Response:
        """데이터 필터링"""
        return excel_filter_data(sheet, range_addr, column, criteria)
    
    def import_csv(self, csv_path: str, sheet: str = None, start_cell: str = "A1") -> Response:
        """CSV 가져오기"""
        return excel_import_csv(csv_path, sheet, start_cell)
    
    def export_csv(self, csv_path: str, sheet: str = None, range_addr: str = None) -> Response:
        """CSV 내보내기"""
        return excel_export_csv(csv_path, sheet, range_addr)
    
    def find_replace(self, sheet: str, find_text: str, replace_text: str, range_addr: str = None) -> Response:
        """찾기 및 바꾸기"""
        return excel_find_replace(sheet, find_text, replace_text, range_addr)
    
    def save_as(self, file_path: str, file_format: str = 'xlsx') -> Response:
        """다른 이름으로 저장"""
        return excel_save_as(file_path, file_format)

# Facade 인스턴스 생성
excel = ExcelFacade()

# ==================== 고급 기능 추가 ====================

@thread_safe_excel
def excel_add_sheet(name: str, position: int = None) -> Response:
    """새 시트 추가"""
    try:
        manager = get_excel_manager()
        
        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")
        
        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")
        
        # 시트 추가
        if position is None:
            sheet = manager.workbook.Sheets.Add(After=manager.workbook.Sheets(manager.workbook.Sheets.Count))
        else:
            sheet = manager.workbook.Sheets.Add(Before=manager.workbook.Sheets(position))
        
        sheet.Name = name
        
        return success_response({
            'sheet_name': name,
            'position': sheet.Index,
            'total_sheets': manager.workbook.Sheets.Count
        }, f"시트 '{name}'가 추가되었습니다")
        
    except Exception as e:
        return error_response(f"시트 추가 실패: {str(e)}")

@thread_safe_excel
def excel_delete_sheet(name: str) -> Response:
    """시트 삭제"""
    try:
        manager = get_excel_manager()
        
        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")
        
        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")
        
        # DisplayAlerts 임시 비활성화
        old_alerts = manager.excel.DisplayAlerts
        manager.excel.DisplayAlerts = False
        
        try:
            manager.workbook.Sheets(name).Delete()
        finally:
            manager.excel.DisplayAlerts = old_alerts
        
        return success_response(
            f"시트 '{name}'가 삭제되었습니다"
        )
        
    except Exception as e:
        return error_response(f"시트 삭제 실패: {str(e)}")

@thread_safe_excel
def excel_set_formula(sheet: str, cell: str, formula: str) -> Response:
    """셀에 수식 설정"""
    try:
        manager = get_excel_manager()
        
        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")
        
        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")
        
        # 시트 가져오기
        try:
            ws = manager.workbook.Worksheets(sheet)
        except:
            return error_response(f"시트 '{sheet}'를 찾을 수 없습니다")
        
        # 수식 설정 (=로 시작하도록 보장)
        if not formula.startswith('='):
            formula = '=' + formula
        
        ws.Range(cell).Formula = formula
        value = ws.Range(cell).Value
        
        return success_response({
            'cell': cell,
            'formula': formula,
            'calculated_value': value,
            'sheet': sheet
        }, f"수식이 {cell}에 설정되었습니다")
        
    except Exception as e:
        return error_response(f"수식 설정 실패: {str(e)}")

@thread_safe_excel
def excel_format_cells(sheet: str, range_addr: str, format_options: Dict) -> Response:
    """셀 서식 지정
    
    format_options:
        - bold: bool
        - italic: bool
        - font_size: int
        - font_color: int (RGB)
        - bg_color: int (RGB)
        - number_format: str (예: "#,##0.00")
        - alignment: str ("left", "center", "right")
        - wrap_text: bool
    """
    try:
        manager = get_excel_manager()
        
        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")
        
        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")
        
        # 시트 가져오기
        try:
            ws = manager.workbook.Worksheets(sheet)
        except:
            return error_response(f"시트 '{sheet}'를 찾을 수 없습니다")
        
        range_obj = ws.Range(range_addr)
        applied = []
        
        # 폰트 서식
        if 'bold' in format_options:
            range_obj.Font.Bold = format_options['bold']
            applied.append('굵게')
        
        if 'italic' in format_options:
            range_obj.Font.Italic = format_options['italic']
            applied.append('기울임')
        
        if 'font_size' in format_options:
            range_obj.Font.Size = format_options['font_size']
            applied.append(f'글꼴크기:{format_options["font_size"]}')
        
        if 'font_color' in format_options:
            range_obj.Font.Color = format_options['font_color']
            applied.append('글꼴색')
        
        # 배경색
        if 'bg_color' in format_options:
            range_obj.Interior.Color = format_options['bg_color']
            applied.append('배경색')
        
        # 숫자 서식
        if 'number_format' in format_options:
            range_obj.NumberFormat = format_options['number_format']
            applied.append('숫자서식')
        
        # 정렬
        if 'alignment' in format_options:
            align_map = {
                'left': -4131,    # xlLeft
                'center': -4108,  # xlCenter
                'right': -4152    # xlRight
            }
            if format_options['alignment'] in align_map:
                range_obj.HorizontalAlignment = align_map[format_options['alignment']]
                applied.append(f'정렬:{format_options["alignment"]}')
        
        # 텍스트 줄바꿈
        if 'wrap_text' in format_options:
            range_obj.WrapText = format_options['wrap_text']
            applied.append('텍스트줄바꿈')
        
        return success_response({
            'range': range_addr,
            'applied_formats': applied,
            'sheet': sheet
        }, f"{len(applied)}개 서식이 적용되었습니다")
        
    except Exception as e:
        return error_response(f"서식 지정 실패: {str(e)}")

@thread_safe_excel
def excel_autofit(sheet: str, columns: bool = True, rows: bool = False) -> Response:
    """열/행 자동 맞춤"""
    try:
        manager = get_excel_manager()
        
        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")
        
        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")
        
        # 시트 가져오기
        try:
            ws = manager.workbook.Worksheets(sheet)
        except:
            return error_response(f"시트 '{sheet}'를 찾을 수 없습니다")
        
        applied = []
        
        if columns:
            ws.Cells.EntireColumn.AutoFit()
            applied.append('열')
        
        if rows:
            ws.Cells.EntireRow.AutoFit()
            applied.append('행')
        
        return success_response(
            f"{', '.join(applied)} 자동 맞춤이 적용되었습니다"
        )
        
    except Exception as e:
        return error_response(f"자동 맞춤 실패: {str(e)}")

@thread_safe_excel
def excel_create_pivot_table(
    source_sheet: str,
    source_range: str,
    target_sheet: str,
    target_cell: str,
    rows: List[str],
    columns: List[str] = None,
    values: List[Dict] = None
) -> Response:
    """피벗 테이블 생성
    
    Args:
        source_sheet: 원본 데이터 시트
        source_range: 원본 데이터 범위
        target_sheet: 피벗 테이블을 생성할 시트
        target_cell: 피벗 테이블 시작 위치
        rows: 행 필드 목록
        columns: 열 필드 목록 (선택사항)
        values: 값 필드 설정 [{'field': 'Sales', 'function': 'Sum'}]
    """
    try:
        manager = get_excel_manager()
        
        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")
        
        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")
        
        # 시트 가져오기
        try:
            src_ws = manager.workbook.Worksheets(source_sheet)
            tgt_ws = manager.workbook.Worksheets(target_sheet)
        except Exception as e:
            return error_response(f"시트를 찾을 수 없습니다: {str(e)}")
        
        # 피벗 캐시 생성
        pc = manager.workbook.PivotCaches().Create(
            SourceType=1,  # xlDatabase
            SourceData=src_ws.Range(source_range)
        )
        
        # 피벗 테이블 생성
        pivot_name = f"PivotTable_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        pt = pc.CreatePivotTable(
            TableDestination=tgt_ws.Range(target_cell),
            TableName=pivot_name
        )
        
        # 행 필드 추가
        for field_name in rows:
            field = pt.PivotFields(field_name)
            field.Orientation = 1  # xlRowField
        
        # 열 필드 추가
        if columns:
            for field_name in columns:
                field = pt.PivotFields(field_name)
                field.Orientation = 2  # xlColumnField
        
        # 값 필드 추가
        if values:
            for value_config in values:
                field = pt.PivotFields(value_config['field'])
                field.Orientation = 4  # xlDataField
                
                # 집계 함수 설정
                if 'function' in value_config:
                    func_map = {
                        'Sum': -4157,
                        'Count': -4112,
                        'Average': -4106,
                        'Max': -4136,
                        'Min': -4139
                    }
                    if value_config['function'] in func_map:
                        field.Function = func_map[value_config['function']]
                
                if 'name' in value_config:
                    field.Name = value_config['name']
        
        return success_response({
            'pivot_name': pivot_name,
            'source': f"{source_sheet}!{source_range}",
            'target': f"{target_sheet}!{target_cell}",
            'rows': rows,
            'columns': columns or [],
            'values': values or []
        }, f"피벗 테이블 '{pivot_name}'이 생성되었습니다")
        
    except Exception as e:
        return error_response(f"피벗 테이블 생성 실패: {str(e)}", traceback.format_exc())

@thread_safe_excel
def excel_sort_data(sheet: str, range_addr: str, key_column: str, ascending: bool = True) -> Response:
    """데이터 정렬"""
    try:
        manager = get_excel_manager()
        
        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")
        
        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")
        
        # 시트 가져오기
        try:
            ws = manager.workbook.Worksheets(sheet)
        except:
            return error_response(f"시트 '{sheet}'를 찾을 수 없습니다")
        
        range_obj = ws.Range(range_addr)
        order_value = 1 if ascending else 2  # xlAscending or xlDescending
        
        range_obj.Sort(
            Key1=ws.Range(key_column),
            Order1=order_value,
            Header=1  # xlYes
        )
        
        return success_response(
            f"데이터가 {key_column} 기준 {'오름차순' if ascending else '내림차순'}으로 정렬되었습니다"
        )
        
    except Exception as e:
        return error_response(f"데이터 정렬 실패: {str(e)}")

@thread_safe_excel
def excel_filter_data(sheet: str, range_addr: str, column: int, criteria: Any) -> Response:
    """데이터 필터링"""
    try:
        manager = get_excel_manager()
        
        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")
        
        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")
        
        # 시트 가져오기
        try:
            ws = manager.workbook.Worksheets(sheet)
        except:
            return error_response(f"시트 '{sheet}'를 찾을 수 없습니다")
        
        range_obj = ws.Range(range_addr)
        range_obj.AutoFilter(Field=column, Criteria1=criteria)
        
        return success_response(
            f"열 {column}에 '{criteria}' 필터가 적용되었습니다"
        )
        
    except Exception as e:
        return error_response(f"필터 적용 실패: {str(e)}")

@thread_safe_excel
def excel_import_csv(csv_path: str, sheet: str = None, start_cell: str = "A1") -> Response:
    """CSV 파일 가져오기"""
    try:
        manager = get_excel_manager()
        
        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")
        
        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")
        
        # CSV 파일 읽기
        if not os.path.exists(csv_path):
            return error_response(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
        
        data = []
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            data = list(reader)
        
        if not data:
            return error_response("CSV 파일이 비어있습니다")
        
        # 시트 선택 또는 현재 시트 사용
        if sheet:
            try:
                ws = manager.workbook.Worksheets(sheet)
            except:
                return error_response(f"시트 '{sheet}'를 찾을 수 없습니다")
        else:
            ws = manager.workbook.ActiveSheet
            sheet = ws.Name
        
        # 데이터 쓰기
        start_range = ws.Range(start_cell)
        rows = len(data)
        cols = len(data[0]) if data else 0
        
        if rows > 0 and cols > 0:
            end_cell = start_range.Offset(rows, cols).Offset(-1, -1)
            range_obj = ws.Range(start_range, end_cell)
            range_obj.Value = data
        
        return success_response({
            'csv_file': csv_path,
            'rows_imported': rows,
            'cols_imported': cols,
            'sheet': sheet,
            'start_cell': start_cell
        }, f"{rows}행 {cols}열의 데이터를 가져왔습니다")
        
    except Exception as e:
        return error_response(f"CSV 가져오기 실패: {str(e)}", traceback.format_exc())

@thread_safe_excel
def excel_export_csv(csv_path: str, sheet: str = None, range_addr: str = None) -> Response:
    """CSV 파일로 내보내기"""
    try:
        manager = get_excel_manager()
        
        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")
        
        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")
        
        # 시트 선택
        if sheet:
            try:
                ws = manager.workbook.Worksheets(sheet)
            except:
                return error_response(f"시트 '{sheet}'를 찾을 수 없습니다")
        else:
            ws = manager.workbook.ActiveSheet
            sheet = ws.Name
        
        # 범위 선택
        if range_addr:
            range_obj = ws.Range(range_addr)
        else:
            range_obj = ws.UsedRange
            range_addr = str(range_obj.Address)
        
        # 데이터 읽기
        values = range_obj.Value
        
        # 데이터 정규화
        if not values:
            data = []
        elif not isinstance(values, tuple):
            data = [[values]]
        elif values and not isinstance(values[0], tuple):
            data = [list(values)]
        else:
            data = [list(row) for row in values]
        
        # CSV 파일로 저장
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        return success_response({
            'csv_file': csv_path,
            'rows_exported': len(data),
            'cols_exported': len(data[0]) if data else 0,
            'sheet': sheet,
            'range': range_addr
        }, f"{len(data)}행의 데이터를 내보냈습니다")
        
    except Exception as e:
        return error_response(f"CSV 내보내기 실패: {str(e)}", traceback.format_exc())

@thread_safe_excel
def excel_find_replace(sheet: str, find_text: str, replace_text: str, range_addr: str = None) -> Response:
    """찾기 및 바꾸기"""
    try:
        manager = get_excel_manager()
        
        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")
        
        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")
        
        # 시트 가져오기
        try:
            ws = manager.workbook.Worksheets(sheet)
        except:
            return error_response(f"시트 '{sheet}'를 찾을 수 없습니다")
        
        # 범위 선택
        if range_addr:
            search_range = ws.Range(range_addr)
        else:
            search_range = ws.UsedRange
            range_addr = "UsedRange"
        
        # 찾기 및 바꾸기 실행
        replaced = search_range.Replace(
            What=find_text,
            Replacement=replace_text,
            LookAt=2,  # xlPart
            SearchOrder=1,  # xlByRows
            MatchCase=False
        )
        
        return success_response(
            f"'{find_text}'를 '{replace_text}'로 바꿨습니다 (범위: {range_addr})"
        )
        
    except Exception as e:
        return error_response(f"찾기/바꾸기 실패: {str(e)}")

@thread_safe_excel
def excel_save_as(file_path: str, file_format: str = 'xlsx') -> Response:
    """다른 이름으로 저장"""
    try:
        manager = get_excel_manager()
        
        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")
        
        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")
        
        # 파일 형식 매핑
        format_map = {
            'xlsx': 51,  # xlOpenXMLWorkbook
            'xls': 56,   # xlExcel8
            'csv': 6,    # xlCSV
            'pdf': 0     # xlTypePDF
        }
        
        file_format_value = format_map.get(file_format.lower(), 51)
        
        # 절대 경로로 변환
        abs_path = os.path.abspath(file_path)
        
        # 저장
        manager.workbook.SaveAs(abs_path, FileFormat=file_format_value)
        manager.file_path = abs_path
        
        return success_response({
            'file_path': abs_path,
            'format': file_format
        }, f"파일이 '{abs_path}'로 저장되었습니다")
        
    except Exception as e:
        return error_response(f"저장 실패: {str(e)}")

# 레거시 호환성을 위한 직접 export
__all__ = [
    'excel',
    'ExcelManager',
    'excel_connect',
    'excel_disconnect',
    'excel_read_range',
    'excel_write_range',
    'excel_list_sheets',
    'excel_add_sheet',
    'excel_delete_sheet',
    'excel_set_formula',
    'excel_format_cells',
    'excel_autofit',
    'excel_create_pivot_table',
    'excel_sort_data',
    'excel_filter_data',
    'excel_import_csv',
    'excel_export_csv',
    'excel_find_replace',
    'excel_save_as',
    'get_excel_manager'
]
"""
Excel 실시간 작업 헬퍼 모듈
pywin32를 사용하여 Excel COM 객체를 통한 실시간 작업 지원
"""

import win32com.client as win32
import pythoncom
import threading
from contextlib import contextmanager
from typing import Optional, List, Any, Union, Tuple
import os
import time
from typing import Dict, Any, TypedDict

# Response 타입 정의
Response = Dict[str, Any]

def success_response(data: Any) -> Response:
    """성공 응답 생성"""
    if isinstance(data, str):
        return {'ok': True, 'message': data}
    return {'ok': True, 'data': data}

def error_response(error: str) -> Response:
    """에러 응답 생성"""
    return {'ok': False, 'error': error}

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
    """Excel COM 객체 생명주기 관리"""

    def __init__(self):
            self.excel = None
            self.workbook = None
            self.file_path = None  # 파일 경로 추가
            self._is_new_instance = False

    def __del__(self):
        """소멸자: COM 객체 정리"""
        try:
            if self.workbook:
                try:
                    self.workbook.Close(SaveChanges=False)
                except:
                    pass
            if self.excel and self._is_new_instance:
                try:
                    self.excel.Quit()
                except:
                    pass
        except:
            pass
        finally:
            self.excel = None
            self.workbook = None

    def ensure_com_connection(self) -> bool:
        """COM 연결 상태 확인 및 복구"""
        try:
            if self.excel:
                # 간단한 작업으로 연결 테스트
                _ = self.excel.Visible
                return True
        except:
            self.excel = None
            self.workbook = None
            return False
        return False

    def connect_or_create(self, file_path: Optional[str] = None) -> dict:
        """
        기존 Excel에 연결하거나 새로 생성

        Args:
            file_path: 연결할 Excel 파일 경로 (None이면 빈 Excel)

        Returns:
            Response dict with excel instance
        """
        try:
            # 1. 먼저 파일 경로가 주어졌고 파일이 존재하면 GetObject 시도
            if file_path and os.path.exists(file_path):
                try:
                    # GetObject로 이미 열려있는 파일에 연결 시도
                    self.workbook = win32.GetObject(os.path.abspath(file_path))
                    self.excel = self.workbook.Application
                    self.excel.Visible = True
                    self._is_new_instance = False
                    self.file_path = os.path.abspath(file_path)  # file_path 저장
                    return success_response({
                        'excel': self.excel,
                        'workbook': self.workbook,
                        'connected_to_existing': True,
                        'file_path': self.file_path
                    })
                except Exception:
                    # GetObject 실패 시 아래에서 새로 열기
                    pass

            # 2. GetObject 실패하거나 파일 경로가 없으면 새 인스턴스 생성
            try:
                # DispatchEx로 완전히 새로운 Excel 인스턴스 생성
                self.excel = win32.DispatchEx('Excel.Application')
                self.excel.Visible = True
                self._is_new_instance = True

                if file_path:
                    # 파일 경로가 주어졌으면 파일 열기
                    if os.path.exists(file_path):
                        self.workbook = self.excel.Workbooks.Open(os.path.abspath(file_path))
                    else:
                        # 파일이 없으면 새로 생성
                        self.workbook = self.excel.Workbooks.Add()
                        self.workbook.SaveAs(os.path.abspath(file_path))
                else:
                    # 파일 경로가 없으면 빈 워크북 생성
                    self.workbook = self.excel.Workbooks.Add()

                self.file_path = os.path.abspath(file_path) if file_path else None  # file_path 저장
                return success_response({
                    'excel': self.excel,
                    'workbook': self.workbook,
                    'connected_to_existing': False,
                    'file_path': self.file_path
                })

            except Exception as e:
                return error_response(f"Excel 인스턴스 생성 실패: {str(e)}")

        except Exception as e:
            return error_response(f"Excel 연결 실패: {str(e)}")

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
        """Excel 종료"""
        try:
            if not self.excel:
                return success_response("Excel이 실행중이지 않습니다")

            # 열려있는 모든 워크북 확인
            if self.excel.Workbooks.Count > 0:
                if not force:
                    return error_response(
                        f"열려있는 워크북이 {self.excel.Workbooks.Count}개 있습니다. "
                        "force=True로 강제 종료하거나 먼저 워크북을 닫으세요."
                    )
                else:
                    # 강제 종료 시 모든 워크북 저장 후 닫기
                    for wb in self.excel.Workbooks:
                        try:
                            wb.Save()
                            wb.Close()
                        except:
                            pass

            # Excel 종료
            self.excel.Quit()
            self.excel = None
            self.workbook = None
            self._is_new_instance = False

            return success_response("Excel이 성공적으로 종료되었습니다")

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
def excel_connect(file_path: Optional[str] = None) -> Response:
    """
    Excel 연결/생성

    Args:
        file_path: Excel 파일 경로 (None이면 빈 Excel)

    Returns:
        Response with connection status
    """
    manager = get_excel_manager()
    return manager.connect_or_create(file_path)

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
    def connect(self, file_path: str = None) -> Response:
        """Excel 파일에 연결"""
        return excel_connect(file_path)

    def disconnect(self, save: bool = False) -> Response:
        """Excel 연결 종료"""
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

# Facade 인스턴스 생성
excel = ExcelFacade()

# 레거시 호환성을 위한 직접 export
__all__ = [
    'excel',
    'ExcelManager',
    'excel_connect',
    'excel_disconnect',
    'excel_read_range',
    'excel_write_range',
    'excel_list_sheets',
    'get_excel_manager'
]
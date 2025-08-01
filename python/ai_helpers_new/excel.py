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
                    return success_response({
                        'excel': self.excel,
                        'workbook': self.workbook,
                        'connected_to_existing': True,
                        'file_path': os.path.abspath(file_path)
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

                return success_response({
                    'excel': self.excel,
                    'workbook': self.workbook,
                    'connected_to_existing': False,
                    'file_path': os.path.abspath(file_path) if file_path else None
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
def excel_read_table(sheet: str, start_cell: str) -> Response:
    """
    테이블 형태 읽기 (헤더 포함, 빈 행까지)

    Args:
        sheet: 시트 이름
        start_cell: 시작 셀 (예: "A1")

    Returns:
        Response with table data and headers
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

        # 시작 셀에서 CurrentRegion 사용하여 연속된 데이터 영역 가져오기
        start_range = ws.Range(start_cell)
        table_range = start_range.CurrentRegion
        values = table_range.Value

        if not values:
            return success_response({
                'headers': [],
                'data': [],
                'rows': 0,
                'cols': 0
            })

        # 단일 셀인 경우 처리
        if not isinstance(values, tuple):
            values = [[values]]
        # 1차원 배열인 경우 2차원으로 변환
        elif values and not isinstance(values[0], tuple):
            values = [list(values)]
        else:
            # 튜플을 리스트로 변환
            values = [list(row) for row in values]

        # 첫 번째 행을 헤더로 처리
        headers = values[0] if values else []
        data = values[1:] if len(values) > 1 else []

        return success_response({
            'headers': headers,
            'data': data,
            'rows': len(data),
            'cols': len(headers),
            'start_cell': start_cell,
            'sheet': sheet
        })

    except Exception as e:
        return error_response(f"테이블 읽기 실패: {str(e)}")

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

@thread_safe_excel
def excel_add_sheet(name: str, position: Optional[int] = None) -> Response:
    """
    시트 추가

    Args:
        name: 시트 이름
        position: 삽입 위치 (None이면 마지막에 추가)

    Returns:
        Response with new sheet info
    """
    try:
        manager = get_excel_manager()

        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")

        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")

        # 시트 이름 중복 확인
        existing_sheets = [ws.Name for ws in manager.workbook.Worksheets]
        if name in existing_sheets:
            return error_response(f"시트 '{name}'가 이미 존재합니다")

        # 시트 추가
        if position is None:
            # 마지막에 추가
            new_sheet = manager.workbook.Worksheets.Add(After=manager.workbook.Worksheets(manager.workbook.Worksheets.Count))
        else:
            # 특정 위치에 추가
            new_sheet = manager.workbook.Worksheets.Add(Before=manager.workbook.Worksheets(position))

        new_sheet.Name = name

        return success_response({
            'sheet_name': name,
            'position': new_sheet.Index,
            'total_sheets': manager.workbook.Worksheets.Count
        })

    except Exception as e:
        return error_response(f"시트 추가 실패: {str(e)}")

@thread_safe_excel
def excel_delete_sheet(name: str) -> Response:
    """
    시트 삭제

    Args:
        name: 삭제할 시트 이름

    Returns:
        Response with deletion status
    """
    try:
        manager = get_excel_manager()

        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")

        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")

        # 시트가 1개뿐인 경우 삭제 불가
        if manager.workbook.Worksheets.Count == 1:
            return error_response("워크북에는 최소 1개의 시트가 있어야 합니다")

        # 시트 찾기
        try:
            sheet = manager.workbook.Worksheets(name)
        except:
            return error_response(f"시트 '{name}'를 찾을 수 없습니다")

        # 경고 메시지 비활성화
        manager.excel.DisplayAlerts = False
        sheet.Delete()
        manager.excel.DisplayAlerts = True

        return success_response({
            'deleted_sheet': name,
            'remaining_sheets': manager.workbook.Worksheets.Count
        })

    except Exception as e:
        return error_response(f"시트 삭제 실패: {str(e)}")

@thread_safe_excel
def excel_select_sheet(name: str) -> Response:
    """
    시트 선택 (활성화)

    Args:
        name: 선택할 시트 이름

    Returns:
        Response with selection status
    """
    try:
        manager = get_excel_manager()

        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")

        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")

        # 시트 찾기
        try:
            sheet = manager.workbook.Worksheets(name)
        except:
            return error_response(f"시트 '{name}'를 찾을 수 없습니다")

        # 시트 활성화
        sheet.Activate()

        return success_response({
            'selected_sheet': name,
            'sheet_index': sheet.Index
        })

    except Exception as e:
        return error_response(f"시트 선택 실패: {str(e)}")

# 고급 기능 (피벗, 수식)
@thread_safe_excel
def excel_create_pivot(
    source_range: str, 
    target_sheet: str, 
    target_cell: str,
    rows: List[str] = None,
    columns: List[str] = None,
    values: List[str] = None,
    name: str = "PivotTable1"
) -> Response:
    """
    피벗 테이블 생성

    Args:
        source_range: 원본 데이터 범위 (예: "Sheet1!A1:D100")
        target_sheet: 피벗 테이블을 생성할 시트
        target_cell: 피벗 테이블 시작 위치 (예: "A1")
        rows: 행 필드로 사용할 열 이름들
        columns: 열 필드로 사용할 열 이름들
        values: 값 필드로 사용할 열 이름들
        name: 피벗 테이블 이름

    Returns:
        Response with pivot table info
    """
    try:
        manager = get_excel_manager()

        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")

        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")

        # 대상 시트 가져오기
        try:
            target_ws = manager.workbook.Worksheets(target_sheet)
        except:
            return error_response(f"시트 '{target_sheet}'를 찾을 수 없습니다")

        # 피벗 캐시 생성
        pc = manager.workbook.PivotCaches().Create(
            SourceType=win32.constants.xlDatabase,
            SourceData=source_range
        )

        # 피벗 테이블 생성
        target_range = target_ws.Range(target_cell)
        pt = pc.CreatePivotTable(
            TableDestination=target_range,
            TableName=name
        )

        # 필드 설정
        if rows:
            for field_name in rows:
                try:
                    field = pt.PivotFields(field_name)
                    field.Orientation = win32.constants.xlRowField
                except:
                    pass

        if columns:
            for field_name in columns:
                try:
                    field = pt.PivotFields(field_name)
                    field.Orientation = win32.constants.xlColumnField
                except:
                    pass

        if values:
            for field_name in values:
                try:
                    field = pt.PivotFields(field_name)
                    field.Orientation = win32.constants.xlDataField
                    field.Function = win32.constants.xlSum
                except:
                    pass

        return success_response({
            'pivot_name': name,
            'source_range': source_range,
            'target_location': f"{target_sheet}!{target_cell}",
            'row_fields': rows or [],
            'column_fields': columns or [],
            'value_fields': values or []
        })

    except Exception as e:
        return error_response(f"피벗 테이블 생성 실패: {str(e)}")

@thread_safe_excel
def excel_apply_formula(range_addr: str, formula: str, sheet: Optional[str] = None) -> Response:
    """
    수식 적용

    Args:
        range_addr: 수식을 적용할 범위 (예: "A1" 또는 "A1:A10")
        formula: 적용할 수식 (예: "=SUM(B1:B10)" 또는 "=A1+B1")
        sheet: 시트 이름 (None이면 현재 활성 시트)

    Returns:
        Response with formula application status
    """
    try:
        manager = get_excel_manager()

        if not manager.ensure_com_connection():
            return error_response("Excel 연결이 끊어졌습니다")

        if not manager.workbook:
            return error_response("열려있는 워크북이 없습니다")

        # 시트 가져오기
        if sheet:
            try:
                ws = manager.workbook.Worksheets(sheet)
            except:
                return error_response(f"시트 '{sheet}'를 찾을 수 없습니다")
        else:
            ws = manager.workbook.ActiveSheet
            sheet = ws.Name

        # 범위 가져오기
        range_obj = ws.Range(range_addr)

        # 수식이 =로 시작하지 않으면 추가
        if not formula.startswith('='):
            formula = '=' + formula

        # 수식 적용
        if ':' in range_addr:
            # 범위에 적용 - 상대 참조를 위해 FormulaR1C1 사용 가능
            # 첫 번째 셀에 수식 설정 후 복사
            first_cell = range_obj.Cells(1, 1)
            first_cell.Formula = formula

            # 나머지 셀에 복사 (Excel이 자동으로 상대 참조 조정)
            first_cell.Copy()
            range_obj.PasteSpecial(Paste=win32.constants.xlPasteFormulas)
            manager.excel.CutCopyMode = False  # 복사 모드 해제
        else:
            # 단일 셀에 적용
            range_obj.Formula = formula

        # 계산 실행
        manager.excel.Calculate()

        return success_response({
            'range': range_addr,
            'sheet': sheet,
            'formula': formula,
            'cells_affected': range_obj.Count
        })

    except Exception as e:
        return error_response(f"수식 적용 실패: {str(e)}")


# WebAutomation Action Recorder 개선안

## 1. ActionRecorder 클래스 추가

```python
class ActionRecorder:
    '''웹 자동화 액션을 기록하고 파이썬 스크립트로 변환하는 클래스'''

    def __init__(self):
        self.actions = []  # 기록된 액션들
        self.imports = set()  # 필요한 import 문
        self.variables = {}  # 변수 저장

    def record_action(self, action_type, **kwargs):
        '''액션 기록'''
        self.actions.append({
            'type': action_type,
            'timestamp': datetime.now(),
            'params': kwargs
        })

    def generate_script(self, script_name='web_automation_script.py'):
        '''기록된 액션을 파이썬 스크립트로 변환'''
        # 스크립트 생성 로직
```

## 2. WebAutomation 클래스 확장

기존 메서드들을 래핑하여 액션을 자동 기록:

```python
class WebAutomationWithRecording(WebAutomation):
    def __init__(self, *args, record_actions=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.recorder = ActionRecorder() if record_actions else None

    def go_to_page(self, url, **kwargs):
        result = super().go_to_page(url, **kwargs)
        if self.recorder and result['success']:
            self.recorder.record_action('navigate', url=url, **kwargs)
        return result

    def click_element(self, selector, by='css', **kwargs):
        result = super().click_element(selector, by, **kwargs)
        if self.recorder and result['success']:
            self.recorder.record_action('click', selector=selector, by=by, **kwargs)
        return result
```

## 3. 헬퍼 함수 확장

```python
def web_record_start():
    '''액션 레코딩 시작'''
    global _web_automation_instance
    _web_automation_instance = WebAutomationWithRecording(record_actions=True)
    return _web_automation_instance

def web_record_stop_and_generate(output_file='auto_script.py'):
    '''레코딩 중지 및 스크립트 생성'''
    if _web_automation_instance and _web_automation_instance.recorder:
        return _web_automation_instance.recorder.generate_script(output_file)
```

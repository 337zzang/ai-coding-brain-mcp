class TestClass:
    def __init__(self):
        self.value = 1
        
    def test_method(self):
        # workflow manager reset
        self._workflow_manager = None
        self._history_manager = None
        print("test")

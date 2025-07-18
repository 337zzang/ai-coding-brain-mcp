# 테스트용 중첩 구조 코드
@decorator
class OuterClass:
    """외부 클래스"""
    
    def method1(self):
        """메서드 1"""
        pass
        
    @property
    def prop(self):
        return self._prop
        
    class InnerClass:
        """내부 클래스"""
        
        def inner_method(self):
            """내부 메서드"""
            pass
            
        class DeepClass:
            """깊은 중첩 클래스"""
            
            def deep_method(self):
                """깊은 메서드"""
                pass
                
def standalone_function():
    """독립 함수"""
    
    def nested_function():
        """중첩 함수"""
        pass
        
    return nested_function

async def async_function():
    """비동기 함수"""
    pass
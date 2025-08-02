import sys
import os

# Add python directory to path
sys.path.insert(0, r'C:\Users\82106\Desktop\ai-coding-brain-mcp\python')

print("=== Simple O3 Function Test ===\n")

# Skip web automation import errors
import warnings
warnings.filterwarnings('ignore')

# Direct import from llm module
try:
    from ai_helpers_new.llm import ask_o3_practical, O3ContextBuilder, quick_o3_context
    print("[OK] Successfully imported O3 functions from llm module")
    
    # Test O3ContextBuilder
    print("\nTesting O3ContextBuilder:")
    builder = O3ContextBuilder()
    print(f"  Type: {type(builder)}")
    
    # Check if it's a function that returns a class
    if callable(builder):
        print("  O3ContextBuilder is a function")
        builder_instance = builder
        print(f"  Instance type: {type(builder_instance)}")
        
        # Test methods
        if hasattr(builder_instance, 'add_context'):
            print("  [OK] add_context method exists")
        if hasattr(builder_instance, 'add_error'):
            print("  [OK] add_error method exists")
        if hasattr(builder_instance, 'build'):
            print("  [OK] build method exists")
    
    print("\n[SUCCESS] O3 functions are available!")
    
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

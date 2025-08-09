"""
Utility functions for standard responses
"""

import os

def ok(data):
    """Success response"""
    return {'ok': True, 'data': data}

def err(message):
    """Error response"""
    return {'ok': False, 'error': message}

def is_ok(result):
    """Check if result is successful"""
    return result.get('ok', False)

def get_data(result):
    """Get data from result"""
    return result.get('data')

def get_error(result):
    """Get error from result"""
    return result.get('error')

def safe_read_file(filepath, encoding='utf-8'):
    """Safely read file with error handling"""
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except (FileNotFoundError, PermissionError, IOError, UnicodeDecodeError) as e:
        return None

def safe_write_file(filepath, content, encoding='utf-8'):
    """Safely write file with error handling"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
        
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except (PermissionError, IOError) as e:
        return False

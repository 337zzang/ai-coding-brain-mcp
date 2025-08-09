"""
Utility functions for standard responses
"""

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

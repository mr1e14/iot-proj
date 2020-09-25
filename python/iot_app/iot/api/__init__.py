from flask import request, jsonify
from flask_restful import abort
from functools import wraps

import hmac


def response_success(data=None):
    if data is None:
        data = {}
    return jsonify({
        'success': True,
        'data': data
    })


def response_error(error_code=500, message='Server encountered error processing the request'):
    abort(error_code, message=message, success=False)


def make_api_key_validator(api_key):
    """
    Generates API key validator function to allow / deny access to resources
    """
    def validate_api_key(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_api_key = request.headers.get('API_KEY')
            if user_api_key is None:
                response_error(error_code=401, message='Missing API key')
            if not hmac.compare_digest(api_key, user_api_key):
                response_error(error_code=401, message='Invalid API key')
            return func(*args, **kwargs)
        return wrapper
    return validate_api_key


from .sensor_readings import TemperatureResource, HumidityResource
from .lights import LightResource, LightEffectResource, LightsDiscoveryResource

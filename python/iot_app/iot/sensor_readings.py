from iot_app.logger.logger import get_logger
from iot_app.config import config
from iot_app.db.sensor_readings import save_temp, get_last_temp, save_humidity, get_last_humidity

from typing import Dict
from functools import wraps
from flask import request, jsonify
from flask_restful import Resource, reqparse, fields, abort
from bson.objectid import ObjectId

import hmac

logging = get_logger(__name__)


def _response_success(data={}):
    return jsonify({
        'success': True,
        'data': data
    })

def _response_error(error_code=500, message='Server encountered error processing the request'):
    abort(error_code, message=message, success=False)

class ReadingType:
    TEMPERATURE = 'temp'
    HUMIDITY = 'humidity'


class SensorReadingResource(Resource):

    def transform_db_result(self, db_result, reading_type):
        """
        Transforms raw mongo db result set to client-friendly response, ready to jsonify
        """
        if db_result is None:
            return {
                reading_type: None,
                'timestamp': None
            }
        timestamp = ObjectId(db_result['_id']).generation_time
        return {
            reading_type: db_result['value'],
            'timestamp': timestamp
        }

    def __validate_api_key(func):
        """
        Validates API key used to make calls to SensorReading resources
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            api_key = request.headers.get('API_KEY')
            if api_key is None:
                _response_error(error_code=401, message='Missing API key')
            if not hmac.compare_digest(config['SENSORS_API_KEY'], api_key):
                _response_error(error_code=401, message='Invalid API key')
            return func(*args, **kwargs)
        return wrapper

    method_decorators = [__validate_api_key]


class TemperatureResource(SensorReadingResource):
    __temp_put_parser = reqparse.RequestParser()
    __temp_put_parser.add_argument("temp", type=int, case_sensitive=False, required=True)

    def __transform_for_temperature(self, db_result):
        return self.transform_db_result(db_result, ReadingType.TEMPERATURE)

    def get(self):
        logging.debug('GET /temperature')
        try:
            db_result = get_last_temp()
            return _response_success(self.__transform_for_temperature(db_result))
        except Exception as err:
            logging.error(err)
            return _response_error()

    def put(self):
        request_args = self.__temp_put_parser.parse_args()
        logging.debug(f'PUT /temperature with args: {request_args}')
        try:
            save_temp(request_args['temp'])
            return _response_success()
        except Exception as err:
            logging.error(err)
            return _response_error()

class HumidityResource(SensorReadingResource):
    __humidity_put_parser = reqparse.RequestParser()
    __humidity_put_parser.add_argument("humidity", type=float, case_sensitive=False, required=True)

    def __transform_for_humidity(self, db_result):
        return self.transform_db_result(db_result, ReadingType.HUMIDITY)

    def __is_valid_humidity(self, value):
        if not isinstance(value, float):
            return False
        return 0 <= value <= 1

    def get(self):
        logging.debug('GET /humidity')
        try:
            db_result = get_last_humidity()
            return _response_success(self.__transform_for_humidity(db_result))
        except Exception as err:
            logging.error(err)
            return _response_error()

    def put(self):
        request_args = self.__humidity_put_parser.parse_args()
        logging.debug(f'PUT /humidity with args: {request_args}')
        if not self.__is_valid_humidity(request_args['humidity']):
            return _response_error(400, 'Humidity must be expressed as a percentage i.e. 0 <= x <= 1')
        try:
            save_humidity(request_args['humidity'])
            return _response_success()
        except Exception as err:
            logging.error(err)
            return _response_error()
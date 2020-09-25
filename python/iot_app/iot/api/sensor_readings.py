from iot_app.logger.logger import get_logger
from iot_app.config import secrets
from iot_app.db.sensor_readings import save_temp, get_last_temp, save_humidity, get_last_humidity
from iot_app.iot.api import make_api_key_validator, response_success, response_error

from flask_restful import Resource, reqparse
from bson.objectid import ObjectId

logging = get_logger(__name__)
_api_secrets = secrets['api']


class ReadingType:
    TEMPERATURE = 'temp'
    HUMIDITY = 'humidity'


class SensorReadingResource(Resource):

    @staticmethod
    def transform_db_result(db_result, reading_type):
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

    method_decorators = [make_api_key_validator(_api_secrets['SENSORS_API_KEY'])]


class TemperatureResource(SensorReadingResource):
    __temp_put_parser = reqparse.RequestParser()
    __temp_put_parser.add_argument("temp", type=int, case_sensitive=False, required=True)

    def __transform_for_temperature(self, db_result):
        return self.transform_db_result(db_result, ReadingType.TEMPERATURE)

    def get(self):
        logging.debug('GET /temperature')
        try:
            db_result = get_last_temp()
            return response_success(self.__transform_for_temperature(db_result))
        except Exception as err:
            logging.error(err)
            return response_error()

    def put(self):
        request_args = self.__temp_put_parser.parse_args()
        logging.debug(f'PUT /temperature with args: {request_args}')
        try:
            save_temp(request_args['temp'])
            return response_success()
        except Exception as err:
            logging.error(err)
            return response_error()


class HumidityResource(SensorReadingResource):
    __humidity_put_parser = reqparse.RequestParser()
    __humidity_put_parser.add_argument("humidity", type=float, case_sensitive=False, required=True)

    def __transform_for_humidity(self, db_result):
        return self.transform_db_result(db_result, ReadingType.HUMIDITY)

    @staticmethod
    def __is_valid_humidity(value):
        if not isinstance(value, float):
            return False
        return 0 <= value <= 1

    def get(self):
        logging.debug('GET /humidity')
        try:
            db_result = get_last_humidity()
            return response_success(self.__transform_for_humidity(db_result))
        except Exception as err:
            logging.error(err)
            return response_error()

    def put(self):
        request_args = self.__humidity_put_parser.parse_args()
        logging.debug(f'PUT /humidity with args: {request_args}')
        if not self.__is_valid_humidity(request_args['humidity']):
            return response_error(400, 'Humidity must be expressed as a percentage i.e. 0 <= x <= 1')
        try:
            save_humidity(request_args['humidity'])
            return response_success()
        except Exception as err:
            logging.error(err)
            return response_error()

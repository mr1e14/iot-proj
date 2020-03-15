from flask import Blueprint, request, jsonify, current_app as app
from iot_app.logger.logger import get_logger


logging = get_logger(__name__)
sensor_readings = Blueprint('sensors', __name__, url_prefix="/sensors")

_data = {'temp': None, 'humidity': None}

class SensorReadingException(Exception):
    
    def __init__(self, error_message, error_code):
        self.message = error_message
        self.code = error_code

@sensor_readings.route('/iot', methods=['POST'])
def handle_readings():
    json_data = request.get_json()
    logging.debug(f"/iot: {json_data}")
    
    api_key = json_data.get('API_KEY')
    if api_key != app.config['SENSORS_API_KEY']:
        raise SensorReadingException('Invalid API key', 401)

    temp = json_data.get('temp')
    humidity = json_data.get('humidity')

    if temp is not None:
        _data['temp'] = temp
    if humidity is not None:
        _data['humidity'] = humidity
    if temp is humidity is None:
        raise SensorReadingException('Invalid request', 400)
    return 'OK', 200

@sensor_readings.route('/read')
@sensor_readings.route('/read/<key>')
def read_data(key=None):
    logging.debug(f"/read: {key}")

    if key is not None:
        try:
            return jsonify({key: _data[key]})
        except KeyError:
            raise SensorReadingException(f"Invalid key: '{key}'", 400)
    return jsonify(_data)
 
@sensor_readings.errorhandler(Exception)
def handle_errors(e):
    logging.error(e, exc_info=True)
    if isinstance(e, SensorReadingException):
        return jsonify({"error_message": e.message, "error_code": e.code}), e.code
    return jsonify({"error_message": "Application error", "error_code": 500}), 500


def get_data():
    return _data
 
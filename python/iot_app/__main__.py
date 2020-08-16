from os.path import dirname, join, abspath
from flask import Flask, request
from flask_restful import Api
from flask_ask import Ask
from iot_app.logger.logger import get_logger
from iot_app.iot import TemperatureResource, HumidityResource, LightResource, LightsDiscoveryResource, LightEffectResource

import iot_app.alexa as alexa

logging = get_logger(__name__)

app = Flask(__name__)
ask = Ask(app, '/alexa')
api = Api(app)

api.add_resource(TemperatureResource, '/iot/temperature')
api.add_resource(HumidityResource, '/iot/humidity')
api.add_resource(LightResource, '/iot/lights/<string:_id>')
api.add_resource(LightEffectResource, '/iot/lights/<string:_id>/effect')
api.add_resource(LightsDiscoveryResource, '/iot/lights')


@ask.launch
def launch():
    return alexa.welcome()


@ask.intent('SensorReading', mapping={'sensor': 'SensorType'})
def sensor_reading(sensor):
    return alexa.sensor_readings(sensor)


@ask.intent('EffectIntent', mapping={'room': 'Room', 'effect': "EffectType"})
def start_effect(room, effect):
    return alexa.start_effect(room, effect)


@ask.intent('StopEffectIntent', mapping={'room': 'Room'})
def stop_lights(room):
    return alexa.stop_effect(room)

    
@app.route('/')
def homepage():
    return '200'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


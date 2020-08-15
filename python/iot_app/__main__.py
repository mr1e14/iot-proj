from os.path import dirname, join, abspath
from flask import Flask, request
from flask_restful import Api
from flask_ask import Ask
#from iot_app.alexa.alexa import  welcome, climate_info, start_disco, stop_flow, start_fade, stop_fade
from iot_app.assets.web_assets import pi_img
from iot_app.logger.logger import get_logger
from iot_app.iot import TemperatureResource, HumidityResource, LightResource, LightsDiscoveryResource, LightEffectResource

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
    return welcome()


@ask.intent('SensorReading', mapping={'sensor': 'SensorType'})
def climate(sensor):
    return climate_info(sensor)


@ask.intent('DiscoLightsIntent', mapping={'room': 'Room'})
def disco_lights(room):
    return start_disco(room)


@ask.intent('StopFlowIntent', mapping={'room': 'Room'})
def stop_lights(room):
    return stop_flow(room)

    
@app.route('/')
def homepage():
    return '200'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


from os.path import dirname, join, abspath
from flask import Flask, request
from flask_restful import Api
from flask_ask import Ask
#from iot_app.alexa.alexa import  welcome, climate_info, start_disco, stop_flow, start_fade, stop_fade
from iot_app.alexa.alexa import IOT_ENV # temporary solution
from iot_app.assets.web_assets import pi_img
from iot_app.logger.logger import get_logger
from iot_app.iot import TemperatureResource, HumidityResource

logging = get_logger(__name__)

app = Flask(__name__)
ask = Ask(app, '/alexa')
api = Api(app)

api.add_resource(TemperatureResource, '/iot/temperature')
api.add_resource(HumidityResource, '/iot/humidity')


@ask.launch
def launch():
    return welcome()


@ask.intent('ClimateIntent', mapping={'prop': 'Property', 'warmth': 'Warmth'})
def climate(prop, warmth):
    return climate_info(prop, warmth)


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


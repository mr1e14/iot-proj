from os.path import dirname, join, abspath
from flask import Flask, request
from flask_ask import Ask
#from iot_app.alexa.alexa import  welcome, climate_info, start_disco, stop_flow, start_fade, stop_fade
from iot_app.alexa.alexa import IOT_ENV # temporary solution
from iot_app.assets.web_assets import pi_img
from iot_app.logger.logger import get_logger
from iot_app.iot import sensor_readings

logging = get_logger(__name__)

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('iot_app.instance.config.DevConfig')
app.register_blueprint(sensor_readings)

ask = Ask(app, '/alexa')


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


@ask.intent('FadeIntent', mapping={'room': 'Room', 'duration': 'Duration', 'off': 'Off'})
def fade_lights(room, duration, off):
    return start_fade(room, duration, off)


@ask.intent('StopFadeIntent', mapping={'room': 'Room'})
def stop_fade_lights(room):
    return stop_fade(room)


@app.route('/register', methods=['POST'])
def register_client():
    if request.form.get("id") in app.config['CLIENTS']:
        return app.config['POST_TOKEN']
    return '403', 403
    
@app.route('/')
def homepage():
    return '200'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


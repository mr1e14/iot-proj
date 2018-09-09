import logging
from os.path import dirname, join, abspath
from flask import Flask, request
from flask_ask import Ask
from alexa import  welcome, climate_info, start_disco, stop_flow
from alexa import IOT_ENV # temporary solution

app_dir = dirname(__file__)
logs_dir = join(app_dir, 'logs')


app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile(abspath(join(app_dir, 'instance/config.py')))
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


@app.route('/register', methods=['POST'])
def register_client():
    if request.form.get("id") in app.config['CLIENTS']:
        return app.config['POST_TOKEN']
    return '403', 403


@app.route('/read', methods=['GET'])
def read_environment():
    key = request.args.get('key')
    if key is not None:
        try:
            return str(IOT_ENV[key])
        except KeyError:
            return 'invalid_key'
    return str(IOT_ENV)


@app.route('/iot', methods=['POST'])
def iot_handler():
    token = request.form.get('token')

    if token != app.config['POST_TOKEN']:
        return '403', 403

    temp = request.form.get('temp')
    humidity = request.form.get('humidity')

    if temp is not None:
        IOT_ENV['temp'] = temp

    if humidity is not None:
        IOT_ENV['humidity'] = humidity

    if temp is humidity is None:
        return 'invalid_message'

    return "200"


@app.route('/')
def homepage():
    return '200'


if __name__ == '__main__':
    app.run(host='0.0.0.0')


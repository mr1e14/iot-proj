import logging
from os.path import dirname, join, abspath
from flask import Flask, request, render_template
from flask_ask import Ask, statement, question
from web_assets import pi_img

app_dir = dirname(__file__)
logs_dir = join(app_dir, 'logs')

logging.basicConfig(filename=join(logs_dir, 'requests.log'), format='%(asctime)s %(message)s')
logging.getLogger('flask_ask').setLevel(logging.DEBUG)

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile(abspath(join(app_dir,'instance/config.py')))
ask = Ask(app, '/alexa')

IOT_ENV = {"temp": None, "humidity": None}


@ask.launch
def launch():
    card_title = render_template('card_title')
    question_text = render_template('welcome')
    return question(question_text).standard_card(card_title, question_text, pi_img)


@ask.intent('EnvIntent', mapping={'prop': 'Property', 'warmth': 'Warmth'})
def env(prop, warmth):
    card_title = render_template('card_title')

    if warmth is prop is None:
        answer = render_template('temp_and_humidity').format(IOT_ENV['temp'], IOT_ENV['humidity'])
        return statement(answer).standard_card(card_title, answer, pi_img)

    if warmth is not None:
        answer = render_template('temp') % IOT_ENV["temp"]
        return statement(answer).standard_card(card_title, answer, pi_img)

    if prop == 'humidity':
        answer = render_template('humidity') % IOT_ENV["humidity"]
    else:
        # it's only temp or humidity at the moment
        answer = render_template('temp') % IOT_ENV["temp"]

    return statement(answer).standard_card(card_title, answer, pi_img)


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


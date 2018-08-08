from flask import Flask, request
import os

app = Flask(__name__, instance_relative_config=True)

IOT_ENV = {"temp": 1, "humidity": 55}


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
    temp = request.form.get('temp')
    humidity = request.form.get('humidity')

    if temp is not None:
        IOT_ENV['temp'] = temp

    if humidity is not None:
        IOT_ENV['humidity'] = humidity

    if temp is humidity is None:
        return 'invalid_message'

    return "success"


@app.route('/')
def homepage():
    return 'This is homepage'


if __name__ == '__main__':
    app.run(debug=True)
    app.secret_key = os.urandom(24)

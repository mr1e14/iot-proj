from flask import Flask, request

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')

IOT_ENV = {"temp": 1, "humidity": 55}


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


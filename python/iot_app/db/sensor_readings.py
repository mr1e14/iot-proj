from iot_app.db import DatabaseManager, handle_mongo_error
from iot_app.logger import get_logger

logging = get_logger(__name__)

""" Collection object where temperature readings are stored"""
temperature = DatabaseManager.get_collection('temp_sensor')
""" Collection of humidity sensor readings """
humidity = DatabaseManager.get_collection('humidity_sensor')


@handle_mongo_error
def get_last_temp():
    logging.debug("Getting last temperature")
    return temperature.find_one({}, sort=[('$natural', -1)])


@handle_mongo_error
def save_temp(value):
    logging.debug('Saving temperature')
    temperature.insert_one({'value': value})


@handle_mongo_error
def get_last_humidity():
    logging.debug("Getting last humidity")
    return humidity.find_one({}, sort=[('$natural', -1)])


@handle_mongo_error
def save_humidity(value):
    logging.debug('Saving humidity')
    humidity.insert_one({'value': value})
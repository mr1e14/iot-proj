from iot_app.db import DatabaseManager, handle_mongo_error
from iot_app.logger import get_logger

from marshmallow import Schema, fields, validate, ValidationError
from typing import Dict


logging = get_logger(__name__)

""" Lights collection object"""
_lights = DatabaseManager.get_collection('lights')


class ObjectIdField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ""
        return value


class LightSchema(Schema):
    _id = ObjectIdField(attribute=None, required=False)
    ip = fields.String(allow_none=False)
    name = fields.String()
    is_default = fields.Boolean(validate=validate.OneOf([True, False])) # prevent truthy / falsy


_schema = LightSchema()


@handle_mongo_error
def get_lights(**filters):
    logging.debug(f'Getting lights. Filters: {filters}')
    return _lights.find(filters)


@handle_mongo_error
def get_one_light(**filters):
    logging.debug(f'Getting one light. Filters: {filters}')
    return _lights.find_one(filters)


@handle_mongo_error
def save_light(data: Dict, **filters):
    logging.debug(f'Saving light. Data: {data}, Filters: {filters}')
    try:
        _schema.load(data)
    except ValidationError as err:
        logging.error(err)
        raise err
    _lights.update_one(filters, {'$set': data})


@handle_mongo_error
def save_new_light(data: Dict):
    logging.debug(f'Saving new light. Data: {data}')
    try:
        _schema.load(data)
    except ValidationError as err:
        logging.error(err)
        raise err
    _lights.insert_one(data)

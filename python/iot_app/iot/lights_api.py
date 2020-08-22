from iot_app.logger import get_logger
from iot_app.iot import make_api_key_validator, response_success, response_error
from iot_app.iot.lights import LightManager, Light, LightException
from iot_app.config import secrets

from flask_restful import Resource, reqparse
from typing import Dict

logging = get_logger(__name__)

lm = LightManager.instance()


def _exclude_none_values(d: Dict) -> Dict:
    return {k: v for k,v in d.items() if v is not None}


def _find_or_abort(_id: str) -> Light:
    light = lm.get_light_by_id(_id)
    if light is None:
        response_error(404, f"No light with ID: {_id}")
    return light


class LightResource(Resource):
    method_decorators = [make_api_key_validator(secrets['LIGHTS_API_KEY'])]

    __light_put_parser = reqparse.RequestParser()
    __light_put_parser.add_argument('name', type=str)
    __light_put_parser.add_argument('is_default', type=bool)
    __light_put_parser.add_argument('color', type=str)
    __light_put_parser.add_argument('brightness', type=int)
    __light_put_parser.add_argument('on', type=bool)

    def get(self, _id):
        logging.info(f'GET /light for ID: {_id}')
        light = _find_or_abort(_id)
        data = light.dump_props()
        return response_success(data)

    def put(self, _id):
        request_args = _exclude_none_values(self.__light_put_parser.parse_args(strict=True))
        logging.info(f'PUT /light for ID: {_id}, args: {request_args}')

        light = _find_or_abort(_id)

        if not light.is_connected:
            if not all(prop in Light.db_props for prop in request_args.keys()):
                response_error(404, 'Light is not currently connected')
        try:
            for prop, value in request_args.items():
                setattr(light, prop, value)
            return response_success()
        except (ValueError, LightException) as err:
            logging.error(err)
            response_error(400, str(err))


class LightsDiscoveryResource(Resource):
    method_decorators = [make_api_key_validator(secrets['LIGHTS_API_KEY'])]

    light_manager = LightManager.instance()

    def get(self):
        logging.info('GET /lights')
        data = [light.dump_props() for light in self.light_manager.get_all_lights()]
        return response_success(data)


class LightEffectResource(Resource):
    method_decorators = [make_api_key_validator(secrets['LIGHTS_API_KEY'])]

    light_manager = LightManager.instance()

    __light_effect_put_parser = reqparse.RequestParser()
    __light_effect_put_parser.add_argument('effect_name', type=str, required=True)
    __light_effect_put_parser.add_argument('effect_props', type=dict)

    def put(self, _id):
        request_args = _exclude_none_values(self.__light_effect_put_parser.parse_args(strict=True))
        logging.info(f'PUT /light/effect for ID: {_id}, args: {request_args}')

        light = _find_or_abort(_id)

        if not light.is_connected:
            response_error(404, 'Light is not currently connected')
        effect_name = request_args.get('effect_name')
        if effect_name not in Light.effects_map.keys() and effect_name is not None:
            response_error(404, f'Invalid effect name: {effect_name}')
        try:
            light.set_effect(effect_name, request_args.get('effect_props', {}))
            return response_success()
        except (ValueError, LightException) as err:
            logging.error(err)
            response_error(400, str(err))

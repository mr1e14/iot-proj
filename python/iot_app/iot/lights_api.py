from iot_app.logger import get_logger
from iot_app.iot import make_api_key_validator, response_success, response_error
from iot_app.iot.lights import LightManager, Light
from iot_app.config import config

from flask_restful import Resource, reqparse, fields

from typing import Dict

logging = get_logger(__name__)


def _exclude_none_values(d: Dict) -> Dict:
    return {k: v for k,v in d.items() if v is not None}

def get_lights_by_id(light_manager: LightManager):
    lights_by_id = {}
    for light in light_manager.get_all_lights():
        lights_by_id[str(light.id)] = light
    return lights_by_id

class LightResource(Resource):
    method_decorators = [make_api_key_validator(config['LIGHTS_API_KEY'])]

    light_manager = LightManager.instance()

    __light_put_parser = reqparse.RequestParser()
    __light_put_parser.add_argument('name', type=str)
    __light_put_parser.add_argument('is_default', type=bool)
    __light_put_parser.add_argument('color', type=str)
    __light_put_parser.add_argument('brightness', type=int)
    __light_put_parser.add_argument('on', type=bool)


    def get(self, _id):
        lights_by_id = get_lights_by_id(self.light_manager)
        logging.info(f'GET /light for ID: {_id}')
        if _id not in lights_by_id.keys():
            response_error(404, f'No light with ID: {_id}')
        light = lights_by_id[_id]
        data = light.dump_props()
        return response_success(data)


    def put(self, _id):
        lights_by_id = get_lights_by_id(self.light_manager)
        request_args = _exclude_none_values(self.__light_put_parser.parse_args(strict=True))
        logging.info(f'PUT /light for ID: {_id}, args: {request_args}')

        if _id not in lights_by_id.keys():
            response_error(404, f"No light with ID: {_id}")
        
        light = lights_by_id[_id]
        if not light.is_connected:
            if not all(prop in Light.db_props for prop in request_args.keys()):
                response_error(404, 'Light is not currently connected')
        try:
            for prop, value in request_args.items():
                setattr(light, prop, value)
            return response_success()
        except ValueError as err:
            logging.error(err)
            response_error(400, str(err))

class LightsDiscoveryResource(Resource):
    method_decorators = [make_api_key_validator(config['LIGHTS_API_KEY'])]

    light_manager = LightManager.instance()

    def get(self):
        logging.info('GET /lights')
        data = [light.dump_props() for light in self.light_manager.get_all_lights()]
        return response_success(data)
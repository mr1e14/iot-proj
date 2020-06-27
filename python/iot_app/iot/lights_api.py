from iot_app.logger import get_logger
from iot_app.iot import make_api_key_validator, response_success, response_error
from iot_app.iot.lights import LightManager, Light
from iot_app.config import config

from flask_restful import Resource, reqparse, fields

from typing import Dict

logging = get_logger(__name__)


def _exclude_none_values(d: Dict) -> Dict:
    return {k: v for k,v in d.items() if v is not None}

class LightResource(Resource):
    method_decorators = [make_api_key_validator(config['LIGHTS_API_KEY'])]

    db_props = ('name', 'is_default')
    bulb_props = ('on', 'brightness', 'color', 'is_flowing')

    __light_put_parser = reqparse.RequestParser()
    __light_put_parser.add_argument('name', type=str)
    __light_put_parser.add_argument('is_default', type=bool)
    __light_put_parser.add_argument('color', type=str)
    __light_put_parser.add_argument('brightness', type=int)
    __light_put_parser.add_argument('on', type=bool)

    light_manager = LightManager.instance()

    lights_by_id = {}
    for light in light_manager.get_all_lights():
        lights_by_id[str(light.id)] = light

    def is_refresh_required(self, is_connected: bool, last_refresh: int) -> bool:
        if not is_connected:
            return False
        if last_refresh is None:
            return True
        refresh_after = 30 # seconds
        return last_refresh > refresh_after


    def get(self, _id):
        logging.info(f'GET /lights for ID: {_id}')
        if _id not in self.lights_by_id.keys():
            response_error(404, f'No light with ID: {_id}')
        light = self.lights_by_id[_id]
        if self.is_refresh_required(light.is_connected, light.last_refresh_in_seconds()):
            logging.debug(f'Refreshing light props as last refresh was {light.last_refresh_in_seconds}s ago')
            light.refresh_props()
        data = light.dump_props()
        return response_success(data)


    def put(self, _id):
        request_args = _exclude_none_values(self.__light_put_parser.parse_args(strict=True))
        logging.info(f'PUT /lights for ID: {_id}, args: {request_args}')

        if _id not in self.lights_by_id.keys():
            response_error(404, f"No light with ID: {_id}")
        
        light = self.lights_by_id[_id]
        if not light.is_connected:
            if not all(prop in self.db_props for prop in request_args.keys()):
                response_error(404, 'Light is not currently connected')
        try:
            for prop, value in request_args.items():
                setattr(light, prop, value)
            return response_success()
        except ValueError as err:
            logging.error(err)
            response_error(400, str(err))

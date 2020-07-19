import yaml
import os

_config_path = os.path.join(os.getcwd(), 'iot_app', 'config', 'config.yaml')
config = yaml.safe_load(open(config_path))
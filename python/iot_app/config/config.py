import yaml
import os

_config_path = os.path.join(os.getcwd(), 'iot_app', 'config', 'config.yaml')
config = yaml.safe_load(open(_config_path))

_secrets_path = os.path.join(os.getcwd(), 'iot_app', 'config', 'secrets.yaml')
secrets = yaml.safe_load(open(_secrets_path))
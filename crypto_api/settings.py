import pathlib
import yaml

BASE_DIR = pathlib.Path(__file__).parent.parent
API_KEY_LENGTH = 64
PRIVATE_KEY_LENGTH = 64
WEI = 10 ** 18

DEBUG_MODE = False

config_path = BASE_DIR / 'config' / 'crypto_api_settings.yaml'


def get_config(path):
    with open(path) as config_file:
        _config = yaml.safe_load(config_file)
    return _config


config = get_config(config_path)

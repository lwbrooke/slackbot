import logging
import os
import sys

import click
import yaml

from .configuration import config
from .utils import merge_many_dicts


def set_up_logging(level=None):
    level = level or logging.INFO
    handlers = [logging.StreamHandler()]
    log_format = '%(asctime)s:%(levelname)s\t:%(name)s:%(message)s'
    logging.basicConfig(level=level, handlers=handlers, format=log_format)


def load_configs(env, config_dir=None):
    config_dir = config_dir or \
        os.path.join(
            os.getenv('XDG_CONFIG_HOME', os.path.join(os.getenv('HOME'), '.config')),
            'fangorn')

    try:
        with open(os.path.join(config_dir, 'default.yaml')) as default_in, \
                open(os.path.join(config_dir, '{}.yaml'.format(env))) as env_in, \
                open(os.path.join(config_dir, 'secret.yaml')) as secret_in:
            default_config = yaml.load(default_in)
            env_config = yaml.load(env_in)
            secret_config = yaml.load(secret_in)
    except FileNotFoundError:
        click.echo('No configuration files found at: {}'.format(config_dir))
        sys.exit(1)

    config.update(merge_many_dicts(default_config, env_config, secret_config))

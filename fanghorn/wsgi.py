import click

from .main import get_app
from .utils import path_type


@click.command()
@click.option('--local', 'env', flag_value='local', default=True, show_default=True, help='Run with dev configs.')
@click.option('--prod', 'env', flag_value='prod', help='Run with prod configs.')
@click.option('--config-dir', type=path_type, help='Explicit configuration directory to use.')
def main(env, config_dir):
    global app
    app = get_app(env, config_dir)


main(standalone_mode=False)

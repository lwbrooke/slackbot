import os
import pathlib
import pkg_resources
import shutil

import click

from .server import get_app
from .utils import path_type


@click.group()
def main():
    """Entry point for fanghorn."""
    pass


@main.command('dev-server')
@click.option('--local', 'env', flag_value='local', default=True, show_default=True, help='Run with dev configs.')
@click.option('--prod', 'env', flag_value='prod', help='Run with prod configs.')
@click.option('--config-dir', type=path_type, help='Explicit configuration directory to use.')
@click.option('-h', '--hostname', default='127.0.0.1', show_default=True, help='Host for the server.')
@click.option('-p', '--port', default=8080, show_default=True, help='Port for the server.')
@click.option('-d', '--debugger', is_flag=True, help='Start server with debugger.')
@click.option('-r', '--reloader', is_flag=True, help='Start server with hot reloader.')
def dev_server(hostname, port, reloader, debugger, env):
    """
    Run the development server.

    Run the development server with the provided options. Requires the
    development dependencies to be installed to work.
    """
    app = get_app(env)
    try:
        from werkzeug.serving import run_simple
    except ImportError:
        click.secho('Development dependencies not installed!', fg='red', err=True)
        raise click.Abort()
    else:
        run_simple(hostname, port, app, use_reloader=reloader, use_debugger=debugger)


@main.command('create-configs')
@click.option('--config-dir', type=path_type, help='Explicit configuration directory to use.')
def create_configs(config_dir):
    """Copy the template config files into a usable location."""
    config_dir = config_dir or \
        os.path.join(
            os.getenv('XDG_CONFIG_HOME', os.path.join(os.getenv('HOME'), '.config')),
            'fanghorn')

    os.makedirs(config_dir, exist_ok=True)

    config_files = pathlib.Path(pkg_resources.resource_filename('fanghorn', 'config_files')).glob('*.yaml')
    with click.progressbar(config_files, label='copying files') as config_files:
        for f in config_files:
            shutil.copy(str(f), config_dir)


@main.command()
@click.argument('origin')
@click.argument('destination')
def traffic(origin, destination):
    """"""
    self._slack = slackclient.SlackClient(config['slack']['bot_user']['token'])


if __name__ == '__main__':
    main()

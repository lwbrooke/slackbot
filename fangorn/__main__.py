import datetime
import os
import pathlib
import pkg_resources
import shutil
import time

import click
import requests
import slackclient

from . import init
from .configuration import config
from .google_maps_wrapper import TrafficMapper
from .server import get_app
from .utils import path_type, FloatRange


@click.group()
def main():
    """Entry point for fangorn."""
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
            'fangorn')

    os.makedirs(config_dir, exist_ok=True)

    config_files = pathlib.Path(pkg_resources.resource_filename('fangorn', 'config_files')).glob('*.yaml')
    with click.progressbar(config_files, label='copying files') as config_files:
        for f in config_files:
            shutil.copy(str(f), config_dir)


@main.command('ping-site')
@click.option('--local', 'env', flag_value='local', default=True, show_default=True, help='Run with dev configs.')
@click.option('--prod', 'env', flag_value='prod', help='Run with prod configs.')
@click.option('--config-dir', type=path_type, help='Explicit configuration directory to use.')
@click.option('--slack-channel', default='#general', help='Channel to post message in.')
@click.option('-d', '--duration', default=1, type=click.IntRange(1, 60), help='Time in minutes to ping site for.')
@click.option('-s', '--sleep-time', default=15, type=click.IntRange(1, 600), help='Time in seconds between pings.')
@click.argument('url')
def ping_site(env, config_dir, slack_channel, duration, sleep_time, url):
    """."""
    init.load_configs(env, config_dir)
    init.set_up_logging()
    slack = slackclient.SlackClient(config['slack']['bot_user']['token'])

    session = requests.Session()

    start = time.time()
    while time.time() - start < duration * 60:
        response = session.get(url)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            slack.api_call(
                'chat.postMessage',
                channel=slack_channel,
                as_user=True,
                text='<!channel> {} is returning a bad response.'.format(url),
                attachments=[{
                    'text': 'Status Code: {}'.format(response.status_code),
                    'color': 'danger'
                }])
        time.sleep(sleep_time)


@main.command()
@click.option('--local', 'env', flag_value='local', default=True, show_default=True, help='Run with dev configs.')
@click.option('--prod', 'env', flag_value='prod', help='Run with prod configs.')
@click.option('--weekdays', 'days', flag_value={0, 1, 2, 3, 4}, help='Only run on weekdays.')
@click.option('--all-days', 'days', flag_value=set(range(7)), default=True, show_default=True, help='Run every day.')
@click.option('--weekends', 'days', flag_value={5, 6}, help='Only run on weekends.')
@click.option('--config-dir', type=path_type, help='Explicit configuration directory to use.')
@click.option('--slack-channel', default='#general', help='Channel to post message in.')
@click.option('-i', '--interval', type=FloatRange(min=0), default=0, help='Time in minutes to wait between posts.')
@click.option('-n', '--number-of-posts', type=click.IntRange(min=1), default=1, help='Number of posts to make.')
@click.argument('origin')
@click.argument('destination')
def traffic(env, days, config_dir, slack_channel, interval, number_of_posts, origin, destination):
    """
    Post traffic maps for the provided ORIGIN and DESTINATION to slack.

    Post traffic maps for the provided ORIGIN and DESTINATION to slack. Post a
    given number of iterations while waiting some amount of time between posts.
    Aliases may be used for ORIGIN or DESTINATION, or fully addresses.
    (e.g. "work" or "home")
    """
    if interval < 0:
        click.secho('', fg='red', err=True)
        raise click.Abort()

    if datetime.datetime.utcnow().weekday() not in days:
        click.echo('Today is not a selected run day. Exiting')
        return

    init.load_configs(env, config_dir)
    init.set_up_logging()
    slack = slackclient.SlackClient(config['slack']['bot_user']['token'])
    mapper = TrafficMapper()

    location_aliases = config['google']['location_aliases']
    origin = location_aliases.get(origin, origin)
    destination = location_aliases.get(destination, destination)

    for i in range(number_of_posts):
        duration, distance, image_name = mapper.get_map(origin, destination)
        slack_message = mapper.as_slack_message(
            origin, destination, duration, distance, image_name)
        slack.api_call(
            'chat.postMessage',
            channel=slack_channel,
            as_user=True,
            **slack_message)

        if i != number_of_posts - 1:
            time.sleep(interval * 60)


if __name__ == '__main__':
    main()

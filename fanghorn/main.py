from .message_router import SlackMessageRouter
from . import init
from falcon_cors import CORS
import falcon


def get_app(env):
    config = init.load_configs(env)
    app = _build_app(config)
    return app


def _build_app(config):
    cors = CORS(**config['cors'])

    app = falcon.API(middleware=[cors.middleware])

    app.req_options.auto_parse_form_urlencoded = True

    app.add_route('/api/messagerouter/{channel}',
                  SlackMessageRouter(config['slack']))

    return app

from .message_router import SlackMessageRouter
from . import init
from falcon_cors import CORS
import falcon


def get_app(env):
    config = init.load_configs(env)
    print(config)
    app = _build_app(config)
    return app


def _build_app(config):
    cors = CORS(**config.get('cors'))

    app = falcon.API(middleware=[cors.middleware])

    app.add_route('/api/messagerouter', SlackMessageRouter())

    return app

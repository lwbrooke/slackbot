from . import init
from .configuration import config
from .message_router import SlackMessageRouter
from .records import TinnitusRecorder
from .traffic import TrafficPoster
from falcon_cors import CORS
import falcon


def get_app(env, config_dir=None):
    init.load_configs(env, config_dir)
    init.set_up_logging()
    app = _build_app()
    return app


def _build_app():
    cors = CORS(**config['cors'])

    app = falcon.API(middleware=[cors.middleware])

    app.req_options.auto_parse_form_urlencoded = True

    app.add_route('/api/messagerouter', SlackMessageRouter())
    app.add_route('/api/traffic', TrafficPoster())
    app.add_route('/api/records/tinnitus', TinnitusRecorder())

    return app

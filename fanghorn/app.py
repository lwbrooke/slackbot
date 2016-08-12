from .message_router import SlackMessageRouter
from falcon_cors import CORS
import falcon


def get_app():
    cors = CORS(allow_all_origins=True)

    app = falcon.API(middleware=[cors.middleware])

    app.add_route('/api/slack/messagerouter', SlackMessageRouter())

    return app

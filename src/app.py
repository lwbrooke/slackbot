from .message_router import SlackMessageRouter
import falcon


def get_app():
    app = falcon.API()

    app.add_route('/api/slack/messagerouter', SlackMessageRouter())

    return app

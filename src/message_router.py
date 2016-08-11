import falcon
import json


class SlackMessageRouter:
    def on_post(self, req, resp):
        resp.body = json.dumps({'message': 'hello, world!'})
        resp.status = falcon.HTTP_200

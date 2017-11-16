import json

import falcon


class HealthCheck:
    def on_get(self, req, resp):
        resp.body = json.dumps({'status': 'happy and health!'})
        resp.status = falcon.HTTP_200

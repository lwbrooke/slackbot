import collections
import falcon
import marshmallow
import slackclient


class SlackMessageRouter:
    def __init__(self, config):
        self._slack = slackclient.SlackClient(config['api_token'])

        webhooks = config['webhooks']
        self._schema = WebhookDataSchema({w['token'] for w
                                          in webhooks.values()})
        self._matchers = {k: tuple(Matcher(m) for m in w.get('matchers', ()))
                          for k, w in webhooks.items()}
        self._channels = {k: w['channel'] for k, w in webhooks.items()}

    def on_post(self, req, resp, channel):
        data, err = self._schema.load(req.params)
        if err:
            resp.status = falcon.HTTP_400
            return

        if any(m(data.text) for m in self._matchers[channel]):
            self._slack.api_call(
                'chat.postMessage',
                channel=self._channels[channel],
                text='This looks interesting...',
                attachments=[{'text': data.text}],
                as_user=True)

        resp.status = falcon.HTTP_200


WebhookData = collections.namedtuple('WebhookData', ('token', 'text'))


class WebhookDataSchema(marshmallow.Schema):
    token = marshmallow.fields.String(required=True)
    text = marshmallow.fields.String(required=True)

    def __init__(self, webhook_tokens):
        super().__init__()
        self._tokens = webhook_tokens

    @marshmallow.validates('token')
    def _matches_token(self, value):
        if value not in self._tokens:
            raise marshmallow.ValidationError('invalid token')

    @marshmallow.post_load
    def _post_load(self, data):
        return WebhookData(**data)


class Matcher:
    def __init__(self, matcher):
        self._matcher = matcher

    def __call__(self, text):
        return self._matcher in text

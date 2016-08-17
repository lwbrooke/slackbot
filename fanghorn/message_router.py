from collections import namedtuple
import falcon
import marshmallow
import slackclient


class SlackMessageRouter:
    def __init__(self, config):
        self._slack = slackclient.SlackClient(config['bot_user']['token'])

        webhook = config['outgoing_webhook']
        self._schema = WebhookDataSchema(webhook['token'],
                                         set(webhook['matchers'].keys()))
        self._matchers = {user_name: Matcher(spec) for
                          user_name, spec in webhook['matchers'].items()}

    def on_post(self, req, resp):
        data, err = self._schema.load(req.params)
        if err:
            resp.status = falcon.HTTP_400
            return

        matcher = self._matchers[data.user_name]
        if matcher(data):
            self._slack.api_call(
                'chat.postMessage',
                channel=matcher.channel,
                text='This looks interesting...',
                attachments=[{'text': data.text}],
                as_user=True)

        resp.status = falcon.HTTP_200


WebhookData = namedtuple('WebhookData', ('token', 'text', 'user_name'))


class WebhookDataSchema(marshmallow.Schema):
    token = marshmallow.fields.String(required=True)
    text = marshmallow.fields.String(required=True)
    user_name = marshmallow.fields.String(required=True)

    def __init__(self, webhook_token, user_names):
        super().__init__()
        self._token = webhook_token
        self._user_names = user_names

    @marshmallow.validates('user_name')
    def _matches_user_name(self, value):
        if value not in self._user_names:
            raise marshmallow.ValidationError('invalid user name')

    @marshmallow.validates('token')
    def _matches_token(self, value):
        if value != self._token:
            raise marshmallow.ValidationError('invalid token')

    @marshmallow.post_load
    def _post_load(self, data):
        return WebhookData(**data)


class Matcher:
    def __init__(self, spec):
        self._text_contains = spec['text_contains']
        self._output_channel = spec['output_channel']

    def __call__(self, data):
        return any(t in data.text for t in self._text_contains)

    @property
    def channel(self):
        return self._output_channel

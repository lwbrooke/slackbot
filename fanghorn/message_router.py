from collections import namedtuple
import falcon
import marshmallow
import slackclient
import logging


class SlackMessageRouter:
    def __init__(self, config):
        self._slack = slackclient.SlackClient(config['bot_user']['token'])

        webhook = config['outgoing_webhook']
        self._schema = WebhookDataSchema(webhook['token'],
                                         set(webhook['matchers'].keys()))
        self._matchers = {user_name: Matcher(spec) for
                          user_name, spec in webhook['matchers'].items()}

    def on_post(self, req, resp):
        h = '\n'.join('\t{}: {}'.format(k, v) for k, v in req.headers.items())
        p = '\n'.join('\t{}: {}'.format(k, v) for k, v in req.params.items())
        logging.info('\nheaders: \n%s\nparams: \n%s', h, p)

        data, err = self._schema.load(req.params)
        if err:
            logging.info('%s %s', data, err)
            logging.info('valid user names %s',
                         ' '.join(self._matchers.keys()))
            resp.status = falcon.HTTP_400
            return

        matcher = self._matchers[data.user_name]
        if matcher(data):
            self._slack.api_call(
                'chat.postMessage',
                channel=matcher.channel,
                text='<!channel>: This looks interesting...',
                attachments=[{'text': data.text}],
                as_user=True)

        resp.status = falcon.HTTP_200


WebhookData = namedtuple('WebhookData', ('token', 'text', 'user_name'))


class WebhookDataSchema(marshmallow.Schema):
    token = marshmallow.fields.String(required=True)
    text = marshmallow.fields.String(required=True)
    user_name = marshmallow.fields.String(required=True)
    bot_name = marshmallow.fields.String()

    def __init__(self, webhook_token, user_names):
        super().__init__()
        self._token = webhook_token
        self._user_names = user_names

    @marshmallow.validates_schema
    def _matches_user_name_or_bot_name(self, data):
        if data.get('user_name') not in self._user_names or \
                data.get('bot_name') not in self._user_names:
            raise marshmallow.ValidationError('invalid user/bot name')

    @marshmallow.validates('token')
    def _matches_token(self, value):
        if value != self._token:
            raise marshmallow.ValidationError('invalid token')

    @marshmallow.post_load
    def _post_load(self, data):
        if 'bot_name' in data:
            data['user_name'] = data['bot_name']
            del data['bot_name']
        return WebhookData(**data)


class Matcher:
    def __init__(self, spec):
        self._text_contains = spec['text_contains']
        self._output_channel = spec['output_channel']

    def __call__(self, data):
        lowered = data.text.lower()
        return any(t in lowered for t in self._text_contains)

    @property
    def channel(self):
        return self._output_channel

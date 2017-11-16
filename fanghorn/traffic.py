from collections import namedtuple
import json

import falcon
import marshmallow

from .configuration import config
from .google_maps_wrapper import TrafficMapper


class TrafficPoster:
    def __init__(self):
        self._schema = SlashCommandDataSchema(config['slack']['traffic_command']['token'],
                                              config['google']['location_aliases'])
        self._mapper = TrafficMapper()

    def on_post(self, req, resp):
        data, err = self._schema.load(req.params)
        if err:
            resp.body = json.dumps(err)
            resp.status = falcon.HTTP_400
            return

        origin = data.text['from']
        destination = data.text['to']
        duration, distance, image_name = self._mapper.get_map(origin, destination)

        slack_message = self._mapper.as_slack_message(origin, destination, duration, image_name)
        slack_message.update(response_type='in_channel')
        resp.body = json.dumps(slack_message)
        resp.status = falcon.HTTP_200


CommandData = namedtuple('CommandData', ('text', 'command', 'response_url', 'token'))


class SlashCommandDataSchema(marshmallow.Schema):
    command = marshmallow.fields.String(required=True)
    token = marshmallow.fields.String(required=True)
    text = marshmallow.fields.Method(deserialize='_parse_text', required=True)
    response_url = marshmallow.fields.Url(required=True)

    def __init__(self, command_token, location_aliases):
        super().__init__()
        self._token = command_token
        self._locations = location_aliases

    @marshmallow.validates('token')
    def _matches_token(self, value):
        if value != self._token:
            raise marshmallow.ValidationError('invalid token')

    def _parse_text(self, text):
        tokens = text.strip().split()
        from_index, to_index = None, None
        for index, token in enumerate(tokens):
            if token == 'from:' and from_index is None:
                from_index = index
            elif token == 'to:' and to_index is None:
                to_index = index
            if from_index is not None and to_index is not None:
                break

        if from_index is None or to_index is None:
            raise marshmallow.ValidationError('"{}" is an invalid command'.format(text))

        from_location = ' '.join(tokens[from_index + 1:len(tokens) if from_index > to_index else to_index])
        to_location = ' '.join(tokens[to_index + 1:len(tokens) if to_index > from_index else from_index])

        if not from_location or not to_location:
            raise marshmallow.ValidationError('"{}" is an invalid command'.format(text))

        return {
            'from': self._locations[from_location] if from_location in self._locations else from_location,
            'to': self._locations[to_location] if to_location in self._locations else to_location
        }

    @marshmallow.post_load
    def _post_load(self, data):
        return CommandData(**data)

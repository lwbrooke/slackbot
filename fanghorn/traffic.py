from .configuration import config
from collections import namedtuple
import falcon
import googlemaps
import json
import marshmallow
import requests
import slackclient
import time

_MODE = 'driving'
_LANGUAGE = 'en'
_UNITS = 'imperial'
_TRAFFIC_MODEL = 'best_guess'
_DEPARTURE_TIME = 'now'


class TrafficPoster:
    def __init__(self):
        self._schema = SlashCommandDataSchema(config['slack']['traffic_command']['token'],
                                              config['google']['location_aliases'])

        self._slack = slackclient.SlackClient(config['slack']['bot_user']['token'])

        self._gmaps = googlemaps.Client(key=config['google']['directions']['key'])

        static_map_config = config['google']['static_map']
        self._path_format = static_map_config['path_format']
        self._marker_format = static_map_config['marker_format']
        self._url = static_map_config['url_base']

        self._session = requests.Session()
        self._session.stream = True
        self._session.params = {
            'size': '{}x{}'.format(static_map_config['size']['width'], static_map_config['size']['height']),
            'key': static_map_config['key']
        }

    def on_post(self, req, resp):
        data, err = self._schema.load(req.params)
        if err:
            resp.body = json.dumps(err)
            resp.status = falcon.HTTP_400
            return
        directions_response = self._gmaps.directions(
            origin=data.text['from'], destination=data.text['to'], mode=_MODE, language=_LANGUAGE,
            units=_UNITS, traffic_model=_TRAFFIC_MODEL, departure_time=_DEPARTURE_TIME)
        polyline = directions_response[0]['overview_polyline']['points']

        map_response = self._session.get(self._url, params={
            'path': self._path_format.format(polyline),
            'markers': (self._marker_format.format('A', data.text['from']),
                        self._marker_format.format('B', data.text['to']))
        })

        upload_response = self._slack.api_call(
            'files.upload',
            file=map_response.raw,
            filename='{}.png'.format(time.time()))
        print(upload_response)

        resp.body = json.dumps({
            'text': 'Here are the traffic conditions between {} and {}'.format(data.text['from'], data.text['to']),
            'attachments': [
                {
                    'title': 'Travel time',
                    'text': directions_response[0]['legs'][0]['duration']['text']
                },
                {
                    'title': 'Distance',
                    'text': directions_response[0]['legs'][0]['distance']['text']
                },
                {
                    'title': 'Route',
                    'image_url': upload_response['file']['url_private']
                }
            ]
        })
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

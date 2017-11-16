import hashlib
import os

import googlemaps
import requests

from .configuration import config

_MODE = 'driving'
_LANGUAGE = 'en'
_UNITS = 'imperial'
_TRAFFIC_MODEL = 'best_guess'
_DEPARTURE_TIME = 'now'


class TrafficMapper:
    def __init__(self):
        self._gmaps = googlemaps.Client(key=config['google']['directions']['key'])

        self._image_directory = config['google']['static_map']['image_directory']

        static_map_config = config['google']['static_map']
        self._image_format = config['google']['static_map']['url_format']
        self._marker_format = static_map_config['marker_format']
        self._path_format = static_map_config['path_format']
        self._url = static_map_config['url_base']

        self._session = requests.Session()
        self._session.params = {
            'size': '{}x{}'.format(static_map_config['size']['width'], static_map_config['size']['height']),
            'key': static_map_config['key']
        }

    def get_map(self, origin, destination):
        directions_response = self._gmaps.directions(
            origin=origin,
            destination=destination,
            mode=_MODE,
            language=_LANGUAGE,
            units=_UNITS,
            traffic_model=_TRAFFIC_MODEL,
            departure_time=_DEPARTURE_TIME)
        polyline = directions_response[0]['overview_polyline']['points']

        map_response = self._session.get(self._url, params={
            'path': self._path_format.format(polyline),
            'markers': (self._marker_format.format('A', origin),
                        self._marker_format.format('B', destination))
        })
        fname = '{}.png'.format(hashlib.md5(map_response.content).hexdigest())
        with open(os.path.join(os.path.expanduser(self._image_directory), fname), 'wb') as fout:
            fout.write(map_response.content)

        return (
            directions_response[0]['legs'][0]['duration_in_traffic']['text'],
            directions_response[0]['legs'][0]['distance']['text'],
            fname
        )

    def as_slack_message(self, origin, destination, duration, distance, image_name):
        return {
            'text': 'Here are the traffic conditions between {} and {}'.format(origin, destination),
            'attachments': [
                {
                    'fields': [

                        {
                            'title': 'Duration',
                            'value': duration,
                            'short': True
                        },
                        {
                            'title': 'Distance',
                            'value': distance,
                            'short': True
                        }
                    ],
                    'image_url': self._image_format.format(image_name)
                }
            ]
        }

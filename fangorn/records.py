from .configuration import config
from collections import namedtuple
from datetime import datetime, timezone
from os.path import expanduser
import falcon
import json
import marshmallow


class TinnitusRecorder:
    def __init__(self):
        self._schema = SlashCommandDataSchema(config['slack']['tinnitus_command']['token'])
        self._record_writer = TinnitusWriter(config['records']['tinnitus']['path'])

    def on_post(self, req, resp):
        data, err = self._schema.load(req.params)
        if err:
            resp.body = json.dumps({
                'text': 'invalid command format: {}'.format(req.params['text']),
                'attachments': [
                    {
                        'text': json.dumps(err)
                    }
                ],
                'response_type': 'ephemeral'
            })
            resp.status = falcon.HTTP_OK
            return

        record = {**data.text, **{'recorded_time': datetime.now(timezone.utc).isoformat()}}
        self._record_writer.write_record(record)

        resp.body = json.dumps({
            'text': 'record successfuly written\near: {ear}\naudibility: {audibility}\ndecibels: {decibels}'.format(**data.text),
            'response_type': 'ephemeral'
        })
        resp.status = falcon.HTTP_OK


CommandData = namedtuple('CommandData', ('text', 'command', 'response_url', 'token'))


class SlashCommandDataSchema(marshmallow.Schema):
    command = marshmallow.fields.String(required=True)
    token = marshmallow.fields.String(required=True)
    text = marshmallow.fields.Method(deserialize='_parse_text', required=True)
    response_url = marshmallow.fields.Url(required=True)

    def __init__(self, command_token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._token = command_token

    @marshmallow.validates('token')
    def _matches_token(self, value):
        if value != self._token:
            raise marshmallow.ValidationError('invalid token')

    def _parse_text(self, text):
        text = text.strip()

        if len(text) < 3 or len(text) > 5:
            raise marshmallow.ValidationError('text must be 4 to 6 characters')

        i = iter(text)
        ear = next(i).lower()
        audibility = next(i)
        decibels = ''.join(i)

        errors = []
        if ear != 'l' and ear != 'r':
            errors.append('l or r are the only valid ear choices.')

        try:
            audibility = int(audibility)
            if audibility < 0 or audibility > 2:
                errors.append('audibility must be between 0 and 2.')
        except ValueError:
            errors.append('audibility must be an integer.')

        try:
            decibels = int(decibels)
            if decibels < 0 or decibels > 200:
                errors.append('decibels must be between 0 and 200.')
        except ValueError:
            errors.append('decibels must be an integer.')

        if errors:
            raise marshmallow.ValidationError(' '.join(errors))

        return {
            'ear': ear,
            'audibility': audibility,
            'decibels': decibels
        }

    @marshmallow.post_load
    def _post_load(self, data):
        return CommandData(**data)


class TinnitusWriter:
    def __init__(self, record_file_path):
        self._path = expanduser(record_file_path)

    def write_record(self, record):
        with open(self._path, 'a') as f_out:
            f_out.write(json.dumps(record) + '\n')

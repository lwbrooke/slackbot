import click


def merge_many_dicts(*configs):
    config = {}

    for c in configs:
        config = merge_dicts(config, c)

    return config


def merge_dicts(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        for k, v in b.items():
            if k not in a:
                a[k] = v
            else:
                a[k] = merge_dicts(a[k], v)
    return a


path_type = click.Path(file_okay=False, exists=True, resolve_path=True)


class FloatRange(click.ParamType):
    name = 'float'

    def __init__(self, min=None, max=None, clamp=False):
        if min is not None and max is not None and min > max:
            raise ValueError('min {} must be less than or equal to max {}'.format(min, max))

        self._min = min
        self._max = max
        self._clamp = clamp

    def convert(self, value, param, ctx):
        try:
            value = float(value)
        except ValueError:
            self.fail('{} is not a valid float'.format(value), param, ctx)

        if self._clamp:
            value = max(value, self._min) if self._min is not None else value
            value = min(value, self._max) if self._max is not None else value
        else:
            if self._min is not None and value < self._min:
                self.fail('{} must be greater than or equal to {}'.format(value, self._min), param, ctx)
            if self._max is not None and value > self._max:
                self.fail('{} must be less than or equal to {}'.format(value, self._max), param, ctx)

        return value

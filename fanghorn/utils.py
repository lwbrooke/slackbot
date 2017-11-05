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

import yaml


def load_configs(env):
    with open('config/default.yaml') as default_in, \
            open('config/{}.yaml'.format(env)) as env_in, \
            open('config/secret.yaml') as secret_in:
        default_config = yaml.load(default_in)
        env_config = yaml.load(env_in)
        secret_config = yaml.load(secret_in)

    return _merge_configs(default_config, env_config, secret_config)


def _merge_configs(*configs):
    config = {}

    for c in configs:
        config = _merge_pair(config, c)

    return config


def _merge_pair(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        for k, v in b.items():
            if k not in a:
                a[k] = v
            else:
                a[k] = _merge_pair(a[k], v)
    return a

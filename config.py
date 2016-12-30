import yaml


def load(filename='config.yml'):
    return yaml.load(open(filename))

import json

class NoWSEncoder(json.JSONEncoder):
    '''Subclass to eliminate whitespace in the resulting JSON'''
    def __init__(self, **kwargs):
        kwargs['separators'] = (',', ':')
        kwargs['ensure_ascii'] = False
        super().__init__(**kwargs)

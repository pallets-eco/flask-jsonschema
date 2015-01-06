# -*- coding: utf-8 -*-
"""
    flask_jsonschema
    ~~~~~~~~~~~~~~~~

    flask_jsonschema
"""

import os

from functools import wraps
import jsonschema
from jsonschema import ValidationError

try:
    import simplejson as json
except ImportError:
    import json

from flask import current_app, request


class DefaultSchemaLoader(object):
    def __init__(self, app):
        default_dir = os.path.join(app.root_path, 'jsonschema')
        schema_dir = app.config.get('JSONSCHEMA_DIR', default_dir)

        schemas = {}
        self._schema_dir = schema_dir
        for fn in os.listdir(schema_dir):
            key = fn.split('.')[0]
            fn = os.path.join(schema_dir, fn)
            if os.path.isdir(fn) or not fn.endswith('.json'):
                continue
            with open(fn) as f:
                schemas[key] = json.load(f)

        self._schemas = schemas

    def get_schema_dir(self):
        return self._schema_dir

    def get_schema(self, path):
        rv = self._schemas[path[0]]
        for p in path[1:]:
            rv = rv[p]
        return rv

    def validate(self, path, data):
        schema = self.get_schema(path)
        jsonschema.validate(schema, data)

class PrmdSchemaLoader(DefaultSchemaLoader):
    def __init__(self, app):
        with open(app.config.get('JSONSCHEMA_SCHEMA')) as f:
            self._schema = json.load(f)

    def get_schema(self):
        return self._schema

    def get_schemata(self, path):
        schemata = self._schema['definitions'][path[0]]
        rel = path[1]
        for link in schemata['links']:
            if link['rel'] == rel:
                return link['schema']

    def validate(self, path, data):
        schemata = self.get_schemata(path)
        resolver = jsonschema.RefResolver.from_schema(self._schema)
        jsonschema.Draft4Validator(schemata, resolver=resolver).validate(data)


class JsonSchema(object):
    def __init__(self, app=None, loader_class=None):
        self.app = app
        if app is not None:
            self._state = self.init_app(app, loader_class)

    def init_app(self, app, loader_class=None):
        loader_class = loader_class or DefaultSchemaLoader

        state = loader_class(app)
        app.extensions['jsonschema'] = state
        return state

    def __getattr__(self, name):
        return getattr(self._state, name, None)

def validate_schema(*schema_path):
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            current_app.extensions['jsonschema'].validate(
                    schema_path, request.json)
            return fn(*args, **kwargs)
        return decorated
    return wrapper

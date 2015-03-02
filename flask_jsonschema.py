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

from flask import current_app, request, g, after_this_request


class DefaultSchemaLoader(object):
    def __init__(self, app, format_checker_class=None):
        self._load_schema(app)
        self.format_checker = format_checker_class()

    def _load_schema(self, app):
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

    def validate_response(self, path, data):
        pass # no response data here

    def validate(self, path, data):
        schema = self.get_schema(path)
        jsonschema.validate(schema, data, format_checker=self.format_checker)

class PrmdSchemaLoader(DefaultSchemaLoader):

    def _load_schema(self, app):
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

    def get_target_schemata(self, path):
        schemata = self._schema['definitions'][path[0]]
        rel = path[1]
        for link in schemata['links']:
            if link['rel'] == rel:
                return link['targetSchema']

    def validate_response(self, path, data):
        schemata = self.get_target_schemata(path)
        resolver = jsonschema.RefResolver.from_schema(self._schema)
        jsonschema.Draft4Validator(
                schemata,
                resolver=resolver,
                format_checker=self.format_checker).validate(data)

    def validate(self, path, data):
        schemata = self.get_schemata(path)
        resolver = jsonschema.RefResolver.from_schema(self._schema)
        jsonschema.Draft4Validator(
                schemata,
                resolver=resolver,
                format_checker=self.format_checker).validate(data)


class JsonSchema(object):
    def __init__(self, app=None, loader_class=None, format_checker_class=None):
        self.app = app
        if app is not None:
            self._state = self.init_app(app, loader_class, format_checker_class)

    def init_app(self, app, loader_class=None, format_checker_class=None):
        loader_class = loader_class or DefaultSchemaLoader

        state = loader_class(app, format_checker_class)
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
            if (current_app.config['JSONSCHEMA_VALIDATE_RESPONSES']):
                @after_this_request
                def post_validation(response):
                   response_json = json.loads(response.get_data())
                   current_app.extensions['jsonschema'].validate_response(
                           schema_path, response_json)
                   return response

            return fn(*args, **kwargs)
        return decorated
    return wrapper

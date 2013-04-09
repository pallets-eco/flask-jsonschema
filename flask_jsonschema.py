# -*- coding: utf-8 -*-
"""
    flask_jsonschema
    ~~~~~~~~~~~~~~~~

    flask_jsonschema
"""

import os

from functools import wraps

try:
    import simplejson as json
except ImportError:
    import json

from flask import current_app, request
from jsonschema import ValidationError, validate


class _JsonSchema(object):
    def __init__(self, schemas):
        self._schemas = schemas

    def get_schema(self, path):
        rv = self._schemas[path[0]]
        for p in path[1:]:
            rv = rv[p]
        return rv


class JsonSchema(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self._state = self.init_app(app)

    def init_app(self, app):
        default_dir = os.path.join(app.root_path, 'jsonschema')
        schema_dir = app.config.get('JSONSCHEMA_DIR', default_dir)
        schemas = {}
        for fn in os.listdir(schema_dir):
            key = fn.split('.')[0]
            fn = os.path.join(schema_dir, fn)
            if os.path.isdir(fn) or not fn.endswith('.json'):
                continue
            with open(fn) as f:
                schemas[key] = json.load(f)
        state = _JsonSchema(schemas)
        app.extensions['jsonschema'] = state
        return state

    def validate(self, *path):
        def wrapper(fn):
            @wraps(fn)
            def decorated(*args, **kwargs):
                schema = current_app.extensions['jsonschema'].get_schema(path)
                validate(request.json, schema)
                return fn(*args, **kwargs)
            return decorated
        return wrapper

    def __getattr__(self, name):
        return getattr(self._state, name, None)

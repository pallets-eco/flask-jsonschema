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
from jsonschema.validators import validator_for


class _JsonSchema(object):
    def __init__(self, schemas):
        self._schemas = schemas

    def get_schema(self, path):
        rv = self._schemas[path[0]]
        for p in path[1:]:
            rv = rv[p]
        return rv


class ValidationError(Exception):
    def __init__(self, message,  schema_errors, *args, **kwargs):
        super(ValidationError, self).__init__(message, *args, **kwargs)
        self.schema_errors = schema_errors


class JsonSchema(object):
    def __init__(self, app=None, format_checker=None):
        self.app = app
        self.format_checker = format_checker
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
                validator_class = validator_for(schema)
                validator = validator_class(schema, format_checker=self.format_checker)
                errors = list(validator.iter_errors(request.json))
                if errors:
                    raise ValidationError('Error validation request against schema', errors)
                return fn(*args, **kwargs)
            return decorated
        return wrapper

    def __getattr__(self, name):
        return getattr(self._state, name, None)

"""
Flask-JsonSchema
----------

A Flask extension for validating JSON requets with jsonschema

"""
from setuptools import setup


setup(
    name='Flask-JsonSchema',
    version='0.2.0',
    url='https://github.com/mattupstate/flask-jsonschema',
    license='MIT',
    author='Matt Wright',
    author_email='matt@nobien.net',
    description='Flask extension for validating JSON requets',
    long_description=__doc__,
    py_modules=['flask_jsonschema'],
    test_suite='nose.collector',
    zip_safe=False,
    platforms='any',
    install_requires=['Flask>=0.9', 'jsonschema>=1.1.0'],
    tests_require=['nose'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

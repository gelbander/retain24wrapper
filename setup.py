
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import retain24wrapper

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='retain24wrapper',
    version=retain24wrapper.__version__,
    packages=['retain24wrapper'],
    url='https://github.com/retain24wrapper/retain24wrapper',
    author=retain24wrapper.__author__,
    author_email='gustaf@dynamo.mobi',
    classifiers=(
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ),
    description='A wrapper for Retain24 webservice api.',
    install_requires=required
)

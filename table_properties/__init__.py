# pylint: disable=missing-docstring, invalid-name

try:
    from . import db, utils, generator
except ImportError as iex:
    print(iex)
    print("Please run 'pip install -r requirements.txt'")
    exit(1)

database = db
utils = utils
generator = generator

PROG_NAME = "table-properties"
PROG_VERSION = 0.3

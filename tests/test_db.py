# pylint: disable=missing-docstring, invalid-name, no-self-use
import pytest

import table_properties.db as db


# pylint: disable=too-few-public-methods
class TestDb():
    def test_default_database(self):
        d = db.Db()
        assert d is not None, "No parameter Db() instance should be created"
        assert d.check_connection()

    def test_convert_value(self):
        d = db.Db()
        assert d.convert_value(1.0) == 1.0
        assert d.convert_value(1) == 1
        assert d.convert_value("1") == 1
        assert d.convert_value("2.0") == 2.0
        assert d.convert_value("test") == "test"
        assert d.convert_value([1, 2]) == [1, 2]

    def test_bad_host(self):
        with pytest.raises(Exception):
            d = db.Db(db.ConnectionParams(host="127.0.0.2"))
            d.check_connection()


class TestConnectionParams():
    def test_defaults(self):
        cp = db.ConnectionParams()
        assert cp.host == [db.DEFAULT_HOST]
        assert cp.port == db.DEFAULT_NATIVE_CQL_PORT
        assert cp.auth_provider is None
        assert not cp.is_ssl_required
        assert cp.ssl_context is None

    def test_username_password_update(self):
        cp = db.ConnectionParams()
        assert cp.auth_provider is None
        cp.username = "cassandra"
        assert cp.username == "cassandra"
        assert cp.auth_provider is None
        cp.password = "cassandra"
        assert cp.password == "cassandra"
        assert cp.auth_provider is not None

    def test_security_context(self):
        cp = db.ConnectionParams()
        assert cp.ssl_context is None
        cp.is_ssl_required = True
        assert cp.ssl_context is not None

    def test_load_rc(self):
        cp = db.ConnectionParams.load_from_rcfile("tests/setup/cqlshrc")
        assert cp is not None
        assert isinstance(cp, db.ConnectionParams)

    def test_load_nonexisting_rc(self):
        with pytest.raises(Exception):
            db.ConnectionParams.load_from_rcfile("tests/setup/cqlshrc1234")

# pylint: disable=missing-docstring, invalid-name, broad-except
import pytest
import yaml

import table_properties.db as db


@pytest.fixture(scope="session")
def current_config():
    """ Injects current config data into tests

        Test if a local Cassandra instance is available for testing. If not
        use mock data to run tests.
    """
    conn_params = db.get_connection_settings()

    if db.check_connection(conn_params):
        try:
            with open("./tests/setup/cql/drop_excalibur.cql", "r") as f:
                stmt = f.read()
            db.exec_stmt(connection=conn_params, cmd_stmt=stmt)

            with open("./tests/setup/cql/create_excalibur.cql", "r") as f:
                stmt = f.read()
            db.exec_stmt(connection=conn_params, cmd_stmt=stmt)

            return db.get_current_config(conn_params, True)
        except Exception:
            pass

    # Load the mock config
    with open("./tests/mocks/excalibur.yaml", "r") as f:
        return yaml.safe_load(f)


def pytest_sessionfinish():
    conn_params = db.get_connection_settings()

    # teardown
    if db.check_connection(conn_params):
        try:
            with open("./tests/setup/cql/drop_excalibur.cql", "r") as f:
                stmt = f.read()
            db.exec_stmt(connection=conn_params, cmd_stmt=stmt)
        except Exception:
            pass

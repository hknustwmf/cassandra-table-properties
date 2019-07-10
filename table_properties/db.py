# pylint: disable=too-many-arguments, too-many-branches, too-many-locals
""" Database interface
"""
import logging
import ssl

import cassandra
import cassandra.auth
import cassandra.cluster
import cassandra.query
import cassandra.util
import cassandra.policies

from table_properties import utils


def get_protocol_version(proto_version: int):
    """Return protocol version
    """
    version_dict = {
        "1": cassandra.ProtocolVersion.V1,
        "2": cassandra.ProtocolVersion.V2,
        "3": cassandra.ProtocolVersion.V3,
        "4": cassandra.ProtocolVersion.V4,
        "5": cassandra.ProtocolVersion.V5
    }
    return version_dict.get(proto_version, cassandra.ProtocolVersion.V2)


def get_connection_settings(
        contact: str = None,
        port: int = None,
        protocol_version=None,
        username: str = None,
        password: str = None,
        use_tls: bool = False,
        client_cert_file: str = None,
        client_key_file: str = None,
        rc_config_file: str = None):
    """Construct connection settings dictionary.
    Args:
        contact:          IP address or hostname
        port:             port number
        protocol_version: protocol version number
        username:         user name
        password:         password
        use_tls:          flag whether to use encrypted connection
        client_cert_file: location of client certificate
        client_key_file:  location of client key
        rc_config_file:   rcconfig filename
    Returns:
        Connection settings dictionary.
    """
    params = dict()
    conf_username = None
    conf_password = None

    # Use cqlshrc values if present
    if rc_config_file:
        rc_config = utils.load_rconfig(rc_config_file)
        if rc_config["connection"]["hostname"]:
            params["contact"] = rc_config["connection"]["hostname"]

        if rc_config["connection"]["port"]:
            try:
                params["port"] = int(rc_config["connection"]["port"])
            except ValueError:
                pass

        if rc_config["connection"]["ssl"]:
            # use_tls is false by default. Override if defined in rc
            use_tls = rc_config["connection"]["ssl"]

        conf_username = rc_config["authentication"]["username"]
        conf_password = rc_config["authentication"]["password"]

    if contact:
        params["contact"] = contact
        params["load_balancing_policy"] = \
            cassandra.policies.WhiteListRoundRobinPolicy([contact])

    if isinstance(port, int):
        params["port"] = port

    if protocol_version:
        params["protocol_version"] = protocol_version

    if (conf_username or username) and (conf_password or password):
        conn_user = username if username else conf_username
        conn_pwrd = password if password else conf_password

        params["auth_provider"] = \
            cassandra.auth.PlainTextAuthProvider(conn_user, conn_pwrd)

        if not protocol_version:
            # Auth provider requires at least protocol version 2
            params["protocol_version"] = cassandra.ProtocolVersion.V2
        else:
            params["protocol_version"] = get_protocol_version(protocol_version)

    if use_tls:
        if client_cert_file and client_key_file:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            ssl_context.load_cert_chain(
                certfile=client_cert_file,
                keyfile=client_key_file)
            params["ssl_context"] = ssl_context
        else:
            params["ssl_context"] = ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return params


def get_class_name(full_class_name: str) -> str:
    """Return actual class name

    Args:
        full_class_name: Full Java class including namespace

    Examples:
        >>> cls="org.apache.cassandra.locator.NetworkTopologyStrategy"
        >>> print(table_properties.db.get_class_name(cls))
        NetworkTopologyStrategy

    Returns:
        Actual class name
    """
    return full_class_name.split(".")[-1]


def convert_value(val: any) -> any:
    """Convert a string to a number

    Args:
        val: Value expression to be converted

    Returns:
        Either the original value or an integer or float
    """
    if not isinstance(val, str):
        return val

    try:
        num_int = int(val)
        return num_int
    except ValueError:
        pass

    try:
        num_float = float(val)
        return num_float
    except ValueError:
        pass

    return val


def key_mapper(orig_key) -> str:
    """ Return the id field name

    Args:
        orig_key: Original key name

    Returns:
        The mapped key name or key name itself
    """
    mapping = {"keyspace_name": "name", "table_name": "name"}

    return mapping.get(orig_key, orig_key)


def get_replication_settings(replication: dict) -> dict:
    """Return mapping with replication settings

    Args:
        replication: Mapping properties in dictionary

    Returns:
        Dictionary with converted replication properties.
    """
    if not isinstance(replication, cassandra.util.OrderedMapSerializedKey):
        return {}

    repl_config = dict()
    data_centers = list()
    for key in replication.keys():
        if key == "class":
            repl_config["class"] = get_class_name(replication["class"])
        elif key == "replication_factor":
            repl_config["replication_factor"] = \
                convert_value(replication["replication_factor"])
        else:
            # data center name
            data_centers.append({
                "name": key,
                "replication_factor": convert_value(replication[key])
            })
    repl_config["data_centers"] = data_centers

    return repl_config


def convert_mapped_props(subconfig):
    """Convert mapped properties

    Args:
        subconfig: Mapping properties

    Returns:
        Dictionary with converted object properties
    """
    if not isinstance(subconfig, cassandra.util.OrderedMapSerializedKey):
        return {}

    settings = dict()
    for key, value in subconfig.items():
        if key == "class":
            value = get_class_name(value)

        settings[key] = convert_value(value)

    return settings


def get_cluster(connection_settings: dict) -> cassandra.cluster.Cluster:
    """Create and return a cluster instance.

    Args:
        connection_settings: Settings dictionary
    Returns:
        Cluster instance
    """

    cluster = cassandra.cluster.Cluster([connection_settings.get("contact", "127.0.0.1")])

    if connection_settings:
        if connection_settings.get("port", 0) > 0:
            cluster.port = connection_settings.get("port")
        if connection_settings.get("load_balancing_policy"):
            cluster.load_balancing_policy = \
                connection_settings.get("load_balancing_policy")
        if connection_settings.get("auth_provider"):
            cluster.auth_provider = connection_settings.get("auth_provider")
        if connection_settings.get("ssl_context"):
            cluster.ssl_context = connection_settings.get("ssl_context")

    return cluster


def exec_query(connection: dict, query_stmt: str) -> list:
    """Execute Cassandra query

    Args:
        connection: connection paramters
        query_stmt: CQL query

    Returns:
        List of rows or empty list
    """
    try:
        cluster = get_cluster(connection)

        with cluster.connect("system_schema",
                             wait_for_all_pools=True) as session:
            session.row_factory = cassandra.query.ordered_dict_factory
            rows = session.execute(query_stmt)

            return rows.current_rows
    except (cassandra.cluster.NoHostAvailable) as ex:
        if hasattr(ex, "errors"):
            for err, obj in ex.errors.items():
                msg = "Host {} responded with '{}'".format(err, str(obj))
                if isinstance(obj, cassandra.cluster.ConnectionShutdown):
                    msg += " " if msg[-1] == "." else ". "
                    msg += "Is SSL/TLS required to connect to the host?"
                print(msg)
    except Exception as ex:
        logging.exception(ex)
        raise

    return []


def check_connection(connection: dict):
    """Test Cassandra connectivity

    Args:
        connection: connection paramters

    Returns:
        True if connection was successful. False otherwise
    """
    try:
        cluster = get_cluster(connection)

        with cluster.connect():
            return True
    except (cassandra.cluster.NoHostAvailable) as ex:
        if hasattr(ex, "errors"):
            for err, obj in ex.errors.items():
                msg = "Host {} responded with '{}'".format(err, str(obj))
                if isinstance(obj, cassandra.cluster.ConnectionShutdown):
                    msg += " " if msg[-1] == "." else ". "
                    msg += "Is SSL/TLS required to connect to the host?"
                print(msg)
    except Exception as ex:
        logging.exception(ex)
        raise

    return False


def get_keyspace_configs(connection: dict) -> dict:
    """Retrieve all keyspace properties.

    Args:
        connection: Connection parameters

    Returns:
        Dictionary with keyspace settings.
    """
    keyspace_configs = []

    rows = exec_query(connection, "SELECT * FROM keyspaces")
    for row in rows:
        ks_name = row.get("keyspace_name").lower()
        if ks_name == "system" or ks_name.startswith("system_"):
            continue

        keyspace = {}
        for key, val in row.items():
            mapped_key = key_mapper(key)
            if isinstance(val, cassandra.util.OrderedMapSerializedKey):
                val = convert_mapped_props(val)
            elif key == "flags":
                val = list(val) if isinstance(val, cassandra.util.SortedSet) \
                                else val
            keyspace[mapped_key] = val
        keyspace_configs.append(keyspace)

    return {"keyspaces": keyspace_configs}


def get_table_configs(connection: dict, keyspace_name: str,
                      drop_ids: bool) -> dict:
    """Retrieve table properties

    Args:
        connection:    Connection parameters in dictionary
        keyspace_name: Keyspace name

    Returns:
        Table properties in dictionary
    """
    table_configs = []

    query_stmt = "SELECT * FROM tables WHERE keyspace_name = '{}';" \
        .format(keyspace_name)

    rows = exec_query(connection, query_stmt)
    for row in rows:
        tbl = {}
        for key, val in row.items():
            if key == "keyspace_name" or (key == "id" and drop_ids):
                continue
            elif isinstance(val, cassandra.util.OrderedMapSerializedKey):
                val = convert_mapped_props(val)
            elif key == "flags":
                val = list(val) if isinstance(val, cassandra.util.SortedSet) \
                                else val
            elif key == "id":
                val = str(val)
            tbl[key_mapper(key)] = val

        table_configs.append(tbl)

    return table_configs


def get_current_config(connection: dict, drop_ids: bool = False) -> dict:
    """Retrieve the current config from the Cassandra instance.

    Args:
        connection: Connection parameters

    Returns:
        Dictionary with keyspace and table properties.
    """
    keyspaces = get_keyspace_configs(connection)

    for keyspace in keyspaces.get("keyspaces", []):
        keyspace["tables"] = get_table_configs(connection,
                                               keyspace.get("name"), drop_ids)

    return keyspaces


def main():
    """ Main function
    """
    local_connection = get_connection_settings()
    for keyspace in get_current_config(local_connection).get("keyspaces", []):
        print("\nKeyspace : {}".format(keyspace.get("name", "")))
        print("- durable_writes : {}".format(keyspace.get("name", "")))
        print("- Tables")
        for tbl in keyspace.get("tables", []):
            print("\t\t- {}".format(tbl.get("name")))

if __name__ == "__main__":
    main()

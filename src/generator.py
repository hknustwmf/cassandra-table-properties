# pylint: disable=missing-docstring
""" Functions to create ALTER statements
"""
import logging

from src import utils


def do_class_names_match(src_class: str, dst_class: str) -> bool:
    if src_class and dst_class:
        src_class_arr = src_class.split(".")
        dst_class_arr = dst_class.split(".")
        if len(src_class_arr) == len(dst_class_arr):
            return sorted(src_class_arr) == sorted(dst_class_arr)

        return src_class_arr[-1] == dst_class_arr[-1]
    if src_class or dst_class:
        # Only one class name was provided
        return False

    # Neither class names were provided
    return True


def compare_values(src: dict, dst: dict) -> list:
    """ Compare configuration properties

    Args:
        src: Current values
        dst: Desired values

    Returns:
        List of changed values
    """

    if not (isinstance(src, dict) and isinstance(dst, dict)):
        return []

    changed_values = []
    for k in dst.keys():
        # Skip name properties
        if k == "name":
            continue
        dst_value = dst.get(k)
        src_value = src.get(k, None)
        if src_value and isinstance(src_value, dict) and isinstance(
                dst_value, dict):
            src_class = src_value.pop("class", None)
            dst_class = dst_value.pop("class", None)
        else:
            src_class = None
            dst_class = None

        if src_value != dst_value or not do_class_names_match(
                src_class, dst_class):
            changed_values.append({"property": k, "desired": dst_value})

    return changed_values


def connect_statments(stmt: str, add_new_line: bool = False) -> str:
    """Helper function to connect partial CQL statements.

    Args:
        stmt:         Current CQL statement
        add_new_line: Flag if connecting statement should be on new line

    Returns:
        connection line
    """
    spacer = "\n" if add_new_line else " "
    return spacer + "WITH " if "WITH " not in stmt else spacer + "AND "


def generate_alter_keyspace_statement(keyspace_name: str,
                                      current_keyspace: dict,
                                      desired_keyspace: dict) -> str:
    """Create ALTER statements for keyspace changes.

    Args:
        keyspace_name:    Keyspace
        current_keyspace: Current keyspace properties
        desired_keyspace: Desired keyspace properties

    Returns:
        CQL statement with changed properties or empty string
    """

    changes = compare_values(current_keyspace, desired_keyspace)
    if not changes:
        return ""

    stmt = "ALTER KEYSPACE {}".format(keyspace_name)
    for change in changes:
        stmt += connect_statments(stmt)
        stmt += "{} = {}".format(change["property"], change["desired"])

    return stmt + ";\n"


def generate_alter_table_statement(keyspace_name: str, current_tables: dict,
                                   desired_tables: dict) -> str:
    """ Create ALTER statements for tables in keyspace

    Args:
        keyspace_name:  Keyspace name
        current_tables: Current table properties
        desired_tables: Desired table properties

    Returns:
        CQL statement with changed properties or empty string
    """
    tbl_stmts = ""
    for desired_table in desired_tables:
        tbl_name = desired_table.get("name", None)
        if not tbl_name:
            raise Exception("Missing table name in config")

        current_table = utils.find_by_value(current_tables, "name", tbl_name)

        if not current_table:
            logging.warning("Table '%s' does not exist. Skipping...", tbl_name)

        changes = compare_values(current_table, desired_table)
        if changes:
            tbl_stmt = "\nALTER TABLE {}.{}".format(keyspace_name, tbl_name)
            for change in changes:
                prop_name = change["property"]
                prop_value = change["desired"]
                if not prop_value or prop_name == "id":
                    continue
                tbl_stmt += connect_statments(tbl_stmt, True)
                if (isinstance(prop_value, dict) or
                        str(prop_value).isnumeric()):
                    param_templ = "{} = {}"
                else:
                    param_templ = "{} = '{}'"
                prop_change = param_templ.format(prop_name, prop_value)
                tbl_stmt += prop_change
            tbl_stmts += tbl_stmt + ";"

    return tbl_stmts if isinstance(tbl_stmts, str) and "WITH " in tbl_stmts \
        else ""


def generate_alter_statements(current_config: dict,
                              desired_config: dict) -> str:
    """ Create ALTER statements for tables and keyspaces

    Args:
        current_config: Current properties
        desired_config: Desired properties

    Returns:
        CQL statement with changed properties or empty string
    """
    current_keyspaces = current_config.get("keyspaces", [])
    desired_keyspaces = desired_config.get("keyspaces", [])

    stmt = ""

    for desired_keyspace in desired_keyspaces:
        ks_name = desired_keyspace.get("name", None)
        if not ks_name:
            logging.error("Invalid keyspace '%s' config. Missing 'name' key",
                          desired_keyspace)
            raise Exception("Invalid configuration data")

        current_keyspace = utils.find_by_value(current_keyspaces, "name",
                                               ks_name)
        if not current_keyspace:
            logging.warning(
                """Skipped keyspace '%s'. Not found in
                            current config. Add keyspace via DDL schema""",
                ks_name)
            continue

        current_tables = current_keyspace.pop("tables", {})
        desired_tables = desired_keyspace.pop("tables", {})

        stmt += generate_alter_keyspace_statement(ks_name, current_keyspace,
                                                  desired_keyspace)

        stmt += generate_alter_table_statement(ks_name, current_tables,
                                               desired_tables)

    return stmt

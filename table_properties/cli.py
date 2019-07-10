# pylint: disable=broad-except, dangerous-default-value, unused-import
""" CLI interface class
"""
import argparse
import logging
import os
import sys

import table_properties as tp


class TablePropertiesCli():
    """Command-line interface class
    """

    def __init__(self):
        self.args = None

    @staticmethod
    def get_arg_parser()->argparse.ArgumentParser:
        """Set up CLI arguments in parser

        Returns:
            argparse.ArgumentParser
        """
        msg = "Compare actual Cassandra keyspace and table properties to " \
              "desired properties defined in a YAML file and create ALTER " \
              "KEYSPACE and ALTER TABLE statements for properties that " \
              "differ."
        parser = argparse.ArgumentParser(prog=tp.PROG_NAME,
                                         description=msg,
                                         formatter_class=lambda prog:
                                         argparse.RawTextHelpFormatter(
                                             prog, width=120))

        parser.add_argument(metavar="<filename>",
                            nargs="?",
                            dest="config_filename",
                            help="Desired configuration YAML file")

        parser.add_argument("-c",
                            "--contactpoint",
                            metavar="<ip>",
                            dest="host_ip",
                            help="Host IP address or name."
                                 "Default: localhost",
                            required=False)

        parser.add_argument("-C",
                            "--clientcert",
                            metavar="<filename>",
                            dest="client_cert_file",
                            help="Client cert file name.",
                            required=False)

        parser.add_argument("-d",
                            "--dump",
                            metavar="<filename>",
                            dest="dump_file",
                            help="Dump current configuration settings to file",
                            required=False)

        parser.add_argument("-f", "--force",
                            dest="force_overwrite",
                            help="Overwrite dump file if it exists.",
                            action="store_true")

        parser.add_argument("-k",
                            "--clientkey",
                            metavar="<filename>",
                            dest="client_key_file",
                            help="Client key file name.",
                            required=False)

        parser.add_argument("-l",
                            "--log",
                            metavar="<filename>",
                            dest="log_file",
                            help="Log file name. "
                                 "Default: tp_YYYYMMDD-HHMMSS.log",
                            required=False)

        parser.add_argument("-p",
                            "--port",
                            type=int,
                            metavar="<port #>",
                            dest="host_port",
                            help="Port number. Default: 9042",
                            required=False)

        parser.add_argument("-o",
                            "--protocolversion",
                            type=int,
                            choices=range(1, 5),
                            default=2,
                            metavar="<protocol version>",
                            dest="protocol_version",
                            help="Cassandra driver protocol version (1-5)."
                                 "Default: 2",
                            required=False)

        parser.add_argument("-P",
                            "--password",
                            metavar="<password>",
                            dest="password",
                            help="Password for plain text authentication.",
                            required=False)

        parser.add_argument("-s", "--skiprc",
                            dest="skip_rc",
                            help="Ignore existing cqlshrc file. Default: true",
                            action="store_true")

        parser.add_argument("-r",
                            "--rcfile",
                            metavar="<filename>",
                            dest="rc_file",
                            help="cqlrc file name. "
                                 "Default: ~/.cassandra/cqlshrc",
                            required=False)

        parser.add_argument("-t", "--tls",
                            dest="use_tls",
                            help="Use TLS encryption for client server "
                                 "communication.",
                            action="store_true")

        parser.add_argument("-u",
                            "--username",
                            metavar="<user name>",
                            dest="username",
                            help="User name for plain text authentication.",
                            required=False)

        parser.add_argument("-v",
                            "--version",
                            action="version",
                            version="{} {}".format(tp.PROG_NAME,
                                                   tp.PROG_VERSION))

        # Set defaults
        parser.set_defaults(force_overwrite=False, use_tls=False,
                            skip_rc=True, rc_file="~/.cassandra/cqlshrc")

        return parser

    def execute(self, args: list = []) -> None:
        """Execute applicaton
        """
        config_filename = None

        # Load the desired configuration from file
        self.args = TablePropertiesCli.get_arg_parser().parse_args(args)

        # Modify root logger settings
        tp.utils.setup_logging(self.args.log_file)

        try:
            if self.args.dump_file or self.args.config_filename:
                rc_filename = self.args.rc_file if not self.args.skip_rc \
                    else None

                # Construct the connection parameters
                conn = tp.db.get_connection_settings(
                    contact=self.args.host_ip,
                    port=self.args.host_port,
                    protocol_version=self.args.protocol_version,
                    username=self.args.username,
                    password=self.args.password,
                    use_tls=self.args.use_tls,
                    client_cert_file=self.args.client_cert_file,
                    client_key_file=self.args.client_key_file,
                    rc_config_file=rc_filename
                    )

                # Read current configuration from database
                current_config = tp.db.get_current_config(conn)

                if self.args.dump_file:
                    try:
                        tp.utils.write_yaml(self.args.dump_file,
                                            current_config,
                                            self.args.force_overwrite)
                    except Exception as ex:
                        logging.exception(ex)

                if self.args.config_filename:
                    config_filename = self.args.config_filename
                    logging.info("Reading config from '%s'", config_filename)
                    desired_config = tp.utils.load_yaml(config_filename)

                    # Generate ALTER statements for Keyspaces and Tables
                    alter_statements = tp.generator. \
                        generate_alter_statements(current_config,
                                                  desired_config)

                    print(alter_statements)
            else:
                self.get_arg_parser().print_usage()
        except Exception as ex:
            logging.exception(ex)
            print(ex)


def main():
    """ Main function
    """
    tpc = TablePropertiesCli()
    tpc.execute(args=sys.argv[1:])

if __name__ == "__main__":
    main()

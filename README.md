# cassandra-table-properties

[![Build Status](https://travis-ci.com/hknustwmf/cassandra-table-properties.svg?branch=master)](https://travis-ci.com/hknustwmf/cassandra-table-properties)
[![codecov](https://codecov.io/gh/hknustwmf/cassandra-table-properties/branch/master/graph/badge.svg)](https://codecov.io/gh/hknustwmf/cassandra-table-properties)

Cassandra table and keyspace configuration tool.

## Overview/Motivation

Cassandra's DDL covers what is traditionally considered schema, but also information that is more configuration in nature. For example, consider keyspace creation:

### keyspace

```sql
CREATE KEYSPACE "globaldomain_T_mathoid__ng_mml" WITH replication = {'class': 'NetworkTopologyStrategy', 'codfw': '3', 'eqiad': '3'}  AND durable_writes = true;
-- \___________________________________________/      \________________________________________________________________________________________________________/
--                    |                                                                                   |
--                  schema                                                                          configuration
```

A keyspace in Cassandra is a namespace to associate tables with (similar to a database in MySQL terminology). Here, _globaldomain_T_mathoid__ng_mml_ is the keyspace, and everything that follows the WITH is configuration pertaining to associated tables (replication, or whether or not to make use of the commitlog).

It is similar with tables:

### table

```sql
-- Schema ~~~~~~~~~~~~~~~
CREATE TABLE "globaldomain_T_mathoid__ng_mml".data (
    "_domain" text,
    key text,
    headers text,
    tid timeuuid,
    value text,
    PRIMARY KEY (("_domain", key))
-- Configuration ~~~~~~~~
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy', 'max_threshold': '32', 'min_threshold': '4'}
    AND compression = {'chunk_length_in_kb': '32', 'class': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND crc_check_chance = 1.0
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 86400
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99PERCENTILE';
```

Likewise, the DDL describes both schema, and table-specific configuration. In the example above, _"globaldomain_T_mathoid__ng_mml".data_ is the table name, followed within the parenthesis by the names and types of the attributes. This is schema, as it models the data to be stored there. Everything that follows the WITH however, is configuration.

This is an important distinction (schema v configuration), because schema is determined by the application; No change in schema makes sense without a corresponding change to the application. Configuration however is site-specific, and operational in nature; Parameters can be unique to a use-case, and updated frequently outside of any change to the application. Schema is determined by application developers, configuration by users/operators.

---

Unfortunately, it is colloquial to refer to the entire DDL for a keyspace and/or table as _schema_.  However, every effort is made throughput this ticket to use the term _schema_ to mean only that which determines the data model, and _configuration_ to refer to the corresponding operational settings.

---

## Installation

Python 3.4 or higher is required. Install the dependencies with

```bash
pip install -r requirements.txt
```

## Usage

From the command prompt, execute below to get help on available options

```bash
table-properties -h
```

To write the current configuration as formatted YAML to stdout

```bash
table-properties -d
```

Once you have an existing configuration, you can make changes to that YAML file and use it as an input file.

```bash
table-properties <filename>
```

This generates ALTER statements if any differences between the configurations were detected. Use

```bash
table-properties <filename> | cqlsh
```

to update Cassandra's configuration.

### Changing Defaults and Using `cqlshrc`

If the server connection is different from the default values, a `cqlrcsh` file can be used to provide those settings. The default file location is in `$HOME/.cassandra/cqlrcsh` but can be changed with the `-r` switch. Use `-s` to not read `cqlrcsh`.

```bash
table-properties -r <filename>
```

#### Other switches

```
  -c <ip>, --contactpoint <ip>            Host IP address or name. Default: localhost
  -C <filename>, --clientcert <filename>  Client cert file name.
  -d, --dump                              Dump current configuration to STDOUT
  -k <filename>, --clientkey <filename>   Client key file name.
  -l <filename>, --log <filename>         Log file name. If none is provied, STDERR is used.
  -p <port #>, --port <port #>            Port number. Default: 9042
  -P, --password                          Prompt for password.
  -r <filename>, --rcfile <filename>      cqlrc file name. Default: ~/.cassandra/cqlshrc
  -t, --tls                               Use TLS encryption for client server communication.
  -u <user name>, --username <user name>  User name for plain text authentication.
  -v, --version                           show program's version number and exit
```

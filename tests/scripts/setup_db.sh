#!/usr/bin/env bash

die() {
    echo $1
    exit 1 
}

print() {
    [ ! $silent ] && echo $1
}

! [[ -x $(command -v cqlsh) ]] && die "cqlsh must be installed"

SCHEMA_DIR=$(pwd)/tests/setup/cql

[[ ! -d $SCHEMA_DIR ]] && die "Cannot locate create scripts"

silent=false
[[ $# -gt 0 && $1 == "--silent" ]] && silent=true

print "Running schema creation scripts..."
find $SCHEMA_DIR -name 'create_*.cql' -exec cat {} \; | cqlsh
print "Done."
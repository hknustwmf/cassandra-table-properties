# Cert Creation

The following commands were used to create the keystore and certificate. The password is 'cassandra'

Create the dummy keystore for development environments

```shell
mkdir -p ./certs
keytool -genkey -keyalg RSA -alias node0 -keystore ./certs/keystore.node0 -storepass cassandra -keypass cassandra -dname "CN=127.0.0.1, OU=None, O=None, L=None, C=None"
```

Convert the JKS format to PKCS12 format

```shell
keytool -importkeystore -srckeystore ./certs/keystore.node0 -destkeystore ./certs/keystore_pkcs12.node0 -deststoretype pkcs12
```

Export the public portion to a file

```shell
keytool -export -alias node0 -file ./certs/node0.cer -keystore ./certs/keystore_pkcs12.node0
```

Create the cert file for the client connection

```shell
openssl pkcs12 -in ./certs/keystore_pkcs12.node0 -nokeys -out ./certs/node0.cer.pem" -passin pass:cassandra
```

## Enabling SSL on the Cluster Node

To test the TLS/SSL setup all we want is an encrypted connection not client authentication. To enable encyption
locate the `cassandra.yaml` file in `/etc/cassandra/` and modify the client_encryption_options section as shown below

```yaml
client_encryption_options:
    enabled: true
    # If enabled and optional is set to true encrypted and unencrypted connections are handled.
    optional: false
    keystore: /etc/cassandra/conf/.keystore
    keystore_password: cassandra
```

Copy the keystore file `node0.keystore` to the conf folder

```shell
sudo mkdir -p /etc/cassandra/conf/
sudo cp ./certs/node0.keystore /etc/cassandra/conf/.keystore
```

and restart the Cassandra service.

## Client Cert Setup

Copy the PKCS12 cert file to `$HOME/.cassandra`

```shell
mkdir $HOME/.cassandra
cp ./certs/node0.cer.pem $HOME/.cassandra/
```

Copy the `cqlsh.sample` file from the tests/setup to `$HOME/.cassandra`

```shell
cp tests/setup/cqlshrc $HOME/.cassandra/cqlshrc
```

and enable an enable client-cluster encryption in `cqlshrc`

```editor-config
;; Always connect using SSL - false by default
ssl = true
...
[ssl]
certfile = /home/holger/.cassandra/node0.cer.pem

;; Optional - true by default.
validate = false
```

Source: [Cassandra SSL Certificates](https://docs.datastax.com/en/archived/cassandra/3.0/cassandra/configuration/secureSSLCertificates.html)

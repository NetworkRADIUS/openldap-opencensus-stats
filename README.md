# openldap-opencensus-stats

Collect statistics from the OpenLDAP monitoring database, and publish them through OpenCensus.

## Overview
A utility to collect metrics from an LDAP server and report them to
monitoring software, such as GCP.

## Installation
### Dependencies
- LDAP libraries and header files
- Python 3.9 or later
- C compilers, to compile the Python bindings to LDAP

### Installation commands
```bash
sudo pip3 install openldap-opencensus-stats
```

### Configuration
A sample configuration file is provided in openldap-opencensus-stats.template.yml.  The
configuration is YAML data, with the structure described below.

This should be copied to `/etc/openldap-opencensus-stats.yml` and amended to suit the
system requirements.

## Running
```bash
/usr/local/bin/openldap_opencensus_stats /etc/openldap-opencensus-stats.yml
```

A sample systemd service definition is provided in the `redhat` directory.

## General Configuration
### ldapServers
A list of the LDAP servers to monitor, and their connection information.  An example is:
```yaml
ldapServers:
  - database: UniqueName
    connection:
      server_uri: ldap://hostname
      userDn: CN=admin,DC=example,DC=org
      userPassword: adminpassword
      startTls: false
      timeout: 5
    syncOnly: False
```
Each entry will have the structure:
- **database** _(optional)_: A human name for this LDAP database.  This
  will be used to tag the statistic for data labelling.
- **connection** _(required)_: The connection information for this LDAP
  database.
  - **serverUri** _(required)_: URI of this LDAP database.  The protocol
    may be `ldap://`, `ldaps://`, or `ldapi://`.
  - **userDn** _(optional)_: Also known as bind DN, this is the user
    credential to use in connecting to this LDAP database.
    __Default: blank__
  - **userPassword** _(optional)_: Password for the userDn.
    __Default: blank__
  - **startTls** _(optional)_:  Whether to StartTLS on an `ldap://`
    connection.  Takes a boolean value, such as "y", "Yes", true,
    False, 1, or 0.  __Default: false__
  - **caFile** _(optional)_: Full path to a file containing one or more
    CA certificates to use when verifying the LDAP server certificate.
    __Default: blank__
  - **certFile** _(optional)_: Full path to a file containing a client
    certificate to use in X509 authentication.
    __Default: blank__
  - **keyFile** _(optional)_: Full path to the private key for X509
    authentication.
    __Default: blank__
  - **saslMech** _(optional)_: SASL mechanism to use.  Only EXTERNAL is
    currently supported.
    __Default: blank__
  - **timeout** _(optional)_:  Seconds to wait for a response from this
    LDAP server before timing out.  A negative value causes the check
    to wait indefinitely.  A zero value effects a poll.
    __Default: -1__
- **syncOnly** _(optional)_: Set to True if this server definition is
  only present for evaluating replication delays
### exporters
This is a list of the ways to export data to a monitoring system.
An example is:
```yaml
exporters:
  - name: Stackdriver
    options:
      project_id: example
  - name: Prometheus
    options:
      namespace: openldap
      port: 8000
      address: 0.0.0.0
```
Each entry will have the structure:
- **name** _(required)_: The name of the exporter.  Currently only two names
  are supported, `Stackdriver` to export to GCP, and `Prometheus`, which
  is mostly useful for development or debugging.
- **options** _(required)_: The options for instantiating the exporter.
  The contents will vary depending on the chosen exporter.
  - **project_id** _(required for Stackdriver)_: The GCP project ID
  - **namespace** _(optional, used by Prometheus)_: Used to construct the
    Prometheus metric_name.  __Default: openldap__
  - **port** _(optional, used by Prometheus)_: The TCP port for the
    Prometheus metrics web service.  __Default: 8000__
  - **address** _(optional, used by Prometheus)_: The IP address to use
    for the Prometheus metrics web service.  __Default: 0.0.0.0__

### logConfig
This is a configuration for the logging.  The software uses the Python
logging framework, and consumes a configuration documented
[at the Python documentation site](https://docs.python.org/3.5/library/logging.config.html#dictionary-schema-details).
This entry is optional, with the default being the default Python
configuration.

An example config is:
```yaml
logConfig:
  root:
    level: DEBUG
    handlers:
      - stderr
      - syslog
  handlers:
    stderr:
      class: logging.StreamHandler
      level: DEBUG
    syslog:
      class: logging.handlers.SysLogHandler
      level: WARNING
```
This configuration specifies that the default logger, root, will log
any message of `DEBUG` or lesser severity through two handlers, `stderr`
and `syslog`.  The `stderr` handler will use a `StreamHandler` to 
output anything of `DEBUG` or lesser severity to standard error.  The
`syslog` handler will use a `SysLogHandler` to output anything of 
`WARNING` or lesser severity to the system log.

## Metrics configuration
This part of the configuration details the database objects to monitor.
This structure is nestable, dynamic, and interpreted.
- Nestable: The structure of this section is nestable.  That is, it can
  repeat an arbitrary number of times.
- Dynamic: The structure is dynamic in two ways.
  - The configuration can react to the LDAP database structure.
  - The configuration can react to the LDAP database values
- Interpreted: The configuration can include Python code to be executed
  at data retrieval time to update the values.

```
object:
  database-object-name: database-object-definition
  database-object-name: database-object-definition
  ...
database-object-name: database-object-name-string | "children"
database-object-name-string: configuration-object-name
database-object-definition:
  rdn: regex-string
  name: regex-string
  object: object
  metric: 
    metric-definition-name: metric-definition
    metric-definition-name: metric-definition
    ...
regex-string: "<string>"
metric-definition-name: configuration-object-name
metric-definition:
  attribute: "<string>"
  description: "<string>"
  unit: unit-name
configuration-object-name: "[A-Za-z0-9_]+"
unit-name: "<string>"

```

### object
`object` contains a number of named database object definitions.

```yaml
object:
  name1:
    [database object definition]
  name2: ...
  name3: ...
```

#### Object names
Names may contain alphanumeric characters plus the underscore. A
special database object name, `children`, will instruct the system to
query the LDAP database for immediate children of the current DN and
replace the `children` named database object definition with one copy
of the database object definition per qualifying child.

#### Object definitions



### Database Object Definition
A database object definition 








### Statistics
This is a list of statistics that can be collected from an LDAP database,
and how to render the collected value in monitoring.  An example is:
```yaml
statistics:
- aggregator: LastValue
  attribute: monitorCounter
  description: connections_current
  dn: cn=Current,cn=Connections,cn=Monitor
  name: connections_current
  unit: 1
```
Each entry will have the structure:
- **name** _(required)_: The name for this statistic, which will be used to
  construct the collected metric name.
- **dn** _(required)_: The LDAP DN to query for data
- **attribute** _(required)_: The LDAP attribute from the above DN to use
  for the statistic data
- **aggregator** _(optional)_: The type of aggregation to perform when the
  monitoring system collects values from this software less often than
  this software collects its values.  Options are `LastValue`, `Count`,
  `Sum`, and `Distribution`.  __Default: LastValue__
- **unit** _(optional)_: The unit of measure for this statistic.  The unit
  must come from [the Unified Code for Units of Measure](https://unitsofmeasure.org/ucum).
  Commonly this will be `1`, `By` (Bytes), or `s` (seconds).
  __Default: 1__


### sync
Configuration for the monitoring of replication delay in a replicated LDAP cluster
An example is:
```yaml
sync:
  dc=example,dc=com:
    clusterServers:
      - database1
      - database2
      - database3
    reportServers:
      - database1
```
Each entry in the dictionary, specifies the base DN of the database in a given cluster.
Under that:
- **clusterServers** _(required)_: Specifies the LDAP servers which make up the cluster.
  These must be values found in the `database` field in `ldapServers`.
- **reportServers** _(required)_: Specifies which of LDAP servers replication offset
  will be reported for.

When processing replication offset, the `contextCSN` of the base DN is queried on all
the LDAP servers in the cluster.  The maximum timestamp found is taken as the current
database timestamp.

For each of the servers listed in `reportServers`, the offset from that timestamp is
reported.

This allows for two scenarios:

- a central reporting server which queries all hosts in a cluster and reports on all of them.
- distributed reporting, where, for example, each replica queries the masters and itself
  and reports only its own offset.

Statistics are tagged with the base DN and the `rid` of the provider.  In a multi master
cluster, for each `reportServers` entry there will be one statistic recorded for each
provider in the cluster tagged with the appropriate `rid`.

## Credits
Copyright 2023, NetworkRADIUS 
This utility was written by Mark Donnelly, mark - at - painless-securtiy - dot - com.


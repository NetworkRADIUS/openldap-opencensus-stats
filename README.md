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
pip3 install -r requirements.txt
```

## Running
```bash
python3 ./ldap_metrics.py ./ldap_metrics.yml
```

## Configuration
A sample configuration file is provided in ldap_metrics.yml.  The
configuration is YAML data, with the following structure:

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
    chosenStatistics:
      - current_connections
      - search_operations
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
  - **timeout** _(optional)_:  Seconds to wait for a response from this
    LDAP server before timing out.  A negative value causes the check
    to wait indefinitely.  A zero value effects a poll.
    __Default: -1__
- **chosenStatistics** _(optional)_: a list of statistics names to
  collect from this LDAP database.  If omitted, all defined statistics 
  are collected.
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

## Credits
Copyright 2023, NetworkRADIUS 
This utility was written by Mark Donnelly, mark - at - painless-securtiy - dot - com.


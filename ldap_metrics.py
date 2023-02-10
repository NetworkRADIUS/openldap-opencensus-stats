#!python3

# openldap-opencensus-stats
# Copyright (C) 2023  NetworkRADIUS
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
from time import sleep

import ldap
import logging
import yaml

import opencensus.ext.stackdriver.stats_exporter

from logging import config

from opencensus.ext import prometheus, stackdriver
from opencensus.ext.prometheus import stats_exporter
from opencensus.stats import view, measure, aggregation, stats
from opencensus.tags import tag_key, tag_map, tag_value

SUPPORTED_EXPORTERS = ['Prometheus', 'Stackdriver']


class LdapStatistic:

    def __init__(self, stat_configuration=None, tag_keys=None):
        if stat_configuration is None:
            stat_configuration = {}
        if tag_keys is None:
            tag_keys = []
        self.dn = stat_configuration.get('dn', '')
        if self.dn is None:
            logging.error("Aborting configuration of LDAP statistic due to lack of dn attribute.")
            raise ValueError('Statistics definition must include the dn attribute')

        self.name = stat_configuration.get('name', id(self))
        self.attribute = stat_configuration.get('attribute', '')
        self.description = stat_configuration.get('description', 'Unspecified')
        self.unit = stat_configuration.get('unit', '1')

        self.measure = measure.MeasureFloat(
            name=self.name,
            description=self.description,
            unit=self.unit
        )

        aggregator_class_name = f'{stat_configuration.get("aggregator", "LastValue")}Aggregation'
        aggregator_class_module = __import__('opencensus.stats.aggregation', fromlist=aggregator_class_name)
        aggregator_class = getattr(aggregator_class_module, aggregator_class_name)

        self.view = view.View(
            name=self.name,
            description=self.description,
            columns=tag_keys,
            aggregation=aggregator_class(),
            measure=self.measure
        )
        stats.stats.view_manager.register_view(self.view)

    def display_name(self):
        return f"{self.name}:{self.attribute}"

    def collect(self, ldap_server=None, measurement_map=None):
        def display_name(server, statistic):
            return f"{server.database}:{statistic.display_name()}"

        if ldap_server is None:
            logging.error(f"INTERNAL ERROR: Failing to collect statistic {self.display_name()} "
                          f"because no LDAP server supplied.")
            raise ValueError("LDAP server must be supplied to LdapStatistic.collect.")
        if measurement_map is None:
            logging.error(f"INTERNAL ERROR: Failing to collect statistic {self.display_name()} "
                          f"because no measurement map was supplied.")
            raise ValueError("The measurement map must be supplied to LdapStatistic.collect")

        value = ldap_server.query_dn_and_attribute(self.dn, self.attribute)
        if value is None:
            logging.warning(f"No value collected for {display_name(ldap_server, self)}")
            return
        logging.debug(f"Collected value for {display_name(ldap_server, self)}: {value}")
        measurement_map.measure_float_put(self.measure, float(value[0]))


class LdapServer:
    def __init__(self,
                 uri,
                 user_dn=None,
                 user_password=None,
                 database=None,
                 start_tls=False,
                 timeout=-1):
        if database is None:
            database = uri

        self.connection = None
        self.database = database
        self.user_dn = user_dn
        self.user_password = user_password

        self.connect_to_ldap(
            server_uri=uri,
            start_tls=start_tls,
            timeout=timeout
        )

    def connect_to_ldap(self, server_uri, start_tls=False, timeout=-1):
        if server_uri is None:
            logging.error(f"Failing to configure LDAP server {self.database} because no URI was supplied.")
            raise ValueError(f"An LDAP server URI must be defined for {self.database}")

        self.connection = ldap.ldapobject.ReconnectLDAPObject(server_uri)
        self.connection.timeout = timeout

        if start_tls:
            logging.info(f"Using StartTLS for {self.database}")
            self.connection.protocol_version = ldap.VERSION3
            self.connection.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
            self.connection.start_tls_s()

    def query(self, dn=None, scope=ldap.SCOPE_SUBTREE, attr_list=None):
        if attr_list is None:
            attr_list = ['+']
        if dn is None:
            logging.error(f"INTERNAL ERROR: Could not run a query because no DN was supplied")
            raise ValueError('Must specify a DN to query')

        try:
            self.connection.simple_bind_s(self.user_dn, self.user_password)
            return self.connection.search_s(dn, scope=scope, attrlist=attr_list)
        except (ldap.SERVER_DOWN, ldap.NO_SUCH_OBJECT, ldap.TIMEOUT):
            return []

    def query_dn_and_attribute(self, dn, attribute):
        results = self.query(dn, scope=ldap.SCOPE_BASE)
        if not results:
            return None

        result_dn, result_attributes = results[0]
        if attribute not in result_attributes:
            return None
        return result_attributes.get(attribute)


def read_config_file(file_name):
    with open(file_name, 'r') as file:
        ret_val = yaml.safe_load(file)
    return ret_val


def parse_command_line():
    parser = argparse.ArgumentParser(description='Monitor the LDAP database.')
    parser.add_argument('config_file')

    return parser.parse_args()


def create_exporter(exporter_configuration=None):
    if exporter_configuration is None:
        raise ValueError("Cannot create an exporter with no configuration!")

    name = exporter_configuration.get('name')
    if name not in SUPPORTED_EXPORTERS:
        logging.error(
            f"Requested exporter named {name}, which is not supported.  Choose from:{', '.join(SUPPORTED_EXPORTERS)}"
        )
        raise ValueError(
            f"Requested exporter named {name}, which is not supported.  Choose from:{', '.join(SUPPORTED_EXPORTERS)}"
        )

    options = exporter_configuration.get('options', {})
    exporter = None
    if "Prometheus" == name:
        if 'options' not in exporter_configuration:
            logging.error("The Prometheus exporter requires options configuration.")
            raise ValueError("The Prometheus exporter requires options configuration.")
        final_options = {'namespace': 'openldap', 'port': 8000, 'address': '0.0.0.0'}
        final_options.update(options)
        exporter = stats_exporter.new_stats_exporter(
            prometheus.stats_exporter.Options(**final_options)
        )

    elif "Stackdriver" == name:
        exporter = opencensus.ext.stackdriver.stats_exporter.new_stats_exporter(interval=5)
        print(f"Exporting stats to this project {exporter.options.project_id}")

    return exporter


def main():
    args = parse_command_line()
    configuration = read_config_file(args.config_file)
    log_config = configuration.get('logConfig')
    if log_config and isinstance(log_config, dict):
        log_config['version'] = log_config.get('version', 1)
        logging.config.dictConfig(log_config)

    key_database = tag_key.TagKey('database')
    statistics = dict([
        (statistic.get('name', ''), LdapStatistic(stat_configuration=statistic, tag_keys=[key_database]))
        for statistic
        in configuration.get('statistics', [])
    ])
    for exporter_config in configuration.get('exporters', []):
        exporter = create_exporter(exporter_config)
        stats.stats.view_manager.register_exporter(exporter)

    servers = {}
    chosen_statistics = {}
    for entry in configuration.get('ldapServers', []):
        connection_config = entry.get('connection', {})
        ldap_server = LdapServer(
            uri=connection_config.get('serverUri'),
            database=entry.get('database'),
            user_dn=connection_config.get('userDn'),
            user_password=connection_config.get('userPassword'),
            start_tls=connection_config.get('startTls', False),
            timeout=connection_config.get('timeout', -1)
        )
        servers[ldap_server.database] = ldap_server
        chosen_statistics[ldap_server.database] = entry.get('chosenStatistics', statistics.keys())

    while True:
        for ldap_server_database, server_statistics in chosen_statistics.items():
            ldap_server = servers[ldap_server_database]
            mmap = stats.stats.stats_recorder.new_measurement_map()
            for server_statistic in server_statistics:
                statistics[server_statistic].collect(ldap_server=ldap_server, measurement_map=mmap)
            tmap = tag_map.TagMap()
            tmap.insert(key_database, tag_value.TagValue(ldap_server.database))
            mmap.record(tmap)
        sleep(5)


if __name__ == '__main__':
    main()

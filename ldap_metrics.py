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

import logging
import yaml

from ldapstats import LdapServer, LdapStatistic

import opencensus.ext.stackdriver.stats_exporter

from logging import config

from opencensus.ext import prometheus
from opencensus.ext.prometheus import stats_exporter
from opencensus.stats import view, stats
from opencensus.tags import tag_key, tag_map, tag_value

# Make up for broken code in the Prometheus exporter
from opencensus.stats import aggregation_data
opencensus.stats.aggregation_data.SumAggregationDataFloat = opencensus.stats.aggregation_data.SumAggregationData

SUPPORTED_EXPORTERS = ['Prometheus', 'Stackdriver']


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


def generate_statistics(configuration=None, tag_keys=None, dn_root='', name_root='', name=None):
    def append(stem=None, suffix=None, separator='/'):
        x = [stem, suffix]
        y = [item for item in x if item]
        return separator.join(y)

    if tag_keys is None:
        tag_keys = []
    if configuration.get('name'):
        name = configuration.get('name')
    if name is None:
        raise ValueError(f'Name is required at {name_root}')

    if configuration is None:
        return []
    if not {'rdn'}.issubset(set(configuration.keys())):
        raise ValueError(f'Required configuration not found for {name}: {configuration}')

    statistics = {}

    full_dn = append(stem=configuration.get('rdn', ''), suffix=dn_root, separator=',')

    for sub_name, sub_configuration in configuration.get('object', {}).items():
        statistics.update(generate_statistics(
            configuration=sub_configuration,
            tag_keys=tag_keys,
            dn_root=full_dn,
            name_root=append(stem=name_root, suffix=name),
            name=sub_name
        ))

    for metric_name, metric_configuration in configuration.get('metric', {}).items():
        object_name = append(name_root, name)
        full_name = append(object_name, metric_name)
        statistics[full_name] = LdapStatistic(
            dn=full_dn,
            name=full_name,
            attribute=metric_configuration.get('attribute'),
            description=metric_configuration.get('description'),
            unit=metric_configuration.get('unit'),
            tag_keys=tag_keys
        )

    return statistics


def main():
    args = parse_command_line()
    configuration = read_config_file(args.config_file)
    log_config = configuration.get('logConfig')
    if log_config and isinstance(log_config, dict):
        log_config['version'] = log_config.get('version', 1)
        logging.config.dictConfig(log_config)

    key_database = tag_key.TagKey('database')
    tag_keys = [key_database]
    statistics = {}
    for name, object_configuration in configuration.get('object', {}).items():
        statistics.update(generate_statistics(
            configuration=object_configuration,
            tag_keys=tag_keys,
            dn_root='',
            name_root='',
            name=name
        ))
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

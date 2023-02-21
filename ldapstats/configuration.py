import copy
import logging
import logging.config
import re

import yaml
from time import sleep

from ldapstats.config_transformers.base import ConfigurationTransformationChainSingleton
from ldapstats.ldap_metric_set import MetricSet
from ldapstats.ldap_server import LdapServerPool
from ldapstats.ldap_statistic import LdapStatistic

from opencensus.stats import stats
from opencensus.tags import tag_key, tag_map, tag_value
from opencensus.ext.prometheus import stats_exporter
import opencensus.ext.stackdriver.stats_exporter

# Make up for broken code in the Prometheus exporter
from opencensus.stats import aggregation_data
opencensus.stats.aggregation_data.SumAggregationDataFloat = opencensus.stats.aggregation_data.SumAggregationData

SUPPORTED_EXPORTERS = ['Prometheus', 'Stackdriver']


class Configuration:
    def __init__(self, config_file_name):
        if config_file_name is None:
            raise ValueError(f"Config file name must be supplied")
        self._config_file_name = config_file_name
        self._configuration_dict = {}
        self._sleep_time = 5
        self._metric_sets = []

        self.reconfigure()

    def reconfigure(self):
        self._configuration_dict = read_yaml_file(self._config_file_name)
        normalized_configuration = ConfigurationTransformationChainSingleton().transform_configuration(
            self._configuration_dict
        )

        self._sleep_time = normalized_configuration.get('period', 5)
        log_config = normalized_configuration.get('log_config')
        if log_config and isinstance(log_config, dict):
            log_config['version'] = log_config.get('version', 1)
            logging.config.dictConfig(log_config)
        for exporter_config in normalized_configuration.get('exporters', []):
            exporter = create_exporter(exporter_config)
            stats.stats.view_manager.register_exporter(exporter)

        for ldap_server_config in normalized_configuration.get('ldap_servers'):
            metric_set = self.generate_metric_set(ldap_server_config)
            self._metric_sets.append(metric_set)

    @staticmethod
    def generate_metric_set(ldap_server_config):
        args = copy.deepcopy(ldap_server_config.get('connection', {}))
        args['database'] = ldap_server_config.get('database')
        ldap_server = LdapServerPool().get_ldap_server(**args)
        metric_set = MetricSet(ldap_server=ldap_server)
        configs = [ldap_server_config.get('object')]
        while configs:
            config = configs.pop()
            if isinstance(config, list):
                for item in config:
                    configs.insert(0, item)
            elif isinstance(config, dict):
                dn = config.get('computed_dn')
                name = config.get('metric_name')
                attribute = config.get('attribute')
                unit = config.get('unit')
                description = config.get('description', '')
                if dn and name and attribute and unit:
                    stat = LdapStatistic(
                        dn=dn,
                        name=name,
                        attribute=attribute,
                        description=description,
                        unit=unit
                    )
                    metric_set.add_statistic(stat)
                for key, value in config.items():
                    configs.insert(0, value)
        return metric_set

    def metric_sets(self):
        return self._metric_sets

    def sleep(self):
        sleep(self._sleep_time)


def read_yaml_file(file_name):
    with open(file_name, 'r') as file:
        ret_val = yaml.safe_load(file)
    return ret_val


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
            stats_exporter.Options(**final_options)
        )

    elif "Stackdriver" == name:
        exporter = opencensus.ext.stackdriver.stats_exporter.new_stats_exporter(interval=5)
        print(f"Exporting stats to this project {exporter.options.project_id}")

    return exporter

import copy
import logging
import logging.config
import re

import yaml
from time import sleep

from ldapstats.ldap_server import LdapServer
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
        self._ldap_server_list = []
        self._statistics_dict = {}
        self._tag_keys = [tag_key.TagKey('database')]
        self._ldap_server_dict = {}
        self._sleep_time = 5

        self.reconfigure()

    def reconfigure(self):
        self._configuration_dict = read_yaml_file(self._config_file_name)
        normalized_configuration = ConfigurationTransformationChainSingleton().transform_configuration(self._configuration_dict)
        self._ldap_server_dict = self._generate_ldap_server_dict(normalized_configuration)
        self._sleep_time = normalized_configuration.get('period', 5)
        log_config = normalized_configuration.get('logConfig')
        if log_config and isinstance(log_config, dict):
            log_config['version'] = log_config.get('version', 1)
            logging.config.dictConfig(log_config)
        for exporter_config in normalized_configuration.get('exporters', []):
            exporter = create_exporter(exporter_config)
            stats.stats.view_manager.register_exporter(exporter)

    def _generate_ldap_server_dict(self, normalized_configuration):
        self._ldap_server_list = self._generate_ldap_server_list()
        self._statistics_dict = self.generate_statistics(
            configuration=normalized_configuration,
            name='',
            tag_keys=self._tag_keys
        )
        ldap_server_dict = {}
        for ldap_server in self._ldap_server_list:
            # Should never be None
            server_configuration = self.get_configuration_for_ldap_server(ldap_server.database)
            chosen_statistics = server_configuration.get('chosenStatistics', [])
            if chosen_statistics and isinstance(chosen_statistics, list):
                self._ldap_server_dict[ldap_server] = [
                    statistic
                    for statistic_name, statistic in self._statistics_dict.items()
                    if statistic_name in chosen_statistics
                ]
            else:
                ldap_server_dict[ldap_server] = list(self._statistics_dict.values())
        return ldap_server_dict

    def _generate_ldap_server_list(self):
        server_config_list = self._configuration_dict.get('ldapServers', [])
        self._ldap_server_list = []
        for server_config in server_config_list:
            connection = server_config.get('connection')
            if connection is None:
                raise ValueError(f"Connection details needed for ldapServer {server_config.get('database')}")
            args = dict([
                (re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower(), value)
                for name, value in connection.items()
            ])
            args['database'] = server_config.get('database')
            self._ldap_server_list.append(LdapServer(**args))
        return self._ldap_server_list

    @staticmethod
    def generate_statistics(configuration=None, tag_keys=None, dn_root='', name_root='', name=None):
        def append(stem='', suffix='', separator='/'):
            ret = stem
            if suffix:
                if stem:
                    ret = ret + separator
                ret = ret + suffix
            return ret

        if not configuration or not isinstance(configuration, dict):
            return {}
        if configuration.get('name'):
            name = configuration.get('name')
        if name is None:
            raise ValueError(f"Name is required at {name_root}")
        rdn = configuration.get('rdn', '')
        if dn_root and not rdn:
            raise ValueError(f"rdn is required at {name_root}")
        full_dn = append(rdn, dn_root, ',')

        statistics = {}
        if isinstance(configuration.get('object'), dict):
            for object_name in configuration.get('object').keys():
                sub_name = append(name_root, name, '/')
                statistics.update(
                    Configuration.generate_statistics(
                        configuration=configuration.get('object').get(object_name),
                        tag_keys=tag_keys,
                        dn_root=full_dn,
                        name_root=sub_name,
                        name=object_name
                    )
                )

        for metric_name, metric_configuration in configuration.get('metric', {}).items():
            object_name = append(name_root, name, '/')
            full_name = append(object_name, metric_name, '/')
            statistics[full_name] = LdapStatistic(
                dn=full_dn,
                name=full_name,
                attribute=metric_configuration.get('attribute'),
                description=metric_configuration.get('description'),
                unit=metric_configuration.get('unit'),
                tag_keys=tag_keys
            )

        return statistics

    def get_configuration_for_ldap_server(self, database):
        for item in self._configuration_dict.get('ldapServers', []):
            if item.get('database') == database:
                return item
        return None

    def metrics(self):
        # {ldap_server: [ldap_statistic, ...], ...}
        return self._ldap_server_dict

    def record_tags(self, ldap_server):
        tmap = tag_map.TagMap()
        tmap.insert(self._tag_keys[0], tag_value.TagValue(ldap_server.database))
        return tmap

    def sleep(self):
        sleep(self._sleep_time)


class ConfigurationTransformationChainSingleton:
    transformation_chain = []

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ConfigurationTransformationChainSingleton, cls).__new__(cls)
        return cls.instance

    def register(self, cls):
        self.transformation_chain.append(cls)
        logging.info(f"Registered transformer: {cls.__name__}")

    def transform_configuration(self, configuration):
        configuration_result = {}
        configuration_input = configuration
        for link in self.transformation_chain:
            print(f"Calling configuration chain link {link.__name__}")
            configuration_result = link.process(configuration_input)
            configuration_input = configuration_result
        return configuration_result


class ConfigurationTransformer:
    transformers = []

    def __init_subclass__(cls, **kwargs):
        ConfigurationTransformationChainSingleton().register(cls)

    @staticmethod
    def process(configuration):
        return configuration


class SnakeCaseConfigurationTransformer(ConfigurationTransformer):
    @staticmethod
    def process(configuration):
        config = {}
        for key, value in configuration.items():
            snake_case_key = re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower()
            if isinstance(value, dict):
                snake_cased_value = SnakeCaseConfigurationTransformer.process(value)
            elif isinstance(value, list):
                snake_cased_value = [
                    SnakeCaseConfigurationTransformer.process(x) if isinstance(x, dict) else x
                    for x in value
                ]
            else:
                snake_cased_value = value
            config[snake_case_key] = snake_cased_value
        return config


class ChildObjectConfigurationTransformer(ConfigurationTransformer):
    @staticmethod
    def process(configuration):
        config = copy.deepcopy(configuration)
        if configuration.get('children'):
            child_value = config.pop('children')
            config['child1'] = child_value
            config['child2'] = child_value
            config['child3'] = child_value
        config['object'] = ChildObjectConfigurationTransformer.process(config.get('object', {}))
        return config


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

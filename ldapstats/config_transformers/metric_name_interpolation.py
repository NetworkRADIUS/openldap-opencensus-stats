import copy

from ldapstats.config_transformers.base import ConfigurationTransformer
from ldapstats.ldap_server import LdapServerPool


class MetricNameInterpolationConfigurationTransformer(ConfigurationTransformer):
    @staticmethod
    def process(configuration):
        if not isinstance(configuration, dict):
            raise ValueError(
                'NameInterpolationConfigurationTransformer expect a configuration that is a dict '
                'but received one that isn\'t.')

        config = copy.deepcopy(configuration)
        for server_config in config.get('ldap_servers'):
            ldap_server = ConfigurationTransformer.get_ldap_server(server_config=server_config)
            server_config['object'] = MetricNameInterpolationConfigurationTransformer.process_objects_for_ldap_server(
                configuration=server_config.get('object', {}),
                dn='',
                ldap_server=ldap_server
            )
        return config

    @staticmethod
    def process_objects_for_ldap_server(configuration, dn, ldap_server):

        if isinstance(configuration, list):
            return [
                MetricNameInterpolationConfigurationTransformer.process_objects_for_ldap_server(item, dn, ldap_server)
                for item in configuration
            ]
        elif isinstance(configuration, dict):
            config = copy.deepcopy(configuration)
            if config.get('metric_name'):
                config['metric_name'] = MetricNameInterpolationConfigurationTransformer.create_metric_name(config)
            return config
        else:
            return configuration

    @staticmethod
    def create_metric_name(config):
        


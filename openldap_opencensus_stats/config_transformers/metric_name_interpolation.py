import copy
import logging
import re

from openldap_opencensus_stats.config_transformers.base import ConfigurationTransformer


class MetricNameInterpolationConfigurationTransformer(ConfigurationTransformer):
    @staticmethod
    def process(configuration):
        if not isinstance(configuration, dict):
            raise ValueError(
                'NameInterpolationConfigurationTransformer expect a configuration that is a dict '
                'but received one that isn\'t.')

        config = copy.deepcopy(configuration)
        for server_config in config.get('ldap_servers'):
            if not server_config.get('sync_only', False):
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
            config = {}

            for key, value in configuration.items():
                proper_value = MetricNameInterpolationConfigurationTransformer.process_objects_for_ldap_server(
                    value, dn, ldap_server)
                if key in ['name']:
                    config['computed_name'] = MetricNameInterpolationConfigurationTransformer.create_metric_name(
                        configuration,
                        ldap_server
                    )
                config[key] = proper_value

            return config

        else:
            return configuration

    @staticmethod
    def create_metric_name(config, ldap_server):
        def repl_func(matches):
            groups = matches.groups()
            if 'rdn' == groups[0]:
                index = int(groups[1])
                rdn_matches = re.match(
                    config.get('rdn'),            # Pattern to match - the 'rdn' entry
                    config.get('computed_rdn')    # String for matching - the 'computed_rdn' entry
                )
                if rdn_matches:
                    return rdn_matches.group(index)
            elif 'attr' == groups[0]:
                attribute_name = groups[1]
                ldap_result = ldap_server.query_dn_and_attribute(
                    config.get('computed_dn', ''),
                    attribute_name
                )
                value = ldap_result[0]
                if isinstance(value, bytes):
                    value = value.decode()
                return str(value)
            else:
                logging.error(f"Unknown interpolation requested in name: {groups[0]}.{groups[1]}")

        name = config.get('computed_name', config.get('name', ''))
        name = re.sub(
            '{([^\\.}]+)\\.([^}]+)}',
            repl_func,
            name
        ).lower()
        return name

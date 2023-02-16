import copy

from ldapstats.config_transformers.base import ConfigurationTransformer


class MetricDnConfigurationTransformer(ConfigurationTransformer):
    @staticmethod
    def process(configuration):
        if not isinstance(configuration, dict):
            raise ValueError(
                'NameConfigurationTransformer expect a configuration that is a dict but received one that isn\'t.')
        config = copy.deepcopy(configuration)
        object_config = config.get('object')
        if object_config:
            config['object'] = MetricDnConfigurationTransformer.process_object_config(
                configuration=object_config
            )
        return config

    @staticmethod
    def process_object_config(configuration, suffix_dn='', separator=','):
        if isinstance(configuration, dict):
            config = {}
            if suffix_dn:
                full_suffix = separator + suffix_dn
            else:
                full_suffix = suffix_dn
            computed_dn = suffix_dn
            if configuration.get('rdn'):
                computed_dn = configuration.get('rdn') + full_suffix

            # True if either 'rdn' or 'attribute' is a key
            if configuration.get('rdn', configuration.get('attribute')):
                config['computed_dn'] = computed_dn
            else:
                computed_dn = suffix_dn
            for key, value in configuration.items():
                config[key] = MetricDnConfigurationTransformer.process_object_config(
                    configuration=value,
                    suffix_dn=computed_dn,
                    separator=separator
                )
            return config
        elif isinstance(configuration, list):
            return [
                MetricDnConfigurationTransformer.process_object_config(
                    configuaration=item,
                    suffix_dn=suffix_dn,
                    separator=separator
                )
                for item in configuration
            ]
        else:
            return configuration

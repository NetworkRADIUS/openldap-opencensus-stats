import copy

from ldapstats.config_transformers.base import ConfigurationTransformer


class MetricNameConfigurationTransformer(ConfigurationTransformer):
    @staticmethod
    def process(configuration):
        if not isinstance(configuration, dict):
            raise ValueError(
                'NameConfigurationTransformer expect a configuration that is a dict but received one that isn\'t.')
        config = copy.deepcopy(configuration)
        object_config = config.get('object')
        if object_config:
            config['object'] = MetricNameConfigurationTransformer.process_object_config(
                configuration=object_config
            )
        return config

    @staticmethod
    def process_object_config(configuration, prefix='', default_name='', separator='/'):
        full_prefix = prefix + separator if prefix else ''
        if isinstance(configuration, dict):
            config = {}
            metric_name = prefix
            if configuration.get('rdn') or configuration.get('attribute'):
                metric_name = full_prefix + configuration.get('name', default_name)
                config['metric_name'] = metric_name
            for key, value in configuration.items():
                config[key] = MetricNameConfigurationTransformer.process_object_config(
                    configuration=value,
                    prefix=metric_name,
                    default_name=key,
                    separator=separator
                )
            return config
        elif isinstance(configuration, list):
            return [
                MetricNameConfigurationTransformer.process_object_config(
                    configuaration=item,
                    prefix=prefix,
                    default_name=default_name,
                    separator=separator
                )
                for item in configuration
            ]
        else:
            return configuration

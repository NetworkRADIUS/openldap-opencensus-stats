from openldap_opencensus_stats.config_transformers.base import ConfigurationTransformer


class MetricNameConfigurationTransformer(ConfigurationTransformer):
    @staticmethod
    def process(configuration):
        return MetricNameConfigurationTransformer.process_object_config(configuration)

    @staticmethod
    def process_object_config(configuration, prefix='', default_name='', separator='/'):
        full_prefix = prefix + separator if prefix else ''
        if isinstance(configuration, dict):
            config = {}
            metric_name = prefix
            if configuration.get('rdn') or configuration.get('attribute'):
                metric_name = full_prefix + configuration.get('computed_name', configuration.get('name', default_name))
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
                    configuration=item,
                    prefix=prefix,
                    default_name=default_name,
                    separator=separator
                )
                for item in configuration
            ]
        else:
            return configuration

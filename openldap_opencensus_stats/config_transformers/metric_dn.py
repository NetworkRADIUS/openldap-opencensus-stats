from openldap_opencensus_stats.config_transformers.base import ConfigurationTransformer


class MetricDnConfigurationTransformer(ConfigurationTransformer):
    @staticmethod
    def process(configuration):
        return MetricDnConfigurationTransformer.process_object_config(configuration)

    @staticmethod
    def process_object_config(configuration, suffix_dn='', separator=','):
        if isinstance(configuration, dict):
            config = {}
            if suffix_dn:
                full_suffix = separator + suffix_dn
            else:
                full_suffix = suffix_dn
            computed_dn = suffix_dn
            rdn = configuration.get('computed_rdn', configuration.get('rdn'))
            if rdn:
                computed_dn = rdn + full_suffix

            for key, value in configuration.items():
                config[key] = MetricDnConfigurationTransformer.process_object_config(
                    configuration=value,
                    suffix_dn=computed_dn,
                    separator=separator
                )

            # True if either 'rdn' or 'attribute' is a key
            if configuration.get('rdn', configuration.get('attribute')):
                config['computed_dn'] = computed_dn
            else:
                computed_dn = suffix_dn

            return config
        elif isinstance(configuration, list):
            return [
                MetricDnConfigurationTransformer.process_object_config(
                    configuration=item,
                    suffix_dn=suffix_dn,
                    separator=separator
                )
                for item in configuration
            ]
        else:
            return configuration

from openldap_opencensus_stats.config_transformers.base import ConfigurationTransformer


class MetricQueryDnConfigurationTransformer(ConfigurationTransformer):
    @staticmethod
    def process(configuration):
        return MetricQueryDnConfigurationTransformer.process_object_config(configuration)

    @staticmethod
    def process_object_config(configuration, query_dn=None):
        if isinstance(configuration, dict):
            config = {}
            configuration_query_dn = configuration.get('query_dn', configuration.get('rdn'))
            if not query_dn and configuration_query_dn:
                query_dn = configuration_query_dn

            for key, value in configuration.items():
                config[key] = MetricQueryDnConfigurationTransformer.process_object_config(
                    configuration=value,
                    query_dn=query_dn,
                )

            # True if either 'rdn' or 'attribute' is a key
            if query_dn:
                config['query_dn'] = query_dn

            return config
        elif isinstance(configuration, list):
            return [
                MetricQueryDnConfigurationTransformer.process_object_config(
                    configuration=item,
                    query_dn=query_dn,
                )
                for item in configuration
            ]
        else:
            return configuration

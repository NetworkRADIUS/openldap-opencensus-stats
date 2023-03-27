import re

from openldap_opencensus_stats.config_transformers.base import ConfigurationTransformer


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

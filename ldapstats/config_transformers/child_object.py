from ldapstats.config_transformers.base import ConfigurationTransformer


class ChildObjectConfigurationTransformer(ConfigurationTransformer):
    @staticmethod
    def process(configuration):
        if isinstance(configuration, dict):
            config = {}
            for key, value in configuration.items():
                proper_value = ChildObjectConfigurationTransformer.process(value)
                if key == 'children':
                    config['child1'] = proper_value
                else:
                    config[key] = proper_value
            return config
        elif isinstance(configuration, list):
            return [
                ChildObjectConfigurationTransformer.process(item)
                for item in configuration
            ]
        else:
            return configuration

import logging


class ConfigurationTransformer:
    transformers = []

    def __init_subclass__(cls, **kwargs):
        ConfigurationTransformationChainSingleton().register(cls)

    @staticmethod
    def process(configuration):
        return configuration

    @staticmethod
    def get_ldap_server(server_config):
        args = dict([
            (re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower(), value)
            for name, value in server_config.get('connection', {}).items()
        ])
        args['database'] = server_config.get('database')
        ldap_server = LdapServerPool().get_ldap_server(**args)
        return ldap_server


class ConfigurationTransformationChainSingleton:
    transformation_chain = []

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ConfigurationTransformationChainSingleton, cls).__new__(cls)
        return cls.instance

    def register(self, cls):
        self.transformation_chain.append(cls)
        logging.critical(f"Registered transformer: {cls.__name__}")

    def transform_configuration(self, configuration):
        configuration_result = {}
        configuration_input = configuration
        for link in self.transformation_chain:
            print(f"Calling configuration chain link {link.__name__}")
            configuration_result = link.process(configuration_input)
            configuration_input = configuration_result
        return configuration_result

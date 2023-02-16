import logging


class ConfigurationTransformer:
    transformers = []

    def __init_subclass__(cls, **kwargs):
        ConfigurationTransformationChainSingleton().register(cls)

    @staticmethod
    def process(configuration):
        return configuration


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

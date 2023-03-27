import copy

from openldap_opencensus_stats.config_transformers.base import ConfigurationTransformer


class CopyForEachDatabaseConfigurationTransformer(ConfigurationTransformer):
    @staticmethod
    def process(configuration):
        conf = copy.deepcopy(configuration)
        ldap_servers = conf.get('ldap_servers', [])
        for server_conf in ldap_servers:
            server_conf['object'] = copy.deepcopy(conf.get('object'))
        return conf

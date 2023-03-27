import logging

import ldap


class LdapServerPool:
    _ldap_servers = {}

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LdapServerPool, cls).__new__(cls)
        return cls.instance

    def get_ldap_server(self, **kwargs):
        if not self._ldap_servers.get(kwargs['database']):
            self._ldap_servers[kwargs['database']] = LdapServer(**kwargs)
            logging.critical(f"Registered LDAP Server: {kwargs['database']}")
        return self._ldap_servers[kwargs['database']]


class LdapServer:
    def __init__(self,
                 server_uri,
                 user_dn=None,
                 user_password=None,
                 database=None,
                 start_tls=False,
                 timeout=-1):
        if database is None:
            database = server_uri

        self.connection = None
        self.database = database
        self.user_dn = user_dn
        self.user_password = user_password

        self.connect_to_ldap(
            server_uri=server_uri,
            start_tls=start_tls,
            timeout=timeout
        )

    def connect_to_ldap(self, server_uri, start_tls=False, timeout=-1):
        if server_uri is None:
            logging.error(f"Failing to configure LDAP server {self.database} because no URI was supplied.")
            raise ValueError(f"An LDAP server URI must be defined for {self.database}")

        self.connection = ldap.ldapobject.ReconnectLDAPObject(server_uri)
        self.connection.timeout = timeout

        if start_tls:
            logging.info(f"Using StartTLS for {self.database}")
            self.connection.protocol_version = ldap.VERSION3
            self.connection.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
            self.connection.start_tls_s()

    def query(self, dn=None, scope=ldap.SCOPE_SUBTREE, attr_list=None):
        logging.debug(f"Querying {self.database} for {dn}")
        if attr_list is None:
            attr_list = ['+']
        if dn is None:
            logging.error(f"INTERNAL ERROR: Could not run a query because no DN was supplied")
            raise ValueError('Must specify a DN to query')

        try:
            self.connection.simple_bind_s(self.user_dn, self.user_password)
            return self.connection.search_s(dn, scope=scope, attrlist=attr_list)
        except (ldap.SERVER_DOWN, ldap.NO_SUCH_OBJECT, ldap.TIMEOUT):
            return []

    def query_dn_and_attribute(self, dn, attribute):
        results = self.query(dn, scope=ldap.SCOPE_BASE)
        if not results:
            return None

        result_dn, result_attributes = results[0]
        if attribute not in result_attributes:
            return None
        return result_attributes.get(attribute)

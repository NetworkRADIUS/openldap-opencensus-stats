import copy

from opencensus.stats import stats
from opencensus.tags import tag_map, tag_value, tag_key


class MetricSet:
    def __init__(self, ldap_server=None, ldap_statistics=None):
        self._ldap_server = ldap_server
        if not ldap_statistics or not isinstance(ldap_statistics, list):
            ldap_statistics = []
        self._ldap_statistics = copy.deepcopy(ldap_statistics)
        self._query_dns = set()

    def set_ldap_server(self, ldap_server):
        self._ldap_server = ldap_server

    def add_statistic(self, ldap_statistic):
        self._ldap_statistics.append(ldap_statistic)
        self._query_dns.add(ldap_statistic.query_dn)

    def collect(self):
        tag_keys = [tag_key.TagKey('database')]
        results = {}
        for query_dn in self._query_dns:
            results[query_dn] = dict([
                (result_dn, result_attributes)
                for result_dn, result_attributes in self._ldap_server.query(dn=query_dn)
            ])
        mmap = stats.stats.stats_recorder.new_measurement_map()
        for server_statistic in self._ldap_statistics:
            ldap_value = results.get(
                server_statistic.query_dn, {}
            ).get(
                server_statistic.dn, {}
            ).get(
                server_statistic.attribute
            )
            server_statistic.collect(ldap_server=self._ldap_server, measurement_map=mmap, ldap_value=ldap_value)
        tmap = tag_map.TagMap()
        tmap.insert(
            tag_keys[0],
            tag_value.TagValue(self._ldap_server.database)
        )
        mmap.record(tmap)

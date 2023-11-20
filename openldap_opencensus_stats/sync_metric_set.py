import logging
from datetime import datetime

from opencensus.stats import stats
from opencensus.tags import tag_map, tag_key, tag_value

from openldap_opencensus_stats.ldap_sync_statistic import LdapSyncStatistic


class SyncMetricSet:
    """
    Set of statistics for LDAP server synchronization.  This set
    represents a LDAP tree base, and contains statistics for
    the offset of each server that services that tree.

    So, if the tree is _dn=example,dn=org_ and the tree is serviced
    by servers ldap1, ldap2, and ldap3, then the resultant stats
    will:
    * Have a name of 'sync/{servername}/offset'
    * Have a BaseDN tag of 'dn=example,dn=org'
    * Have floating point values representing the number of seconds
      that the latest timestamp of their tree differs from the
      timestamp of the most recent change among the entire cluster
    """
    def __init__(self,
                 base_dn=None,
                 ldap_servers=None):
        if not base_dn:
            logging.error('INTERNAL: Sync metric set created without the base DN')
            raise ValueError('INTERNAL: Sync metric set created without the base DN')
        self._base_dn = base_dn
        if not ldap_servers:
            logging.error('INTERNAL: Sync metric set created without any LDAP servers')
            raise ValueError('INTERNAL: Sync metric set created without any LDAP servers')
        self.timestamp_attribute = 'contextCSN'

        self._statistics = {}
        for ldap_server in ldap_servers:
            self._statistics[ldap_server] = LdapSyncStatistic(
                name=f'sync/{ldap_server.database}/offset',
                description='Offset in seconds from the most recent update'
            )

    def collect(self):
        # Setup
        #################################################
        mmap = stats.stats.stats_recorder.new_measurement_map()

        # Main Processing
        #################################################
        watermarks = {}
        for ldap_server in self._statistics.keys():
            result = ldap_server.query_dn_and_attribute(
                dn=self._base_dn,
                attribute=self.timestamp_attribute
            )
            if (result and result[0]):
                result_str = result[0].decode('utf-8')
                segments = result_str.split('#')
                watermarks[ldap_server.database] = datetime.strptime(
                    segments[0],
                    '%Y%m%d%H%M%S.%fZ'
                )  # Record the timestamp

        high_water_mark = max(watermarks.values())
        for ldap_server, stat in self._statistics.items():
            if (ldap_server.database in watermarks):
                this_watermark = watermarks[ldap_server.database]
                offset = (high_water_mark - this_watermark).total_seconds()
                stat.collect(
                    ldap_server=ldap_server,
                    measurement_map=mmap,
                    offset=offset
                )
        # Record/Publish the data
        tmap = tag_map.TagMap()
        tmap.insert(
            tag_key.TagKey('BaseDN'),
            tag_value.TagValue(self._base_dn)
        )
        mmap.record(tmap)

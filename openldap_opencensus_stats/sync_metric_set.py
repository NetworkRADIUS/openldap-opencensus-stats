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
    * Have a rid tag with the rid of the provider.
    * Have floating point values representing the number of seconds
      that the latest timestamp of their tree differs from the
      timestamp of the most recent change among the entire cluster
    """
    def __init__(self,
                 base_dn=None,
                 ldap_servers=None,
                 report_servers=None):
        if not base_dn:
            logging.error('INTERNAL: Sync metric set created without the base DN')
            raise ValueError('INTERNAL: Sync metric set created without the base DN')
        self._base_dn = base_dn
        if not ldap_servers:
            logging.error('INTERNAL: Sync metric set created without any cluster LDAP servers')
            raise ValueError('INTERNAL: Sync metric set created without any cluster LDAP servers')
        if not report_servers:
            logging.error('INTERNAL: Sync metric set created without any reporting LDAP servers')
            raise ValueError('INTERNAL: Sync metric set created without any reporting LDAP servers')
        self.timestamp_attribute = 'contextCSN'

        self._statistics = {}
        for ldap_server in ldap_servers:
            report = ldap_server.database in report_servers
            self._statistics[ldap_server] = LdapSyncStatistic(
                name=f'sync/{ldap_server.database}/offset',
                description='Offset in seconds from the most recent update',
                unit='s',
                report=report
            )

    def collect(self):
        # Main Processing
        #################################################
        watermarks = {}
        for ldap_server in self._statistics.keys():
            result = ldap_server.query_dn_and_attribute(
                dn=self._base_dn,
                attribute=self.timestamp_attribute
            )
            if (result):
                # Record the timestamp from each contextCSN returned
                for value in result:
                    result_str = value.decode('utf-8')
                    segments = result_str.split('#')
                    rid = str(int(segments[2], 16))  # The rid is the third segment, in hex
                    if (rid in watermarks):
                        watermarks[rid].update({ldap_server.database: datetime.strptime(
                            segments[0], '%Y%m%d%H%M%S.%fZ'
                        )})
                    else:
                        watermarks[rid] = {ldap_server.database: datetime.strptime(
                            segments[0], '%Y%m%d%H%M%S.%fZ'
                        )}

        for rid in watermarks.keys():
            mmap = stats.stats.stats_recorder.new_measurement_map()

            high_water_mark = max(watermarks[rid].values())
            for ldap_server, stat in self._statistics.items():
                if (ldap_server.database in watermarks[rid]) and (stat.report):
                    this_watermark = watermarks[rid][ldap_server.database]
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
            tmap.insert(
                tag_key.TagKey('rid'),
                tag_value.TagValue(rid)
            )
            mmap.record(tmap)

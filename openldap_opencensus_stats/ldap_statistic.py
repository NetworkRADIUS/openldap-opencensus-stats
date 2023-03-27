# openldap_opencensus_stats
# Copyright (C) 2023  NetworkRADIUS
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import logging

from opencensus.stats import measure, view, aggregation, stats


class LdapStatistic:

    @staticmethod
    def log_and_raise(message=''):
        logging.error(message)
        raise ValueError(message)

    def __init__(self,
                 dn=None,
                 name=None,
                 attribute=None,
                 description='Unspecified',
                 unit='By',
                 value_function='value',
                 query_dn=None,
                 tag_keys=None):
        if tag_keys is None:
            tag_keys = []
        if dn is None:
            self.log_and_raise('Statistics definition must include the dn attribute')
        if name is None:
            self.log_and_raise('Statistics definition must include a name for the statistic')
        if attribute is None:
            self.log_and_raise('Statistics definition must include the attribute to query')
        if query_dn is None:
            self.log_and_raise('Statistics definition must include the DN to query')

        self.attribute = attribute
        self.dn = dn
        self.query_dn = query_dn
        self.measure = measure.MeasureFloat(
            name=name,
            description=description,
            unit=unit
        )

        self.view = view.View(
            name=name,
            description=description,
            columns=tag_keys,
            aggregation=aggregation.LastValueAggregation(),
            measure=self.measure
        )
        stats.stats.view_manager.register_view(self.view)
        self._value_function = lambda value: eval(value_function)

    def display_name(self):
        return f"{self.measure.name}:{self.attribute}"

    def collect(self, ldap_server=None, measurement_map=None, ldap_value=None):
        def display_name(server, statistic):
            return f"{server.database}:{statistic.display_name()}"

        if ldap_server is None:
            self.log_and_raise(f"INTERNAL ERROR: Failing to collect statistic {self.display_name()} "
                               f"because no LDAP server supplied.")
        if measurement_map is None:
            self.log_and_raise(f"INTERNAL ERROR: Failing to collect statistic {self.display_name()} "
                               f"because no measurement map was supplied.")

        # if not ldap_value:
        #     ldap_value = ldap_server.query_dn_and_attribute(self.dn, self.attribute)
        if ldap_value is None:
            logging.warning(f"No ldap_value collected for {display_name(ldap_server, self)}")
            return
        ldap_value_float = float(ldap_value[0])
        logging.debug(f"Collected ldap_value for {display_name(ldap_server, self)}: {ldap_value_float}")
        value = self._value_function(ldap_value_float)
        if ldap_value_float != value:
            logging.debug(f"  Transformed into: {value}")
        measurement_map.measure_float_put(self.measure, value)

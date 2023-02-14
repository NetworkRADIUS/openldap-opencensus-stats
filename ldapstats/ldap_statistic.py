# ldapstats
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
                 tag_keys=None):
        if tag_keys is None:
            tag_keys = []
        if dn is None:
            self.log_and_raise('Statistics definition must include the dn attribute')
        if name is None:
            self.log_and_raise('Statistics definition must include a name for the statistic')
        if attribute is None:
            self.log_and_raise('Statistics definition must include the attribute to query')

        self.attribute = attribute
        self.dn = dn
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

    def display_name(self):
        return f"{self.measure.name}:{self.attribute}"

    def collect(self, ldap_server=None, measurement_map=None):
        def display_name(server, statistic):
            return f"{server.database}:{statistic.display_name()}"

        if ldap_server is None:
            self.log_and_raise(f"INTERNAL ERROR: Failing to collect statistic {self.display_name()} "
                               f"because no LDAP server supplied.")
        if measurement_map is None:
            self.log_and_raise(f"INTERNAL ERROR: Failing to collect statistic {self.display_name()} "
                               f"because no measurement map was supplied.")

        value = ldap_server.query_dn_and_attribute(self.dn, self.attribute)
        if value is None:
            logging.warning(f"No value collected for {display_name(ldap_server, self)}")
            return
        logging.debug(f"Collected value for {display_name(ldap_server, self)}: {value}")
        measurement_map.measure_float_put(self.measure, float(value[0]))

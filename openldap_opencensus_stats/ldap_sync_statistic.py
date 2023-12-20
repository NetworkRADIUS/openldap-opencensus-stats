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


class LdapSyncStatistic:

    @staticmethod
    def log_and_raise(message=''):
        logging.error(message)
        raise ValueError(message)

    def __init__(self,
                 name=None,
                 description='Undescribed',
                 unit='ms',
                 tag_keys=None,
                 report=False):
        if name is None:
            self.log_and_raise('Statistics definition must include a name for the statistic')
        self.name = name
        self.report = report
        tag_keys = tag_keys or ['BaseDN', 'rid']

        self.measure = self.generate_measure(description, name, unit)
        self.view = self.generate_view(description, name, tag_keys, self.measure)
        stats.stats.view_manager.register_view(self.view)

    @staticmethod
    def generate_view(description, name, tag_keys, stat_measure):
        return view.View(
            name=name,
            description=description,
            columns=tag_keys,
            aggregation=aggregation.LastValueAggregation(),
            measure=stat_measure
        )

    @staticmethod
    def generate_measure(description, name, unit):
        return measure.MeasureFloat(
            name=name,
            description=description,
            unit=unit
        )

    def display_name(self,
                     ldap_server=None):
        return self.name

    def collect(self,
                ldap_server=None,
                measurement_map=None,
                offset=None):
        if offset is None:
            logging.warning(f"No offset collected for {self.display_name(ldap_server)}")
            return
        if measurement_map is None:
            logging.warning(f"No measurement_map for {self.display_name(ldap_server)}")
            return

        logging.debug(f"Collected ldap_value for {self.display_name(ldap_server)}: {offset}")
        measurement_map.measure_float_put(self.measure, offset)

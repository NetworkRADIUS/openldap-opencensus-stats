#!/usr/bin/python3

# openldap-opencensus-stats.py
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

import argparse
from openldap_opencensus_stats.configuration import Configuration


def parse_command_line():
    parser = argparse.ArgumentParser(description='Monitor the LDAP database.')
    parser.add_argument('config_file')

    return parser.parse_args()


def monitor():
    args = parse_command_line()
    configuration = Configuration(args.config_file)
    while True:
        metric_sets = configuration.metric_sets()
        for metric_set in metric_sets:
            metric_set.collect()
        configuration.sleep()


if __name__ == '__main__':
    monitor()

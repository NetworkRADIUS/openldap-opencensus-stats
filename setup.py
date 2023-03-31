import os
import shutil
import subprocess

from setuptools import setup, find_packages
from setuptools.command.install import install

VERSION = '0.0.6'
DESCRIPTION = 'OpenLDAP OpenCensus Statistics'
LONG_DESCRIPTION = 'A package to gather statistics for OpenLDAP and publish via OpenCensus.'


class InstallService(install):
    def run(self):
        # Run the regular installation
        install.run(self)

        # Install the service as well
        current_dir_path = os.path.dirname(os.path.realpath(__file__))
        service_file_source = os.path.join(current_dir_path, 'redhat/openldap-opencensus-stats.service')
        service_dest_path = os.path.join('/lib/systemd/system')
        if os.path.exists(service_dest_path):
            service_file_dest = '/lib/systemd/system/openldap_opencensus_stats.service'
            shutil.copyfile(service_file_source,
                            service_file_dest)
            shutil.chown(service_file_dest, 'root', 'root')
            subprocess.check_output(['systemctl', 'daemon-reload'])
            subprocess.check_output(['systemctl', 'enable', 'openldap-opencensus-stats.service'])
        else:
            print("Systemd does not seem to exist on this system.")


setup(
    name="openldap-opencensus-stats",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author="Mark Donnelly",
    author_email="mark@painless-security.com",
    license='AGPL 3.0',
    packages=find_packages(),
    install_requires=[
        'grpcio==1.47.0',
        'opencensus-ext-stackdriver==0.8.0',
        'opencensus-ext-prometheus',
        'opencensus==0.10.0',
        'python-ldap',
        'pyyaml',
    ],
    keywords='openldap opencensus metrics',
    entry_points={
        'console_scripts': [
            'openldap_opencensus_stats = openldap_opencensus_stats.openldap_opencensus_stats:main'
        ]
    },
    cmdclass={'install': InstallService},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        "Programming Language :: Python :: 3",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP",
    ]
)

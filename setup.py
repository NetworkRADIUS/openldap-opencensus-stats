from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'OpenLDAP OpenCensus Statistics'
LONG_DESCRIPTION = 'A package to gather statistics for OpenLDAP and publish via OpenCensus.'

setup(
    name="openldap-opencensus-stats",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author="Mark Donnelly",
    author_email="mark@painless-security.com",
    license='AGPL 3.0',
    packages=find_packages(),
    install_requires=[],
    keywords='openldap opencensus metrics',
    classifiers= [
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


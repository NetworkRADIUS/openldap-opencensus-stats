%global _python_bytecompile_extra 0

Name:           openldap-opencensus-stats
Version:        1.0.0
Release:        1%{?dist}
Summary:        Export OpenLDAP cn=Monitoring statistics via OpenCensus
BuildArch:      noarch

License:        AGPL
URL:            https://github.com/NetworkRADIUS/openldap-opencensus-stats
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-pytest
BuildRequires:  systemd-rpm-macros
Requires:       python3 systemd


%description
Export OpenLDAP cn=Monitoring statistics via OpenCensus

%prep
%setup -q


%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_bindir}
mkdir -p $RPM_BUILD_ROOT/%{_libdir}/python3.6/site-packages/
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/
mkdir -p $RPM_BUILD_ROOT/%{_unitdir}
cp %{name}.py $RPM_BUILD_ROOT/%{_bindir}/%{name}
cp -r ldapstats $RPM_BUILD_ROOT/%{_libdir}/python3.6/site-packages/
cp %{name}.yml $RPM_BUILD_ROOT/%{_sysconfdir}
cp redhat/%{name}.service $RPM_BUILD_ROOT/%{_unitdir}
cp redhat/%{name}.env $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%files
%{_bindir}/%{name}
%{_libdir}/python3.6/site-packages/
%{_sysconfdir}/%{name}.yml
%{_sysconfdir}/sysconfig/%{name}
%{_unitdir}/%{name}.service

%changelog
* Thu Mar   2 2023 Mark Donnelly <mark@painless-security.com> - 1.0.0
- First version being packaged

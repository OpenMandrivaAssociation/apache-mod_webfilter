#Module-Specific definitions
%define mod_name mod_webfilter
%define mod_conf A12_%{mod_name}.conf
%define mod_so %{mod_name}.so

Summary:	An apache content filter module
Name:		apache-%{mod_name}
Version:	0.6
Release:	%mkrel 11
Group:		System/Servers
License:	GPL
URL:		http://software.othello.ch/mod_webfilter/
Source0:	%{mod_name}-%{version}.tar.bz2
Source1:	%{mod_conf}.bz2
Source2:	mod_webfilter.txt.bz2
Patch0:		mod_webfilter-0.6-misc_fixes.patch
Patch1:		mod_webfilter-0.6-apache220.diff
Requires:	apache-mod_php
Requires:	apache-mod_proxy
BuildRequires:	autoconf2.5
BuildRequires:	automake1.7
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	apache-conf >= 2.2.0
Requires(pre):	apache >= 2.2.0
Requires:	apache-conf >= 2.2.0
Requires:	apache >= 2.2.0
BuildRequires:	apache-devel >= 2.2.0
BuildRequires:	file
BuildRequires:	gdbm-devel
Epoch:		1
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
Even though the free software community opposes censoring efforts
on the Internet, corporations still prefer to restrict the access
their employees have to the interet with technical measures.
Flexible solutions for URL filtering have so far mostly been
provided by commercial software vendors, free software
implementations usually were not versatile enough for commercial
environments. Unfortunately, this also meant that commercial
products were used for proxies and firewalls, and in the process
for many other things as well. 


We believe that mod_webfilter could improve this. In the webfilter
databases, each hostname or domain suffix is categorized with one
or more categories describing the content the site offers. The
administrator can configure the module with a whitelist and a
blacklist. If the hostname requested by a user has a category as
specified in the whitelist, the request is accepted, even if the
following blacklist test would reject it. If the hostname
requested has a category as specified in the black list, it is
rejected. All other requests are accepted, but tag filtering, an
additional capability of the module, is applied to the content
delivered for this URL. 


In principle, one database for blacklist and whitelist would be
enough, nevertheless the module allows the databases for whitelist
and blacklist to be different. This makes sense e.g. in a setting
where the blacklist is imported from some public database of
`indecent' URLs, and the whitelist is a locally maintained
database of exceptions. 

%prep

%setup -q -n %{mod_name}-%{version}
%patch0 -p1
%patch1 -p0

bzcat %{SOURCE2} > mod_webfilter.txt

# strip away annoying ^M
find . -type f|xargs file|grep 'CRLF'|cut -d: -f1|xargs perl -p -i -e 's/\r//'
find . -type f|xargs file|grep 'text'|cut -d: -f1|xargs perl -p -i -e 's/\r//'

%build
export WANT_AUTOCONF_2_5=1
libtoolize --copy --force; aclocal-1.7; autoconf; automake-1.7

export CFLAGS=`%{_sbindir}/apxs -q CFLAGS`

%configure2_5x --localstatedir=/var/lib \
    --with-apxs=%{_sbindir}/apxs \
    --with-htdocs=%{_var}/www/html/admin/mod_webfilter

make

pushd module
    # the autoconf stuff is a mess, we have to build the module "by hand"
    echo "static char *mod_webfilter_version = \"%{version}\";" > mod_webfilter_version.h
    %{_sbindir}/apxs -c mod_webfilter.c
    mv .libs ../
popd

%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%makeinstall_std

install -d %{buildroot}%{_var}/www/html/admin/%{mod_name}
install -d %{buildroot}/var/lib/%{mod_name}

# create some funny defaults ;)
echo "bad_sites no_visit" | %{buildroot}%{_bindir}/webfilter_create \
    %{buildroot}/var/lib/mod_webfilter/blacktypes

echo "good_sites go_visit" | %{buildroot}%{_bindir}/webfilter_create \
    %{buildroot}/var/lib/mod_webfilter/whitetypes

echo "www.microsoft.com bad_sites #bad" | %{buildroot}%{_bindir}/webfilter_create \
    %{buildroot}/var/lib/mod_webfilter/black

echo "nux.se good_sites #good" | %{buildroot}%{_bindir}/webfilter_create \
    %{buildroot}/var/lib/mod_webfilter/white

# remove silly things...
rm -f %{buildroot}%{_var}/www/html/admin/mod_webfilter/*

# install the web stuff
install -m644 web/whitelist.php %{buildroot}%{_var}/www/html/admin/mod_webfilter/whitelist.php

install -d %{buildroot}%{_libdir}/apache-extramodules
install -d %{buildroot}%{_sysconfdir}/httpd/modules.d

install -m0755 .libs/*.so %{buildroot}%{_libdir}/apache-extramodules/
bzcat %{SOURCE1} > %{buildroot}%{_sysconfdir}/httpd/modules.d/%{mod_conf}

install -d %{buildroot}%{_var}/www/html/addon-modules
ln -s ../../../..%{_docdir}/%{name}-%{version} %{buildroot}%{_var}/www/html/addon-modules/%{name}-%{version}

%post
if [ -f %{_var}/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart 1>&2;
fi

%postun
if [ "$1" = "0" ]; then
    if [ -f %{_var}/lock/subsys/httpd ]; then
	%{_initrddir}/httpd restart 1>&2
    fi
fi

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc doc/mod_webfilter.html AUTHORS ChangeLog NEWS README TODO mod_webfilter.txt
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/%{mod_conf}
%attr(0755,apache,apache) %dir /var/lib/mod_webfilter
%attr(0666,apache,apache) %config(noreplace) /var/lib/mod_webfilter/white
%attr(0666,apache,apache) %config(noreplace) /var/lib/mod_webfilter/black
%attr(0666,apache,apache) %config(noreplace) /var/lib/mod_webfilter/whitetypes
%attr(0666,apache,apache) %config(noreplace) /var/lib/mod_webfilter/blacktypes
%attr(0755,root,root) %{_bindir}/webfilter_*
%attr(0755,root,root) %{_libdir}/apache-extramodules/%{mod_so}
%{_var}/www/html/addon-modules/*
%attr(0644,root,root) %{_var}/www/html/admin/mod_webfilter/whitelist.php
%{_var}/www/html/admin/mod_webfilter/
%{_mandir}/man1/webfilter_*



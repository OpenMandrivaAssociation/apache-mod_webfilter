#Module-Specific definitions
%define mod_name mod_webfilter
%define mod_conf A12_%{mod_name}.conf
%define mod_so %{mod_name}.so

Summary:	An apache content filter module
Name:		apache-%{mod_name}
Version:	0.6
Release:	13
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
BuildRequires:	automake
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
libtoolize --copy --force; aclocal; autoconf; automake

export CFLAGS=`%{_bindir}/apxs -q CFLAGS`

%configure2_5x --localstatedir=/var/lib \
    --with-apxs=%{_bindir}/apxs \
    --with-htdocs=%{_var}/www/html/admin/mod_webfilter

make

pushd module
    # the autoconf stuff is a mess, we have to build the module "by hand"
    echo "static char *mod_webfilter_version = \"%{version}\";" > mod_webfilter_version.h
    %{_bindir}/apxs -c mod_webfilter.c
    mv .libs ../
popd

%install

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

%files
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
%{_mandir}/man1/webfilter_*




%changelog
* Tue May 24 2011 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-13mdv2011.0
+ Revision: 678440
- mass rebuild

* Mon Jan 03 2011 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-12mdv2011.0
+ Revision: 627738
- don't force the usage of automake1.7

* Sun Oct 24 2010 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-11mdv2011.0
+ Revision: 588086
- rebuild

* Mon Mar 08 2010 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-10mdv2010.1
+ Revision: 516250
- rebuilt for apache-2.2.15

* Sat Aug 01 2009 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-9mdv2010.0
+ Revision: 406672
- rebuild

* Mon Jul 14 2008 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-8mdv2009.0
+ Revision: 235128
- rebuild

* Thu Jun 05 2008 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-7mdv2009.0
+ Revision: 215671
- fix rebuild
- hard code %%{_localstatedir}/lib to ease backports

  + Pixel <pixel@mandriva.com>
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

* Fri Mar 07 2008 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-6mdv2008.1
+ Revision: 181968
- rebuild

  + Olivier Blin <oblin@mandriva.com>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Sat Sep 08 2007 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-5mdv2008.0
+ Revision: 82701
- rebuild


* Sat Mar 10 2007 Oden Eriksson <oeriksson@mandriva.com> 0.6-4mdv2007.1
+ Revision: 140776
- rebuild

* Thu Nov 09 2006 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-3mdv2007.1
+ Revision: 79556
- Import apache-mod_webfilter

* Mon Aug 07 2006 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-3mdv2007.0
- rebuild

* Fri Dec 16 2005 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-2mdk
- rebuilt against apache-2.2.0 (P1)

* Mon Nov 28 2005 Oden Eriksson <oeriksson@mandriva.com> 1:0.6-1mdk
- fix versioning

* Sun Jul 31 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_0.6-2mdk
- fix deps

* Fri Jun 03 2005 Oden Eriksson <oeriksson@mandriva.com> 2.0.54_0.6-1mdk
- rename the package
- the conf.d directory is renamed to modules.d
- use new rpm-4.4.x pre,post magic

* Sun Mar 20 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_0.6-4mdk
- use the %1

* Mon Feb 28 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_0.6-3mdk
- fix %%post and %%postun to prevent double restarts
- fix bug #6574

* Wed Feb 16 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_0.6-2mdk
- spec file cleanups, remove the ADVX-build stuff

* Tue Feb 08 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.53_0.6-1mdk
- rebuilt for apache 2.0.53

* Wed Sep 29 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.52_0.6-1mdk
- built for apache 2.0.52

* Fri Sep 17 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.51_0.6-1mdk
- built for apache 2.0.51

* Tue Jul 13 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 2.0.50_0.6-1mdk
- built for apache 2.0.50
- remove redundant provides

* Tue Jun 15 2004 Oden Eriksson <oden.eriksson@kvikkjokk.net> 2.0.49_0.6-1mdk
- built for apache 2.0.49


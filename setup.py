#!/usr/bin/env python

"""
distutils-based setup for grid-updates
"""

import sys
if sys.hexversion < int(0x020600f0):
    sys.stderr.write('ERROR: grid-updates requires Python 2.6 or newer.\n')
    sys.exit(1)

from distutils.core import setup
import platform
import shutil
extra_args = {}
SCRIPTS = []

if platform.system() == 'Windows':
    shutil.copy('scripts/grid-updates', 'scripts/grid-updates.py')
    script_name = 'scripts/grid-updates.py'
    try:
        import py2exe
        extra_args['console'] = ['scripts/grid-updates.py']
    except ImportError:
        pass
else:
    script_name = 'scripts/grid-updates'
SCRIPTS.append(script_name)

setup(name = 'grid-updates',
        # Get the version number dynamically after importing g-u
        version = __import__('gridupdates').__version__,
        py_modules = ['gridupdates'],
        description = 'Tahoe-LAFS helper script',
        long_description = """\
`grid-updates` is intended to help keep Tahoe-LAFS
nodes' configurations up-to-date.  It can retrieve
lists of introducers as well as news feeds from the
Tahoe grid.  This is useful for any public grid that
relies solely on volunteers.

On some public grids (especially the one on I2P) all
nodes, even introducers, are run by volunteers and may
disappear at any given time.  Maintaining a list
of all known introducers and distributing it to all
participants of the grid will ensure the best possible
connectivity for everyone.

Furthermore, there is no reliable way to contact node
operators.  This is why we want to encourage users to
subscribe to a news feed relevant to their Tahoe grid.
We hope it's going to be a way to inform unknown node
operators about their wrongly configured nodes, necessary
updates, recommended configuration changes and such.""",
        author = 'darrob, KillYourTV',
        author_email = 'darrob@mail.i2p, killyourtv@mail.i2p',
        url = 'http://darrob.i2p/grid-updates',
        license = 'Public Domain',
        data_files = [
           ('share/grid-updates', ['share/NEWS.atom.template',
            'share/news-stub.html', 'share/pandoc-template.html',
            'share/tahoe.css.patched', 'share/welcome.xhtml.patched']),
           ('share/doc/grid-updates', ['README.txt', 'INSTALL.txt']),
           ('share/man/man1', ['man/grid-updates.1'])],
        scripts = SCRIPTS,
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Environment :: Web Environment',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: Developers',
            'Intended Audience :: System Administrators',
            'License :: Public Domain',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: Microsoft :: Windows :: Windows NT/2000',
            'Operating System :: Microsoft :: Windows :: Windows Server 2003',
            'Operating System :: Microsoft :: Windows :: Windows Server 2008',
            'Operating System :: Microsoft :: Windows :: Windows Vista',
            'Operating System :: Microsoft :: Windows :: Windows XP',
            'Operating System :: POSIX',
            'Operating System :: POSIX :: AIX',
            'Operating System :: POSIX :: BSD',
            'Operating System :: POSIX :: BSD :: BSD/OS',
            'Operating System :: POSIX :: BSD :: FreeBSD',
            'Operating System :: POSIX :: BSD :: NetBSD',
            'Operating System :: POSIX :: BSD :: OpenBSD',
            'Operating System :: POSIX :: Linux',
            'Operating System :: POSIX :: SCO',
            'Operating System :: POSIX :: SunOS/Solaris',
            'Operating System :: Unix',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: OS Independent',
            'Natural Language :: English',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.0',
            'Programming Language :: Python :: 3.1',
            'Programming Language :: Python :: 3.2',
            'Topic :: Utilities',
            'Topic :: System :: Systems Administration',
            'Topic :: System :: Filesystems',
            'Topic :: System :: Distributed Computing',
            'Topic :: System :: Archiving :: Backup',
            'Topic :: System :: Archiving :: Mirroring',
            'Topic :: System :: Archiving',
            ],
            platforms = ['FreeBSD',
                         'Linux',
                         'MacOS X',
                         'POSIX',
                         'Unix',
                         'Windows'],
            provides = ['gridupdates'],
            **extra_args
        )

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

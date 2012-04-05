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

if platform.system() == 'Windows':
    shutil.copy('scripts/grid-updates', 'scripts/grid-updates.py')
    script_name = 'scripts/grid-updates.py'
    try:
        import py2exe
    except ImportError:
        pass
else:
    script_name = 'scripts/grid-updates'

setup(name = 'grid-updates',
        version = '1.0.0a',
        py_modules = ['gridupdates'],
        description = 'Tahoe-LAFS helper script',
        author = 'darrob',
        author_email = 'darrob@mail.i2p',
        url = 'http://darrob.i2p/grid-updates',
        license = 'Public Domain',
        data_files = [('share/grid-updates', ['etc/NEWS.atom.template',
            'etc/news-stub.html', 'etc/pandoc-template.html',
            'etc/tahoe.css.original',  'etc/tahoe.css.patched',
            'etc/welcome.xhtml.original', 'etc/welcome.xhtml.patched']),
            ('share/man/man1', ['man/grid-updates.1'])],
        scripts = [script_name],
        console = [script_name],
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
        )

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

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
        author = ['darrob','KillYourTV'],
        author_email = ['darrob@mail.i2p', 'killyourtv@mail.i2p'],
        url = 'http://darrob.i2p/grid-updates',
        license = 'Public Domain',
        data_files = [('share/grid-updates', ['etc/NEWS.atom.template',
            'etc/news-stub.html', 'etc/pandoc-template.html',
            'etc/tahoe.css.original',  'etc/tahoe.css.patched',
            'etc/welcome.xhtml.original', 'etc/welcome.xhtml.patched']),
            ('share/man/man1', ['man/grid-updates.1'])],
        scripts = [script_name],
        console = [script_name],
        )

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

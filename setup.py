#!/usr/bin/env python

"""
distutils-based setup for grid-updates
"""

import sys
if sys.hexversion < int(0x020600f0):
    sys.stderr.write('ERROR: grid-updates requires Python 2.6 or newer.\n')
    sys.exit(1)
elif sys.hexversion > int(0x030000f0) and sys.hexversion < int(0x030200f0):
    sys.stderr.write('ERROR: grid-updates requires Python 3.2 or newer.\n')
    sys.exit(1)

from distutils.core import setup, Command
import platform
import shutil
import subprocess
from gridupdates.version import __version__
extra_args = {}
SCRIPTS = []

if platform.system() == 'Windows':
    shutil.copy('grid-updates', 'grid-updates.py')
    script_name = 'grid-updates.py'
    try:
        import py2exe
        extra_args['console'] = ['grid-updates.py']
    except ImportError:
        pass
else:
    script_name = 'grid-updates'
SCRIPTS.append(script_name)

class Trial(Command):
    user_options = [ ("no-rterrors", None, "Don't print out tracebacks as they occur."),
                     ("rterrors", "e", "Print out tracebacks as they occur (default, so ignored)."),
                     ("until-failure", "u", "Repeat a test (specified by -s) until it fails."),
                     ("reporter=", None, "The reporter to use for this test run."),
                     ("quiet", None, "Don't display version numbers and paths of Tahoe dependencies."),
                   ] 
    def initialize_options(self):
        self.rterrors = False
        self.no_rterrors = False
        self.until_failure = False
        self.reporter = None
        self.quiet = False

    def finalize_options(self):
        pass

    def run(self):
        args = [sys.executable, './tests.py', '--verbose']
        rc = subprocess.call(args)
        sys.exit(rc)

setup(cmdclass = {'trial': Trial}, name = 'grid-updates',
        # Get the version number dynamically after importing g-u
        version = __version__,
        packages = ['gridupdates'],
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
        url = 'http://killyourtv.i2p/grid-updates',
        license = 'Public Domain',
        data_files = [
           ('share/grid-updates', ['share/NEWS.atom.template',
            'share/news-stub.html', 'share/pandoc-template.html',
            'share/tahoe.css.patched', 'share/welcome.xhtml.patched',
            'share/tahoe.css.patched19', 'share/welcome.xhtml.patched19']),
           ('share/doc/grid-updates', ['README.txt', 'INSTALL.txt']),
           ('share/doc/grid-updates/example-subscriptions',
                      ['share/example-subscriptions/repair-list.json.txt',
                       'share/example-subscriptions/introducers.json.txt']),
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

def run_command(args, cwd=None, verbose=False):
    try:
        # remember shell=False, so use git.cmd on windows, not just git
        p = subprocess.Popen(args, stdout=subprocess.PIPE, cwd=cwd)
    except EnvironmentError:
        # Python2.5 hack
        _, err, _= sys.exc_info()
        if verbose:
            print("unable to run %s" % args[0])
            print(e)
        return None
    stdout = p.communicate()[0].strip()
    if p.returncode != 0:
        if verbose:
            print("unable to run %s (error)" % args[0])
        return None
    return stdout

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

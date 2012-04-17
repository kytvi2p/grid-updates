#!/usr/bin/env python

from __future__ import print_function
from distutils.version import LooseVersion
from shutil import copyfile
import os
import re
import sys
# Maybe this is better than try -> except?
if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser
    from urllib import urlencode
    from urllib2 import HTTPError
    from urllib2 import urlopen
    from urllib2 import URLError
else:
    from configparser import ConfigParser as SafeConfigParser
    from urllib.request import urlopen
    from urllib.parse import urlencode
    from urllib.error import HTTPError
    from urllib.error import URLError

#from gridupdates import __patch_version__
from Modules.Functions import find_tahoe_dir
from Modules.Functions import find_datadir
from Modules.Functions import is_root
from Modules.Functions import get_tahoe_version

def install_news_stub(web_static_dir):
    """Copy a placeholder NEWS.html file to Tahoe's web.static directory to
    avoid 404 Errors (e.g. in the Iframe)."""
    targetfile = os.path.join(web_static_dir, 'NEWS.html')
    if not os.access(targetfile, os.F_OK):
        news_stub_file = os.path.join(find_datadir(), 'news-stub.html')
        copyfile(news_stub_file, targetfile)


class PatchWebUI(object):
    """This class implements the patching functions of grid-updates."""

    def __init__(self, tahoe_node_url, verbosity=0):
        self.verbosity = verbosity
        self.tahoe_node_url = tahoe_node_url
        if self.verbosity > 0:
            print("-- Patching Tahoe web console --")
        self.datadir = find_datadir()
        self.webdir = os.path.join(find_tahoe_dir(tahoe_node_url), 'web')
        self.filepaths = {'welcome.xhtml': [], 'tahoe.css': []}
        self.add_patch_filepaths()
        self.add_target_filepaths()
        if self.verbosity > 3:
            print('DEBUG: Data dir is: %s' % self.datadir)
            print('DEBUG: Tahoe web dir is: %s' % self.webdir)
            print('DEBUG: File paths:')
            print(self.filepaths)

    def run_action(self, mode, web_static_dir):
        """Call this method to execute the desired action (--patch-tahoe or
        --undo-patch-tahoe). It will run the necessary methods."""
        if self.compatible_version(self.tahoe_node_url):
            if mode == 'patch':
                if is_root():
                    print('WARN: Not installing NEWS.html placeholder (running'
                        ' as root.')
                else:
                    install_news_stub(web_static_dir)
                for uifile in list(self.filepaths.keys()):
                    patch_version = self.read_patch_version(
                                            self.filepaths [uifile][1])
                    if patch_version:
                        # file is patched
                        if not patch_version == __patch_version__:
                            if self.verbosity > 1:
                                print('INFO: A newer patch is available. '
                                                            'Installing.')
                            self.install_file(uifile)
                        else:
                            if self.verbosity > 2:
                                print('DEBUG: Patch is up-to-date.')
                    else:
                        self.backup_file(uifile)
                        self.install_file(uifile)
            if mode == 'undo':
                for uifile in list(self.filepaths.keys()):
                    self.restore_file(uifile)

    def compatible_version(self, tahoe_node_url):
        """Check Tahoe-LAFS's version to be known. We don't want to replace an
        unexpected and possibly redesigned web UI."""
        tahoe_version = LooseVersion(get_tahoe_version(tahoe_node_url))
        if tahoe_version >= LooseVersion('1.8.3') and \
                tahoe_version < LooseVersion('1.9'):
            if self.verbosity > 2:
                print('DEBUG: Found compatible version of Tahoe-LAFS (%s)'
                        % tahoe_version)
            return True
        else:
            if self.verbosity > 2:
                print('DEBUG: Incompatible version of Tahoe-LAFS (%s).'
                      ' Cannot patch web UI.' % tahoe_version)
            return False

    def add_patch_filepaths(self):
        """Add locations of patched web UI files to the location dict."""
        for patchfile in list(self.filepaths.keys()):
            filepath = os.path.join(self.datadir, patchfile + '.patched')
            if not os.path.exists(filepath):
                print('ERROR: Could not find %s.' % filepath, file=sys.stderr)
                sys.exit(1)
            self.filepaths[patchfile].append(filepath)

    def add_target_filepaths(self):
        """Add locations of original web UI files to the location dict."""
        for targetfile in list(self.filepaths.keys()):
            filepath = (os.path.join(self.webdir, targetfile))
            if not os.path.exists(filepath):
                print('ERROR: Could not find %s.' % filepath, file=sys.stderr)
                sys.exit(1)
            self.filepaths[targetfile].append(filepath)

    def read_patch_version(self, uifile):
        """Get the patches' versions from web UI files."""
        with open(uifile, 'r') as f:
            match = re.search(r'grid-updates\ patch\ VERSION=(.*)\ ',
                    f.readlines()[-1])
            if match:
                patch_version = match.group(1)
                if self.verbosity > 2:
                    print('DEBUG: Patch version of %s is: %s' %
                                            (uifile, patch_version))
                return patch_version
            else:
                return False

    def backup_file(self, uifile):
        """Make a backup copy of file if it doesn't already exist."""
        # TODO exception
        targetfile = self.filepaths[uifile][1]
        backupfile = targetfile + '.grid-updates.original'
        if not os.path.exists(backupfile):
            if self.verbosity > 2:
                print('DEBUG: Backing up %s' % targetfile)
            copyfile(targetfile, backupfile)
        else:
            if self.verbosity > 2:
                print('DEBUG: Backup of %s already exists.' % targetfile)


    def restore_file(self, uifile):
        """Restore a backup copy; undo patching."""
        # TODO exception
        targetfile  = self.filepaths[uifile][1]
        backupfile = targetfile + '.grid-updates.original'
        if self.verbosity > 1:
            print('INFO: Restoring %s' % backupfile)
        copyfile(backupfile, targetfile)


    def install_file(self, uifile):
        """Copy the patched version of a file into the tahoe directory."""
        # TODO exception
        patchedfile = self.filepaths[uifile][0]
        targetfile  = self.filepaths[uifile][1]
        if self.verbosity > 1:
            print('INFO: Installing patched version of %s' % targetfile)
        copyfile(patchedfile, targetfile)

"""This module handles WebUI patching duties."""

from __future__ import print_function
from distutils.version import LooseVersion
from shutil import copy2
import os
import re
import sys

from gridupdates.functions import find_tahoe_dir
from gridupdates.functions import find_datadir
from gridupdates.functions import is_root
from gridupdates.functions import compatible_version
from gridupdates.functions import get_tahoe_version
from gridupdates.functions import install_news_stub

class PatchWebUI(object):
    """This class implements the patching functions of grid-updates."""

    def __init__(self, latest_patch_version, tahoe_node_url, verbosity=0):
        self.verbosity = verbosity
        self.tahoe_node_url = tahoe_node_url
        ver = get_tahoe_version(tahoe_node_url)
        if ver is not None:
            self.tahoe_version = LooseVersion(ver)
        else:
            self.tahoe_version = ver
        print("Detected tahoe v%s" % self.tahoe_version)
        self.latest_patch_version = latest_patch_version
        self.datadir = find_datadir()
        self.is_compatible_version = compatible_version(self.tahoe_version,
                self.verbosity)
        if self.verbosity > 0 and ver is not None:
            print("-- Patching or checking Tahoe web console --")
        tahoe_dir = find_tahoe_dir(tahoe_node_url)
        if tahoe_dir is not None:
            self.webdir = os.path.join(tahoe_dir, 'web')
        else:
            sys.exit(1)
        self.filepaths = {'welcome.xhtml': [], 'tahoe.css': []}
        if ver is not None:
            self.add_patch_filepaths()
            self.add_target_filepaths()
        if self.verbosity > 3:
            print('DEBUG: Data dir is: %s' % self.datadir)
            print('DEBUG: Tahoe web dir is: %s' % self.webdir)
            if ver is not None and self.is_compatible_version:
                print('DEBUG: File paths:')
                print(self.filepaths)

    def run_action(self, mode, web_static_dir):
        """Call this method to execute the desired action (--patch-tahoe or
        --undo-patch-tahoe). It will run the necessary methods."""
        if self.is_compatible_version:
            if mode == 'patch':
                if is_root():
                    print('WARN: Not installing NEWS.html placeholder (running'
                        ' as root).')
                else:
                    install_news_stub(web_static_dir)
                for uifile in list(self.filepaths.keys()):
                    patch_version = self.read_patch_version(
                                            self.filepaths [uifile][1])
                    if patch_version:
                        # file is patched
                        if not patch_version == self.latest_patch_version:
                            if self.verbosity > 1:
                                print('INFO: A newer patch is available. '
                                                            'Installing.')
                            # Try to run function and abort if it fails. This
                            # will prevent g-u from trying the remaining files
                            # in the for loop.
                            # I'm not sure if this is the best way or a good
                            # idea at all.
                            if not self.install_file(uifile):
                                sys.exit(1)
                        else:
                            if self.verbosity > 0:
                                print('Patch is up-to-date.')
                    else:
                        # Only try to install the patched uifile if the backup
                        # succeeded.
                        if self.backup_file(uifile):
                            self.install_file(uifile)
                        else:
                            sys.exit(1)
            if mode == 'undo':
                for uifile in list(self.filepaths.keys()):
                    # Try to run function and abort if it fails. This
                    # will prevent g-u from trying the remaining files
                    # in the for loop.
                    # I'm not sure if this is the best way or a good
                    # idea at all.
                    if not self.restore_file(uifile):
                        sys.exit(1)

    def patch_update_available(self):
        """Function to check if patched WebUI files have available updates."""
        patch_version = self.read_patch_version(
                self.filepaths['welcome.xhtml'][1])
        if not patch_version:
            if self.verbosity > 0:
                print('Tahoe web console not patched.')
            return False
        if patch_version == self.latest_patch_version:
            if self.verbosity > 0:
                print('Patch is up-to-date.')
            return False
        else:
            if self.verbosity > 0:
                print('A newer patch version is available. '
                        'Run --patch-tahoe to install it.')
            return True

    def add_patch_filepaths(self):
        """Add locations of patched web UI files to the location dict."""
        for patchfile in list(self.filepaths.keys()):
            if self.tahoe_version < LooseVersion('1.9'):
                filepath = os.path.join(self.datadir, patchfile + '.patched')
            else:
                filepath = os.path.join(self.datadir, patchfile + '.patched19')
            if not os.path.exists(filepath):
                print('ERROR: Could not find %s.' % filepath, file=sys.stderr)
                sys.exit(1)
            self.filepaths[patchfile].append(filepath)

    def add_target_filepaths(self):
        """Add locations of original web UI files to the location dict."""
        for targetfile in list(self.filepaths.keys()):
            # tahoe.css is located in web, not web/static/ in Tahoe < 1.9
            if self.tahoe_version < LooseVersion('1.9'):
                filepath = (os.path.join(self.webdir, targetfile))
            elif targetfile == 'tahoe.css':
                filepath = (os.path.join(self.webdir, 'static', targetfile))
            else:
                filepath = (os.path.join(self.webdir, targetfile))
            if not os.path.exists(filepath):
                print('ERROR: Could not find %s.' % filepath, file=sys.stderr)
                sys.exit(1)
            self.filepaths[targetfile].append(filepath)

    def read_patch_version(self, uifile):
        """Get the patches' versions from web UI files."""
        with open(uifile, 'r') as welcome_file:
            match = re.search(r'grid-updates\ patch\ VERSION=(.*)\ ',
                    welcome_file.readlines()[-1])
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
        targetfile = self.filepaths[uifile][1]
        backupfile = targetfile + '.grid-updates.original'
        if not os.path.exists(backupfile):
            if self.verbosity > 2:
                print('DEBUG: Backing up %s' % targetfile)
            try:
                copy2(targetfile, backupfile)
            except IOError as exc:
                print('ERROR: Cannot backup original WUI:', exc, file=sys.stderr)
            else:
                if self.verbosity > 2:
                    print('DEBUG: Backup successful.')
                return True
        else:
            if self.verbosity > 2:
                print('DEBUG: Backup of %s already exists.' % targetfile)
            return True


    def restore_file(self, uifile):
        """Restore a backup copy; undo patching."""
        # TODO exception
        targetfile  = self.filepaths[uifile][1]
        backupfile = targetfile + '.grid-updates.original'
        if self.verbosity > 0:
            print('Restoring %s' % backupfile)
        try:
            copy2(backupfile, targetfile)
        except IOError as exc:
            print('ERROR: Cannot restore original WUI:', exc, file=sys.stderr)
        else:
            if self.verbosity > 2:
                print('DEBUG: File sucessfully restored.')
            os.remove(backupfile) # does this require a separate permission check?
            return True


    def install_file(self, uifile):
        """Copy the patched version of a file into the tahoe directory."""
        # TODO exception
        patchedfile = self.filepaths[uifile][0]
        targetfile  = self.filepaths[uifile][1]
        if self.verbosity > 0:
            print('Installing patched version of %s' % targetfile)
        try:
            copy2(patchedfile, targetfile)
        except IOError as exc:
            print('ERROR: Cannot install patched WUI files:', exc, file=sys.stderr)
        else:
            return True

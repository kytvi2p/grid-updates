#!/usr/bin/env python

from __future__ import print_function
import json
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

#from gridupdates import __version__

class Updates(object):
    """This class implements the update functions of grid-updates."""

    def __init__(self, output_dir, url, verbosity=0):
        self.verbosity = verbosity
        self.output_dir = output_dir
        self.url = url
        if self.verbosity > 0:
            print("-- Looking for script updates --")
        self.dir_url = self.url + '/?t=json'

    def run_action(self, mode):
        """Call this method to execute the desired action (--check-version or
        --download-update). It will run the necessary methods."""
        if self.new_version_available():
            if mode == 'check':
                self.print_versions()
            elif mode == 'download':
                self.download_update()
        else:
            if self.verbosity > 0:
                print('No update available.')

    def get_version_number(self):
        """Determine latest available version number by parsing the Tahoe
        directory."""
        if self.verbosity > 1:
            print("INFO: Checking for new version.")
        if self.verbosity > 2:
            print('DEBUG: Parsing Tahoe dir: %s.' % self.dir_url)
        # list Tahoe dir
        try:
            json_dir = urlopen(self.dir_url).read().decode('utf8')
        except HTTPError as exc:
            print('ERROR: Could not access the Tahoe directory:', exc,
                    file=sys.stderr)
            sys.exit(1)
        except URLError as urlexc:
            print("ERROR: %s trying to access Tahoe directory: %s." %
                                (urlexc, self.dir_url), file=sys.stderr)
            sys.exit(1)
        else:
            # parse json index of dir
            file_list = list(json.loads(json_dir)[1]['children'].keys())
            # parse version numbers
            version_numbers = []
            for filename in file_list:
                if re.match("^grid-updates-.*\.tar\.gz$", filename):
                    version = (re.sub(r'^grid-updates-(.*)\.tar\.gz', r'\1',
                                                               filename))
                    version_numbers.append(version)
            if not version_numbers:
                print('ERROR: No versions of grid-updates available in this'
                                        ' Tahoe directory.', file=sys.stderr)
                return
            latest_version = sorted(version_numbers)[-1]
            if self.verbosity > 1:
                print('INFO: Current version: %s; newest available: %s.' %
                        (__version__, latest_version))
            return latest_version

    def new_version_available(self):
        """Determine if the local version is smaller than the available
        version."""
        self.latest_version = self.get_version_number()
        if __version__ < self.latest_version:
            return True
        else:
            return False

    def print_versions(self):
        """Print current and available version numbers."""
        # verbosity doesn't matter in this case; it's a user request:
        #if self.verbosity > 0:
        if self.new_version_available:
            print('There is a new version available: %s (currently %s).' %
                    (self.latest_version, __version__))
        else:
            print('This version of grid-updates (%s) is up-to-date.' %
                                                             __version__)

    def download_update(self):
        """Download script tarball."""
        download_url = (
                self.url + '/grid-updates-v' + self.latest_version + '.tgz')
        if self.verbosity > 1:
            print("INFO: Downloading", download_url)
        try:
            remote_file = urlopen(download_url)
        except HTTPError as exc:
            print('ERROR: Could not download the tarball:', exc,
                    file=sys.stderr)
            sys.exit(1)
        except URLError as urlexc:
            print("ERROR: %s trying to download tarball from  %s." %
                            (urlexc, download_url), file=sys.stderr)
            sys.exit(1)
        local_file = os.path.join(self.output_dir, 'grid-updates-v' +
                                    self.latest_version + '.tgz')
        try:
            with open(local_file,'wb') as output:
                output.write(remote_file.read())
        except IOError as exc:
            print('ERROR: Could not write to local file:', exc,
                    file=sys.stderr)
            sys.exit(1)
        else:
            if self.verbosity > 0:
                print('Success: downloaded an update to %s.' %
                        os.path.abspath(local_file))

from __future__ import print_function
import json
import os
import re
import sys
# Maybe this is better than try -> except?
if sys.version_info[0] == 2:
    from urllib2 import HTTPError
    from urllib2 import urlopen
    from urllib2 import URLError
else:
    from urllib.request import urlopen
    from urllib.error import HTTPError
    from urllib.error import URLError

class Update(object):
    """This class implements the update functions of grid-updates."""

    def __init__(self, current_version, output_dir, url, verbosity=0):
        self.verbosity = verbosity
        self.version = current_version
        self.output_dir = output_dir
        self.url = url
        if self.verbosity > 0:
            print("-- Looking for script updates --")
        if self.url is not None:
            self.dir_url = self.url + '/?t=json'
            self.latest_version = self.get_version_number()

    def run_action(self, mode, requested_dist='tar'):
        """Call this method to execute the desired action (--check-version or
        --download-update). It will run the necessary methods."""
        # TODO Requested download type should be checked for validity before
        # making any network connections.

        if self.new_version_available():
            if mode == 'check':
                self.print_versions()
            elif mode == 'download':
                download_filename = self.gen_download_filename(requested_dist)
                self.download(download_filename, 'update')
                self.download(download_filename + '.sig', 'signature')
            return True
        else:
            if self.verbosity > 0:
                print('No update available.')
                return False

    def gen_download_filename(self, req_dist):
        """This function accepts a file extension and returns the filename of a
        grid-updates update."""
        basename = ('grid-updates-' + self.latest_version)
        available_formats = {
                'tar': basename + '.tar.gz',
                'zip': basename + '.zip',
                'py2exe': basename + '.py2exe.exe',
                'exe': basename + '.win32.exe',
                'deb': 'grid-updates_' + self.latest_version + '-1_all.deb'
                }
        if req_dist not in available_formats.keys():
            raise ValueError("""You've requested an unknown update format. Valid formats: %s """ %
                    [ i for i in list(available_formats.keys())])

        return available_formats[req_dist]

    def get_version_number(self):
        """Determine latest available version number by parsing the Tahoe
        directory."""
        if self.verbosity > 1:
            print("INFO: Checking for new version.")
        if self.verbosity > 2:
            print('DEBUG: Parsing Tahoe dir: %s.' % self.dir_url)
        # list Tahoe dir
        if self.url is None:  # will only happen when testing
            return
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
                        (self.version, latest_version))
            return latest_version

    def new_version_available(self):
        """Determine if the local version is smaller than the available
        version."""
        if self.version < self.latest_version:
            return True
        else:
            return False

    def print_versions(self):
        """Print current and available version numbers."""
        # verbosity doesn't matter in this case; it's a user request:
        #if self.verbosity > 0:
        if self.new_version_available:
            print('There is a new version available: %s (currently %s).' %
                    (self.latest_version, self.version))
        else:
            print('This version of grid-updates (%s) is up-to-date.' %
                                                             self.version)

    def download(self, download_filename, filetype):
        """Download script tarball and/or signature."""
        download_url = (self.url + '/' + download_filename)
        if self.verbosity > 1:
            print("INFO: Downloading", download_url)
        try:
            remote_file = urlopen(download_url)
        except HTTPError as exc:
            print('ERROR: Could not download', download_filename, ': ', exc,
                    file=sys.stderr)
            sys.exit(1)
        except URLError as urlexc:
            print("ERROR: %s trying to download %s from  %s." %
                            (download_filename, urlexc, download_url), file=sys.stderr)
            sys.exit(1)
        local_file = os.path.join(self.output_dir, download_filename)
        try:
            with open(local_file,'wb') as output:
                output.write(remote_file.read())
        except IOError as exc:
            print('ERROR: Could not write to local file:', exc,
                    file=sys.stderr)
            sys.exit(1)
        else:
            if self.verbosity > 0:
                print('Success: Saved %s file to %s.' %
                        (filetype, os.path.abspath(local_file)))

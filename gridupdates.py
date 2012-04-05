#!/usr/bin/env python

"""grid-updates is a helper script for Tahoe-LAFS nodes."""

from __future__ import print_function
from shutil import copyfile, rmtree
import json
import optparse
import os
import platform
import re
import sys
import tarfile
import tempfile # use os.tmpfile()?
# Maybe this is better than try -> except?
if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser
    from urllib import urlencode
    from urllib2 import HTTPError
    from urllib2 import urlopen
else:
    from configparser import ConfigParser as SafeConfigParser
    from urllib.request import urlopen
    from urllib.parse import urlencode
    from urllib.error import HTTPError
import random
from distutils.version import LooseVersion
import subprocess
from datetime import datetime
from uuid import uuid4

__author__ = ['darrob', 'KillYourTV']
__license__ = "Public Domain"
__version__ = "1.0.0a"
__maintainer__ = ['darrob', 'KillYourTV']
__email__ = ['darrob@mail.i2p', 'killyourtv@mail.i2p']
__status__ = "Development"

# TODO illegal var name?
__patch_version__ = '1.8.3-gu5'

# General Functions
# =================
def gen_full_tahoe_uri(node_url, uri):
    """Generate a complete, accessible URL from a Tahoe URI."""
    return node_url + '/uri/' + uri

def tahoe_dl_file(url, verbosity=0):
    """Download a file from the Tahoe grid; returns the raw response."""
    if verbosity > 1:
        print('INFO: Downloading subscription from the Tahoe grid.')
    if verbosity > 2:
        print("DEBUG: Downloading from: %s" % url)
    try:
        response = urlopen(url)
    except HTTPError as exc:
        print('ERROR: Could not download the file:', exc, file=sys.stderr)
        sys.exit(1)
    else:
        return response

def is_valid_introducer(uri):
    """Check if the introducer address has the correct format."""
    if re.match(r'^pb:\/\/.*@', uri):
        return True
    else:
        return False

def parse_result(result, mode, unhealthy, verbosity=0):
    """Parse JSON response from Tahoe deep-check operation.
    Optionally prints status output; returns number of unhealthy shares.
    """
    #   [u'check-and-repair-results', u'cap', u'repaircap',
    #   u'verifycap', u'path', u'type', u'storage-index']
    if mode == 'deep-check':
        if not ('check-and-repair-results' in
                list(json.loads(result).keys())):
            # This would be the final 'stats' line.
            return 'unchecked', unhealthy
        uritype   = json.loads(result)['type']
        path   = json.loads(result)['path']
        status = (json.loads(result)
                    ['check-and-repair-results']
                    ['post-repair-results']
                    ['summary'])
        # Print
        if verbosity > 1:
            if uritype == 'directory' and not path:
                print('   <root>: %s' % status)
            else:
                print('   %s: %s' % (path[0], status))
        # Count unhealthy
        if status.startswith('Unhealthy'):
            unhealthy += 1
        return status, unhealthy
    elif mode == 'one-check':
        status = json.loads(result)['post-repair-results']['summary']
        # Count unhealthy
        if status.startswith('Unhealthy'):
            unhealthy += 1
        return status, unhealthy

def find_datadir():
    """Determine datadir (e.g. /usr/share) from the grid-updates executable's
    location."""
    bindir = os.path.dirname(sys.argv[0])
    if os.path.exists(os.path.join(bindir, 'share')):
        datadir = os.path.join(bindir, 'share/grid-updates')
    elif os.path.exists(os.path.join(bindir, 'etc')):
        datadir = os.path.join(bindir, 'etc')
    else:
        datadir = os.path.abspath(bindir) + '/../share/grid-updates'
    if not os.path.exists(datadir):
        print('ERROR: Does not exist: %s.' % datadir, file=sys.stderr)
    return datadir

def find_tahoe_dir(tahoe_node_url):
    """Determine the location of the tahoe installation directory and included
    'web' directory by parsing the tahoe web console."""
    webconsole = urlopen(tahoe_node_url)
    match = re.search(r'.*\ \'(.*__init__.pyc)', webconsole.read())
    tahoe_dir = os.path.dirname(match.group(1))
    return tahoe_dir

def get_tahoe_version(tahoe_node_url):
    """Determine Tahoe-LAFS version number from web console."""
    webconsole = urlopen(tahoe_node_url)
    match = re.search(r'allmydata-tahoe:\ (.*),', webconsole.read())
    version = match.group(1)
    return version

def remove_temporary_dir(directory, verbosity=0):
    """Remove a (temprorary) directory."""
    try:
        rmtree(directory)
    except:
        print("ERROR: Couldn't remove temporary dir: %s." % directory,
                file=sys.stderr)
    else:
        if verbosity > 2:
            print('DEBUG: Removed temporary dir: %s.' % directory)

def install_news_stub(web_static_dir):
    """Copy a placeholder NEWS.html file to Tahoe's web.static directory to
    avoid 404 Errors (e.g. in the Iframe)."""
    targetfile = os.path.join(web_static_dir, 'NEWS.html')
    if not os.access(targetfile, os.F_OK):
        news_stub_file = os.path.join(find_datadir(), 'news-stub.html')
        copyfile(news_stub_file, targetfile)



# Actions
# =======
def action_repair(uri_dict, verbosity=0):
    """Repair all (deep-check) Tahoe shares in a dictionary."""
    if verbosity > 0:
        print("-- Repairing the grid-updates Tahoe shares. --")
    mode = 'deep-check'
    unhealthy = 0
    # shuffle() to even out chances of all shares to get repaired
    # (Is this useful?)
    sharelist = list(uri_dict.keys())
    random.shuffle(sharelist)
    for sharename in sharelist:
        repair_uri = uri_dict[sharename][1]
        results = repair_share(sharename, repair_uri, mode, verbosity)
        if verbosity > 1:
            print('INFO: Post-repair results for: %s' % sharename)
        for result in results:
            status, unhealthy = parse_result(result.decode('utf8'),
                                                mode, unhealthy, verbosity)
        if unhealthy == 1:
            sub = 'object'
        else:
            sub = 'objects'
        if verbosity > 1:
            print("  Status: %d %s unhealthy." % (unhealthy, sub))
    if verbosity > 0:
        print("Deep-check of grid-updates shares completed: "
                            "%d %s unhealthy." % (unhealthy, sub))

def action_comrepair(tahoe_node_url, uri_dict, verbosity=0):
    """The --community-repair command. Repair all shares in the uri_dict."""
    if verbosity > 0:
        print("-- Repairing Tahoe shares. --")
    # TODO This action should probably be renamed to something less
    # specific, because there is a variety of use cases for it that don't
    # have to be community oriented.
    unhealthy = 0
    url = uri_dict['comrepair'][1] + '/community-repair.json.txt'
    subscriptionfile = tahoe_dl_file(url, verbosity).read()
    # shuffle() to even out chances of all shares to get repaired
    sharelist = (list(json.loads(subscriptionfile.decode('utf8'))
                                            ['community-shares']))
    random.shuffle(sharelist)
    for share in sharelist:
        sharename  = share['name']
        repair_uri = gen_full_tahoe_uri(tahoe_node_url, share['uri'])
        mode       = share['mode']
        if mode == 'deep-check':
            results = repair_share(sharename, repair_uri, mode, verbosity)
            for result in results:
                status, unhealthy = parse_result(result.decode('utf8'),
                                                    mode, unhealthy, verbosity)
            if verbosity > 1:
                if unhealthy == 1:
                    sub = 'object'
                else:
                    sub = 'objects'
                print("  Deep-check completed: %d %s unhealthy."
                                                % (unhealthy, sub))
        if mode == 'one-check':
            result = repair_share(sharename, repair_uri, mode, verbosity)
            status, unhealthy = parse_result(result.decode('utf8'), mode,
                                                        unhealthy, verbosity)
            if verbosity > 1:
                print("  Status: %s" % status)
    if verbosity > 0:
        print('Repairs have completed (unhealthy: %d).' % unhealthy)

def repair_share(sharename, repair_uri, mode, verbosity=0):
    """Run (deep-)checks including repair and add-lease on a Tahoe share;
    returns response in JSON format."""
    if verbosity > 0:
        print("Repairing '%s' share (%s)." % (sharename, mode))
    if mode == 'deep-check':
        params = urlencode({'t': 'stream-deep-check',
                            'repair': 'true',
                            'add-lease': 'true'}
                            ).encode('utf8')
    elif mode == 'one-check':
        params = urlencode({'t': 'check',
                            'repair': 'true',
                            'add-lease': 'true',
                            'output': 'json'}
                            ).encode('utf8')
    else:
        print("ERROR: 'mode' must either be 'one-check' or 'deep-check'.",
                                                        file=sys.stderr)
        sys.exit(1)
    if verbosity > 2:
        print('DEBUG: Running urlopen(%s, %s).' % (repair_uri, params))
    try:
        response = urlopen(repair_uri, params)
    except HTTPError as exc:
        # TODO Doesn't catch all errors
        print('ERROR: Could not run %s for %s: %s', (mode, sharename, exc),
                                                        file=sys.stderr)
        sys.exit(1)
    else:
        if mode == 'deep-check':
            # deep-check returns multiple JSON objects, 1 per line
            result = response.readlines()
        elif mode == 'one-check':
            # one-check returns a single JSON object
            result = response.read()
        return result
    finally:
        # TODO This can cause: UnboundLocalError: local variable 'response'
        # referenced before assignment
        response.close()


class List(object):
    """This class implements the introducer list related functions of
    grid-updates."""

    def __init__(self, nodedir, url, verbosity=0):
        self.verbosity = verbosity
        self.nodedir = nodedir
        self.url = url + '/introducers.json.txt'
        if self.verbosity > 0:
            print("-- Updating introducers --")
        self.old_list = []
        self.introducers = os.path.join(self.nodedir, 'introducers')
        self.introducers_bak = self.introducers + '.bak'
        (self.old_introducers, self.old_list) = self.read_existing_list()
        json_response = tahoe_dl_file(self.url, verbosity)
        self.intro_dict = self.create_intro_dict(json_response)

    def run_action(self, mode):
        """Call this method to execute the desired action (--merge-introducers
        or --sync-introducers)."""
        if self.lists_differ():
            self.backup_original()
            if mode == 'merge':
                self.merge_introducers()
            if mode == 'sync':
                self.sync_introducers()
        else:
            if self.verbosity > 0:
                print('Introducer list already up-to-date.')

    def create_intro_dict(self, json_response):
        """Compile a dictionary of introducers (uri->name,active) from a JSON
        object."""
        try:
            new_list = json.loads(json_response.read().decode('utf8'))
        except:
            # TODO specific exception
            print("ERROR: Couldn't parse new JSON introducer list.",
                                                        file=sys.stderr)
        intro_dict = {}
        for introducer in new_list['introducers']:
            uri = introducer['uri']
            if is_valid_introducer(uri):
                if self.verbosity > 2:
                    print('DEBUG: Valid introducer address: %s' % uri)
                intro_dict[uri] = (introducer['name'], introducer['active'])
            else:
                if self.verbosity > 0:
                    print("WARN: '%s' is not a valid Tahoe-LAFS introducer "
                            "address. Skipping.")
        return intro_dict

    def read_existing_list(self):
        """Read the local introducers file as a single string (to be written
        again) and as individual lines. """
        if self.verbosity > 2:
            print('DEBUG: Reading the local introducers file.')
        try:
            with open(self.introducers, 'r') as intlist:
                old_introducers = intlist.read()
                old_list = old_introducers.splitlines()
        except IOError as exc:
            print('WARN: Cannot read local introducers files:', exc,
                    file=sys.stderr)
            print('WARN: Are you sure you have a compatible version of '
                    'Tahoe-LAFS?', file=sys.stderr)
            print('WARN: Pretending to have read an empty introducers list.',
                    file=sys.stderr)
            old_introducers = ''
            old_list = []
        return (old_introducers, old_list)

    def backup_original(self):
        """Copy the old introducers file to introducers.bak."""
        try:
            with open(self.introducers_bak, 'w') as intbak:
                intbak.write(self.old_introducers)
        except IOError:
            print('ERROR: Cannot create backup file introducers.bak',
                    file=sys.stderr)
            sys.exit(1)
        else:
            if self.verbosity > 2:
                print('DEBUG: Created backup of local introducers.')

    def lists_differ(self):
        """Compile lists of introducers: all active, locally missing and
        expired."""
        self.subscription_uris = []
        for introducer in list(self.intro_dict.keys()):
            # only include active introducers
            if self.intro_dict[introducer][1]:
                self.subscription_uris.append(introducer)
            else:
                if self.verbosity > 2:
                    print('INFO: Skipping disabled introducer: %s' %
                            self.intro_dict[introducer][0])
        if sorted(self.subscription_uris) == sorted(self.old_list):
            if self.verbosity > 2:
                print('DEBUG: Introducer lists identical.')
            return False
        # Compile lists of new (to be added and outdated (to be removed) #
        # introducers
        self.new_intros = list(set(self.subscription_uris) - set(self.old_list))
        self.expired_intros = list(set(self.old_list) -
                set(self.subscription_uris))
        return True

    def merge_introducers(self):
        """Add newly discovered introducers to the local introducers file;
        remove nothing."""
        if self.verbosity > 1:
            expired_intros = list(set(self.old_list) -
                    set(self.subscription_uris))
            for intro in expired_intros:
                print("INFO: Introducer not in subscription list: %s" % intro)
        try:
            with open(self.introducers, 'a') as intlist:
                for new_intro in self.new_intros:
                    if self.intro_dict[new_intro][1]:
                        if self.verbosity > 0:
                            print('New introducer: %s.' %
                                    self.intro_dict[new_intro][0])
                        intlist.write(new_intro + '\n')
        except IOError as exc:
            print('ERROR: Could not write to introducer file: %s' % exc,
                    file=sys.stderr)
            sys.exit(1)
        else:
            if self.verbosity > 0:
                print('Successfully updated the introducer list.'
                      ' Changes will take effect upon restart of the node.')

    def sync_introducers(self):
        """Add and remove introducers in the local list to make it identical to
        the subscription's."""
        try:
            with open(self.introducers, 'w') as intlist:
                for introducer in self.subscription_uris:
                    intlist.write(introducer + '\n')
        except IOError as exc:
            print('ERROR: Could not write to introducer file: %s' %
                    exc, file=sys.stderr)
            sys.exit(1)
        else:
            if self.verbosity > 0:
                for introducer in self.new_intros:
                    print('Added introducer: %s' %
                            self.intro_dict[introducer][0])
                for introducer in self.expired_intros:
                    if introducer in self.intro_dict:
                        print('Removed introducer: %s' %
                                self.intro_dict[introducer][0])
                    else:
                        print('Removed unknown introducer: %s' % introducer)
                print('Successfully updated the introducer list.'
                      ' Changes will take effect upon restart of the node.')


class News(object):
    """This class implements the --download-news function of grid-updates."""

    def __init__(self, tahoe_node_dir, web_static_dir, url, verbosity=0):
        self.verbosity = verbosity
        self.tahoe_node_dir = tahoe_node_dir
        self.web_static = web_static_dir
        self.url = url
        if self.verbosity > 0:
            print("-- Updating NEWS --")
        self.local_news = os.path.join(self.tahoe_node_dir, 'NEWS')
        self.tempdir = tempfile.mkdtemp()
        self.local_archive = os.path.join(self.tempdir, 'NEWS.tgz')

    def run_action(self):
        """Call this method to execute the desired action (--download-news). It
        will run the necessary methods."""
        if self.verbosity > 2:
            print('DEBUG: Selected action: --download-news')
        self.download_news()
        self.extract_tgz()
        if self.news_differ():
            self.print_news()
        else:
            if self.verbosity > 0:
                print('There are no news.')
        # Copy in any case to make easily make sure that all versions
        # (escpecially the HTML version) are always present:
        self.install_files()

    def download_news(self):
        """Download NEWS.tgz file to local temporary file."""
        url = self.url + '/NEWS.tgz'
        if self.verbosity > 1:
            print("INFO: Downloading news from the Tahoe grid.")
        if self.verbosity > 2:
            print("INFO: Downloading", url)
        try:
            response = urlopen(url).read()
        except HTTPError:
            print("ERROR: Couldn't find %s." % url, file=sys.stderr)
            sys.exit(1)
        else:
            with open(self.local_archive,'wb') as output:
                output.write(response)

    def extract_tgz(self):
        """Extract NEWS.tgz archive into temporary directory."""
        if self.verbosity > 2:
            print('DEBUG: Extracting %s to %s.' %
                    (self.local_archive, self.tempdir))
        try:
            tar = tarfile.open(self.local_archive, 'r:gz')
            for newsfile in ['NEWS', 'NEWS.html', 'NEWS.atom']:
                tar.extract(newsfile, self.tempdir)
            tar.close()
        except tarfile.TarError:
            print('ERROR: Could not extract NEWS.tgz archive.', file=sys.stderr)
            sys.exit(1)

    def news_differ(self):
        """Compare the local and newly downloaded NEWS files to determine of
        there are new news. Return True/False."""
        try:
            locnews = open(self.local_news, 'r')
        except:
            if self.verbosity > 2:
                print('DEBUG: No NEWS file found in node directory.')
            differ = True
        else:
            with open(os.path.join(self.tempdir, 'NEWS'), 'r') as tempnews:
                if locnews.read() != tempnews.read():
                    if self.verbosity > 2:
                        print('DEBUG: NEWS files differ.')
                    differ = True
                else:
                    if self.verbosity > 2:
                        print('DEBUG: NEWS files seem to be identical.')
                    differ = False
                locnews.close()
        return differ

    def print_news(self):
        """Print the contents of the newly downloaded NEWS file in the
        temporary directory."""
        with open(os.path.join(self.tempdir, 'NEWS'), 'r') as tempnews:
            for line in tempnews.readlines():
                print('  | ' + line, end='')

    def install_files(self):
        """Copy extracted NEWS files to their intended locations."""
        try:
            copyfile(os.path.join(self.tempdir, 'NEWS'), self.local_news)
            for newsfile in ['NEWS.html', 'NEWS.atom']:
                copyfile(os.path.join(self.tempdir, newsfile),
                        os.path.join(self.tahoe_node_dir,
                                        self.web_static,
                                        newsfile))
        except:
            print("ERROR: Couldn't copy one or more NEWS files into the "
                  "node directory.", file=sys.stderr)
            sys.exit(1)
        else:
            if self.verbosity > 2:
                print('DEBUG: Copied NEWS files into the node directory.')



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
        else:
            # parse json index of dir
            file_list = list(json.loads(json_dir)[1]['children'].keys())
            # parse version numbers
            version_numbers = []
            for filename in file_list:
                if re.match("^grid-updates-v.*\.tgz$", filename):
                    version = (re.sub(r'^grid-updates-v(.*)\.tgz', r'\1',
                                                               filename))
                    version_numbers.append(version)
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


class PatchWebUI(object):
    """This class implements the patching functions of grid-updates."""

    def __init__(self, tahoe_node_url, verbosity=0):
        self.verbosity = verbosity
        self.tahoe_node_url = tahoe_node_url
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
        if self.verbosity > 2:
            print('DEBUG: Restoring %s' % backupfile)
        copyfile(backupfile, targetfile)


    def install_file(self, uifile):
        """Copy the patched version of a file into the tahoe directory."""
        # TODO exception
        patchedfile = self.filepaths[uifile][0]
        targetfile  = self.filepaths[uifile][1]
        if self.verbosity > 2:
            print('DEBUG: Installing patched version of %s' % targetfile)
        copyfile(patchedfile, targetfile)


class MakeNews(object):
    """This class implements the --make-news function of grid-updates."""

    def __init__(self, verbosity=0):
        self.verbosity = verbosity
        self.tempdir = tempfile.mkdtemp()
        if self.verbosity > 2:
            print('DEBUG: tempdir is: %s' % self.tempdir)
        # check for pandoc and markdown
        # find template locations
        self.datadir = find_datadir()

    def run_action(self, md_file, output_dir):
        """Call this method to execute the desired action (--make-news). It
        will run the necessary methods."""
        html_file = self.compile_md(md_file)
        if html_file:
            atom_file = self.compile_atom()
            include_list = [md_file, html_file, atom_file]
            self.make_tarball(include_list, output_dir)
            remove_temporary_dir(self.verbosity, self.tempdir)

    def compile_md(self, mdfile):
        """Compile an HTML version of the Markdown source of NEWS; return the
        file path."""
        source = mdfile
        output_html = os.path.join(self.tempdir, 'NEWS.html')
        pandoc_tmplt = os.path.join(self.datadir, 'pandoc-template.html')
        try:
            subprocess.call(["pandoc",
                            "-w", "html",
                            "-r", "markdown",
                            "--email-obfuscation", "none",
                            "--template", pandoc_tmplt,
                            "--output", output_html,
                            source])
        except OSError as ose:
            print("ERROR: Couldn't run pandoc subprocess: %s" % ose)
        else:
            return output_html

    def compile_atom(self):
        """Create an Atom news feed file from a template by adding the current
        date and an UUID (uuid4 is supposed to be generated randomly); returns
        the file path."""
        atom_tmplt = os.path.join(self.datadir, 'NEWS.atom.template')
        output_atom = os.path.join(self.tempdir, 'NEWS.atom')
        with open(atom_tmplt, 'r') as f:
            formatted = f.read()
        # insert date
        now = datetime.now()
        formatted = re.sub(r'REPLACEDATE', now.isoformat(), formatted)
        # insert UUID
        uuid = str(uuid4())
        formatted = re.sub(r'REPLACEID', uuid, formatted)
        with open(output_atom, 'w') as f:
            f.write(formatted)
        return output_atom

    def make_tarball(self, include_list, output_dir):
        """Add files from a list to NEWS.tgz in --output-dir; remove directory
        structure."""
        tarball = os.path.join(output_dir, 'NEWS.tgz')
        tar = tarfile.open(tarball, mode='w:gz')
        try:
            for item in include_list:
                tarinfo = tar.gettarinfo(item, arcname=os.path.basename(item))
                tarinfo.uid = tarinfo.gid = 0
                tarinfo.uname = tarinfo.gname = "root"
                tar.addfile(tarinfo, open(item, 'rb'))
        finally:
            tar.close()


def parse_opts(argv):
    """Parse options given in config files or the command line."""
    # CONFIGURATION PARSING
    # =====================

    # Parse settings:
    #   1. Set default fall-backs.
    #   2. Parse configuration files.
    #       (Apply defaults if necessary.)
    #   3. Parse command line options.
    #       (Use values from 2. as defaults.)

    # OS-dependent settings
    #for k in os.environ: print "%s: %s" %(k, os.environ[k])
    operating_system = platform.system()
    if operating_system == 'Windows':
        default_tahoe_node_dir = os.path.join(os.environ['USERPROFILE'],
                                                        ".tahoe")
        config_locations = [
                os.path.join(os.environ['APPDATA'],
                                        'grid-updates',
                                        'config.ini')]
    else:
        default_tahoe_node_dir = os.path.join(os.environ['HOME'], ".tahoe")
        # Config file list
        # Check for XDG environment variables; use defaults if not set
        # The order of config files matters to ConfigParser
        config_locations = []
        # 1. XDG_CONFIG_DIRS
        try:
            xdg_config_dir_list = os.path.join(
                        os.environ['XDG_CONFIG_DIRS']).split(':')
        except KeyError:
            config_locations.append(os.path.join('/etc', 'xdg',
                                                'grid-updates',
                                                'config.ini'))
        else:
            for directory in xdg_config_dir_list:
                config_locations.append(os.path.join(directory,
                                                    'grid-updates',
                                                    'config.ini'))
        # 2. XDG_CONFIG_HOME
        try:
            xdg_config_home = os.environ['XDG_CONFIG_HOME']
        except KeyError:
            config_locations.append(os.path.join(
                                                os.environ['HOME'],
                                                ".config",
                                                'grid-updates',
                                                'config.ini'))
        else:
            config_locations.append(os.path.join(xdg_config_home,
                                                'grid-updates',
                                                'config.ini'))

    # 1. Default settings
    #tahoe_node_dir = os.path.abspath('testdir')
    default_tahoe_node_url = 'http://127.0.0.1:3456'
    default_list_uri = ('URI:DIR2-RO:t4fs6cqxaoav3r767ce5t6j3h4:'
            'gvjawwbjljythw4bjhgbco4mqn43ywfshdi2iqdxyhqzovrqazua')
    default_news_uri = ('URI:DIR2-RO:hx6754mru4kjn5xhda2fdxhaiu:'
            'hbk4u6s7cqfiurqgqcnkv2ckwwxk4lybuq3brsaj2bq5hzajd65q')
    default_script_uri = ('URI:DIR2-RO:mjozenx3522pxtqyruekcx7mh4:'
            'eaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a')
    default_comrepair_uri = ('URI:DIR2-RO:ysxswonidme22ireuqrsrkcv4y:'
            'nqxg7ihxnx7eqoqeqoy7xxjmsqq6vzfjuicjtploh4k7mx6viz3a')
    default_output_dir = os.path.abspath(os.getcwd())

    # 2. Configparser
    # uses defaults (above) if not found in config file
    config = SafeConfigParser({
        'tahoe_node_dir': default_tahoe_node_dir,
        'tahoe_node_url': default_tahoe_node_url,
        'list_uri': default_list_uri,
        'news_uri': default_news_uri,
        'script_uri': default_script_uri,
        'comrepair_uri': default_comrepair_uri,
        'output_dir': default_output_dir,
        })

    # Check if any configuration files are available; get their settings if
    # they are, apply standard settings if they aren't.
    available_cfg_files = []

    # Determine which config files are available
    for loc in config_locations:
        if os.access(loc, os.R_OK):
            available_cfg_files.append(loc)
    # Also parse specified config file
    if '--config' in argv:
        pos = argv.index('--config')
        available_cfg_files.append(argv[pos + 1])

    if available_cfg_files:
        # Parse config files in standard locations if available
        config.read(available_cfg_files)
        tahoe_node_dir = config.get('OPTIONS', 'tahoe_node_dir')
        tahoe_node_url = config.get('OPTIONS', 'tahoe_node_url')
        list_uri       = config.get('OPTIONS', 'list_uri')
        news_uri       = config.get('OPTIONS', 'news_uri')
        script_uri     = config.get('OPTIONS', 'script_uri')
        comrepair_uri  = config.get('OPTIONS', 'comrepair_uri')
        output_dir     = config.get('OPTIONS', 'output_dir')
    else:
        # Set standard fallback values if no config files found
        tahoe_node_dir = default_tahoe_node_dir
        tahoe_node_url = default_tahoe_node_url
        list_uri       = default_list_uri
        news_uri       = default_news_uri
        script_uri     = default_script_uri
        comrepair_uri  = default_comrepair_uri
        output_dir     = default_output_dir

    # 3. Optparse
    # defaults to values from Configparser
    parser = optparse.OptionParser()
    # actions
    action_opts = optparse.OptionGroup(
        parser, 'Actions',
        'These arguments control which actions will be executed.')
    action_opts.add_option('-s', '--sync-introducers',
            action = 'store_true',
            dest = "sync",
            default = False,
            help = "Synchronize the local list of introducers with the "
                    "subscription's.")
    action_opts.add_option('-m', '--merge-introducers',
            action = 'store_true',
            dest = "merge",
            default = False,
            help = 'Downloads and merges list of introducers into your '
                    'local list.')
    action_opts.add_option('-n', '--download-news',
            action = 'store_true',
            dest = "news",
            default = False,
            help = 'Downloads news feed.')
    action_opts.add_option('-r', '--repair',
            action = 'store_true',
            dest = "repair",
            default = False,
            help = 'Run a deep-check and repair on all grid-updates shares.')
    action_opts.add_option('--check-version',
            action = 'store_true',
            dest = "check_version",
            default = False,
            help = 'Check for a new version of grid-updates.')
    action_opts.add_option('--download-update',
            action = 'store_true',
            dest = "download_update",
            default = False,
            help = 'Download a new version of grid-updates.')
    action_opts.add_option('-R', '--community-repair',
            action = 'store_true',
            dest = "comrepair",
            default = False,
            help = 'TODO')
    action_opts.add_option('--patch-tahoe',
            action = 'store_true',
            dest = "patch_ui",
            default = False,
            help = ('Patch the Tahoe Web UI to display grid-updates news '
                                                'in an IFrame.'))
    action_opts.add_option('--undo-patch-tahoe',
            action = 'store_true',
            dest = "undo_patch_ui",
            default = False,
            help = 'Restore the original Tahoe Web console files.')
    action_opts.add_option('--make-news',
            action = 'store',
            dest = "mknews_md_file",
            help = 'Compile a grid-updates-compatible NEWS.tgz file from'
                    ' a Markdown file.')
    parser.add_option_group(action_opts)
    # options
    other_opts = optparse.OptionGroup(
        parser, 'Options',
        'These arguments can override various settings.')
    other_opts.add_option('-d', '--node-dir',
            action = 'store',
            dest = "tahoe_node_dir",
            default = tahoe_node_dir,
            help = 'Specify the Tahoe node directory.')
    other_opts.add_option('-u', '--node-url',
            action = 'store',
            dest = 'tahoe_node_url',
            default = tahoe_node_url,
            help = "Specify the Tahoe gateway node's URL.")
    other_opts.add_option('--list-uri',
            action = 'store',
            dest = 'list_uri',
            default = list_uri,
            help = 'Override default location of introducers list.')
    other_opts.add_option('--news-uri',
            action = 'store',
            dest = 'news_uri',
            default = news_uri,
            help = 'Override default location of news list.')
    other_opts.add_option('--script-uri',
            action = 'store',
            dest = 'script_uri',
            default = script_uri,
            help = 'Override default location of script releases.')
    other_opts.add_option('--comrepair-uri',
            action = 'store',
            dest = 'comrepair_uri',
            default = comrepair_uri,
            help = ('Override default location of additional repair '
                    'subscription.'))
    other_opts.add_option('-o', '--output-dir',
            action = 'store',
            dest = 'output_dir',
            default = output_dir,
            help = ('Override default output directory (%s) for script '
                    'update downloads and NEWS.tgz generation.'
                    % os.getcwd()))
    parser.add_option_group(other_opts)
    # remaining
    parser.add_option('-v',
            action='count',
            dest='verbosity',
            default=1,
            help = 'Increase verbosity (-vv for debug mode).')
    parser.add_option('-q',
            action='store_const',
            const=0,
            dest='verbosity',
            help = 'Turn off verbosity.')
    parser.add_option('-V', '--version',
            dest = "version",
            action = "store_true",
            default = False,
            help = 'Display version information.')
    # Fake option: this option will not be accessed directly; --config is used
    # for ConfigParser (see above); this entry exists here for completeness of
    # --help
    parser.add_option('-c', '--config',
            action = 'store',
            dest = 'config',
            help = 'Manually specify a configuration file.')
    # parse arguments
    (opts, args) = parser.parse_args()

    # DEBUG
    if opts.verbosity > 2:
        print('DEBUG: The following options have been set:')
        for opt in [
                opts.tahoe_node_dir,
                opts.tahoe_node_url,
                opts.list_uri,
                opts.news_uri,
                opts.script_uri,
                opts.comrepair_uri,
                opts.output_dir]:
            print('  %s' % opt)

    return (opts, args)

def main():
    """Main function: run selected actions."""
    # Parse config files and command line arguments
    (opts, args) = parse_opts(sys.argv)

    # ACTION PARSING AND EXECUTION
    # ============================

    # Check for at least 1 mandatory option
    if (not opts.version
    and not opts.merge
    and not opts.sync
    and not opts.news
    and not opts.repair
    and not opts.check_version
    and not opts.download_update
    and not opts.comrepair
    and not opts.patch_ui
    and not opts.undo_patch_ui
    and not opts.mknews_md_file):
        print('ERROR: You need to specify an action. Please see %s --help.' %
                sys.argv[0], file=sys.stderr)
        sys.exit(2)

    if opts.version:
        print('grid-updates version: %s.' % __version__)
        sys.exit(0)

    # conflicting options
    if opts.merge and opts.sync:
        print('ERROR: --merge-introducers & --sync-introducers are '
            ' mutually exclusive actions.', file=sys.stderr)
        sys.exit(2)

    # Parse tahoe options (find web.static for NEWS files)
    tahoe_cfg_path = os.path.join(opts.tahoe_node_dir, 'tahoe.cfg')
    tahoe_config = SafeConfigParser({'web.static': 'public_html'})
    # TODO figure out why try..except doesn't work
    #try:
    #    tahoe_config.read(tahoe_cfg_path)
    #except ConfigParser.NoSectionError:
    #    print('ERROR: Could not parse tahoe.cfg.', file=sys.stderr)
    #    sys.exit(1)
    #else:
    #    print(tahoe_config.get('node', 'web.static'))
    #    web_static_dir = os.path.abspath(
    #            os.path.join(
    #                    tahoe_node_dir,
    #                    tahoe_config.get('node', 'web.static')))
    if os.access(tahoe_cfg_path, os.R_OK):
        # Also use existence of tahoe.cfg as an indicator of a Tahoe node
        # directory
        tahoe_config.read(tahoe_cfg_path)
        web_static_dir = os.path.abspath(
                os.path.join(
                        opts.tahoe_node_dir,
                        tahoe_config.get('node', 'web.static')))
    else:
        print('ERROR: Could not parse tahoe.cfg. Not a valid Tahoe node.',
                file=sys.stderr)
        sys.exit(1)

    # Tahoe node dir validity check (in addition to the above tahoe.cfg check)
    if not os.access(opts.tahoe_node_dir, os.W_OK):
        print("ERROR: Need write access to", opts.tahoe_node_dir,
                file=sys.stderr)
        sys.exit(1)

    # generate URI dictionary
    uri_dict = {'list': (opts.list_uri,
                                    gen_full_tahoe_uri(
                                            opts.tahoe_node_url,
                                            opts.list_uri)),
                'news': (opts.news_uri,
                                    gen_full_tahoe_uri(
                                            opts.tahoe_node_url,
                                            opts.news_uri)),
                'script': (opts.script_uri,
                                    gen_full_tahoe_uri(
                                            opts.tahoe_node_url,
                                            opts.script_uri)),
                'comrepair': (opts.comrepair_uri,
                                    gen_full_tahoe_uri(
                                            opts.tahoe_node_url,
                                            opts.comrepair_uri))
                }

    # Check URI validity
    for uri in list(uri_dict.values()):
        if not re.match('^URI:', uri[0]):
            print( "'%s' is not a valid Tahoe URI. Aborting." % uri[0])
            sys.exit(1)

    if opts.verbosity > 2:
        print("DEBUG: Tahoe node dir is", opts.tahoe_node_dir)

    # Run actions
    # -----------
    # The try-except constructs are there to make the program continue with the
    # next action if one fails. It might not be the most elegant way.
    if opts.merge or opts.sync:
        intlist = List(opts.tahoe_node_dir,
                        uri_dict['list'][1],
                        opts.verbosity)
        if opts.sync:
            intlist.run_action('sync')
        elif opts.merge:
            intlist.run_action('merge')
    if opts.news:
        news = News(opts.tahoe_node_dir,
                    web_static_dir,
                    uri_dict['news'][1],
                    opts.verbosity)
        news.run_action()
    if opts.check_version or opts.download_update:
        update = Updates(opts.output_dir,
                            uri_dict['script'][1],
                            opts.verbosity)
        if opts.check_version:
            update.run_action('check')
        elif opts.download_update:
            update.run_action('download')
    if opts.patch_ui or opts.undo_patch_ui:
        webui = PatchWebUI(opts.tahoe_node_url, opts.verbosity)
        if opts.patch_ui:
            webui.run_action('patch', web_static_dir)
        elif opts.undo_patch_ui:
            webui.run_action('undo', web_static_dir)
    if opts.mknews_md_file:
        mknews = MakeNews(opts.verbosity)
        mknews.run_action(opts.mknews_md_file, opts.output_dir)
    if opts.repair:
        action_repair(uri_dict, opts.verbosity)
    if opts.comrepair:
        action_comrepair(opts.tahoe_node_url, uri_dict, opts.verbosity)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\ngrid-updates interrupted by user.")
        sys.exit(1)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
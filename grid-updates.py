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
    from configparser import SafeConfigParser
    from urllib.request import urlopen
    from urllib.parse import urlencode
    from urllib.error import HTTPError
import random

__author__ = ['darrob', 'KillYourTV']
__license__ = "Public Domain"
__version__ = "1.0.0a"
__maintainer__ = ['darrob', 'KillYourTV']
__email__ = ['darrob@mail.i2p', 'killyourtv@mail.i2p']
__status__ = "Development"

def tahoe_dl_file(verbosity, url):
    """Download a file from the Tahoe grid; returns the raw response."""
    if verbosity > 1:
        print('INFO: Downloading subscription from the Tahoe grid.')
    if verbosity > 2:
        print("DEBUG: Downloading from: %s" % url)
    try:
        response = urlopen(url)
    except HTTPError as exc:
        print('ERROR: Could not download the file:', exc, file=sys.stderr)
        exit(1)
    else:
        return response


class List:
    def __init__(self, verbosity, nodedir, url):
        self.verbosity = verbosity
        self.nodedir = nodedir
        self.url = url + '/introducers.json.txt'
        if self.verbosity > 0:
            print("-- Updating introducers --")
        self.old_list = []
        self.introducers = os.path.join(self.nodedir, 'introducers')
        self.introducers_bak = self.introducers + '.bak'
        (self.old_introducers, self.old_list) = self.read_existing_list()
        json_response = tahoe_dl_file(verbosity, self.url)
        self.intro_dict = self.create_intro_dict(json_response)

    def create_intro_dict(self, json_response):
        try:
            new_list = json.loads(json_response.read().decode('utf8'))
        except:
            # TODO specific exception
            print("ERROR: Couldn't parse new JSON introducer list.",
                                                        file=sys.stderr)
        intro_dict = {}
        for introducer in new_list['introducers']:
            intro_dict[introducer['uri']] = (introducer['name'],
                    introducer['active'])
        return intro_dict

    def read_existing_list(self):
        """Read the local introducers file as a single string (to be written
        again) and as individual lines. """
        if self.verbosity > 2:
            print('DEBUG: Reading the local introducers file.')
        try:
            with open(self.introducers, 'r') as f:
                old_introducers = f.read()
                old_list = old_introducers.splitlines()
        except IOError as exc:
            print('WARN: Cannot read local introducers files:', exc,
                    file=sys.stderr)
            print('WARN: Are you sure you have a compatible version of Tahoe-LAFS?',
                    file=sys.stderr)
            print('WARN: Pretending to have read an empty introducers list.',
                    file=sys.stderr)
            old_introducers = ''
            old_list = []
        return (old_introducers, old_list)

    def backup_original(self):
        """Copy the old introducers file to introducers.bak."""
        try:
            with open(self.introducers_bak, 'w') as f:
                f.write(self.old_introducers)
        except IOError:
            print('ERROR: Cannot create backup file introducers.bak',
                    file=sys.stderr)
            exit(1)
        else:
            if self.verbosity > 2:
                print('DEBUG: Created backup of local introducers.')

    def lists_differ(self):
        """Compile lists of introducers: all active, locally missing and
        expired."""
        self.subscription_uris = []
        for introducer in self.intro_dict.keys():
            # only include active introducers
            if self.intro_dict[introducer][1]:
                self.subscription_uris.append(introducer)
            else:
                if self.verbosity > 1:
                    print('INFO: Skipping inactive introducer: %s' %
                            self.intro_dict[introducer][0])
        if sorted(self.subscription_uris) == sorted(self.old_list):
            if self.verbosity > 0:
                print('INFO: Introducer list already up-to-date.')
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
            expired_intros = list(set(self.old_list) - set(self.subscription_uris))
            for intro in expired_intros:
                print("INFO: Introducer not in subscription list: %s" % intro)
        try:
            with open(self.introducers, 'a') as f:
                for new_intro in self.new_intros:
                    if self.intro_dict[new_intro][1]:
                        if self.verbosity > 0:
                            print('New introducer: %s.' %
                                    self.intro_dict[new_intro][0])
                        f.write(new_intro + '\n')
        except IOError as exc:
            print('ERROR: Could not write to introducer file: %s' % exc,
                    file=sys.stderr)
            exit(1)

    def sync_introducers(self):
        """Add and remove introducers in the local list to make it identical to
        the subscription's."""
        try:
            with open(self.introducers, 'w') as f:
                for introducer in self.subscription_uris:
                    f.write(introducer + '\n')
        except IOError as exc:
            print('ERROR: Could not write to introducer file: %s' %
                    exc, file=sys.stderr)
            exit(1)
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


class News:
    def __init__(self, verbosity, nodedir, web_static_dir, url):
        self.verbosity = verbosity
        self.nodedir = nodedir
        self.web_static = web_static_dir
        self.url = url
        if self.verbosity > 0:
            print("-- Updating NEWS --")
        self.local_news = os.path.join(self.nodedir, 'NEWS')
        self.tempdir = tempfile.mkdtemp()
        self.local_archive = os.path.join(self.tempdir, 'NEWS.tgz')

    def download_news(self):
        """Download NEWS.tgz file to local temporary file."""
        url = self.url + '/NEWS.tgz'
        if self.verbosity > 1:
            print("INFO: Downloading", url)
        try:
            response = urlopen(url).read()
        except HTTPError:
            print("ERROR: Couldn't find %s." % url, file=sys.stderr)
            exit(1)
        else:
            with open(self.local_archive,'wb') as output:
                output.write(response)

    def extract_tgz(self):
        """Extract NEWS.tgz archive into temporary directory."""
        if self.verbosity > 2:
            print('DEBUG: Extracting %s to %s.' % \
                    (self.local_archive, self.tempdir))
        try:
            tar = tarfile.open(self.local_archive, 'r:gz')
            for newsfile in ['NEWS', 'NEWS.html', 'NEWS.atom']:
                tar.extract(newsfile, self.tempdir)
            tar.close()
        except tarfile.TarError:
            print('ERROR: Could not extract NEWS.tgz archive.', file=sys.stderr)
            exit(1)

    def news_differ(self):
        """Compare NEWS files and print to stdout if they differ (if allowed
        by verbosity level)."""
        # TODO convoluted; can probably be solved with a single try..except
        if os.access(self.local_news, os.F_OK):
            try:
                ln = open(self.local_news, 'r+')
            except IOError as exc:
                print('ERROR: Cannot access NEWS file: %s' % exc,
                        file=sys.stderr)
                exit(1)
            else:
                with open(os.path.join(self.tempdir, 'NEWS'), 'r') as tn:
                    if ln.read() != tn.read():
                        if self.verbosity > 2:
                            print('DEBUG: NEWS files differ.')
                        if self.verbosity > 0:
                            tn.seek(0)
                            for line in tn.readlines():
                                print('  | ' + line, end='')
                    else:
                        if self.verbosity > 1:
                            print('INFO: NEWS files seem to be identical.')
                if self.verbosity > 2:
                    print('DEBUG: Successfully extracted and' \
                            'compared NEWS files.')
            finally:
                ln.close()
        else:
            with open(os.path.join(self.tempdir, 'NEWS'), 'r') as tn:
                if self.verbosity > 2:
                    print('DEBUG: No NEWS file found in node directory.')
                if self.verbosity > 0:
                    for line in tn.readlines():
                        print('  | ' + line, end='')

    def install_files(self):
        """Copy extracted NEWS files to their intended locations."""
        try:
            copyfile(os.path.join(self.tempdir, 'NEWS'), self.local_news)
            for newsfile in ['NEWS.html', 'NEWS.atom']:
                copyfile(os.path.join(self.tempdir, newsfile),
                        os.path.join(self.nodedir, self.web_static, newsfile))
        except:
            print("ERROR: Couldn't copy one or more NEWS files into the" \
                  "node directory.", file=sys.stderr)
            exit(1)
        else:
            if self.verbosity > 2:
                print('DEBUG: Copied NEWS files into the node directory.')

    def remove_temporary(self):
        """Clean up temporary NEWS files."""
        try:
            rmtree(self.tempdir)
        except:
            print("ERROR: Couldn't remove temporary dir: %s." % self.tempdir,
                    file=sys.stderr)
        else:
            if self.verbosity > 2:
                print('DEBUG: Removed temporary dir: %s.' % self.tempdir)


class Updates:
    def __init__(self, verbosity, output_dir, url):
        self.verbosity = verbosity
        self.output_dir = output_dir
        self.url = url
        if self.verbosity > 0:
            print("-- Looking for script updates --")
        self.dir_url = self.url + '/?t=json'
        if self.new_version_available():
            self.new_version_available = True
        else:
            self.new_version_available = False

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
            exit(1)
        else:
            # parse json index of dir
            file_list = list(json.loads(json_dir)[1]['children'].keys())
            # parse version numbers
            version_numbers = []
            for filename in file_list:
                if re.match("^grid-updates-v.*\.tgz$", filename):
                    v = (re.sub(r'^grid-updates-v(.*)\.tgz', r'\1', filename))
                    version_numbers.append(v)
            latest_version = sorted(version_numbers)[-1]
            if self.verbosity > 1:
                print('INFO: Current version: %s; newest available: %s.' % \
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
            print('There is a new version available: %s (currently %s).' %\
                    (self.latest_version, __version__))
        else:
            print('This version of grid-updates (%s) is up-to-date.' % \
                                                             __version__)

    def download_update(self):
        """Download script tarball."""
        if self.new_version_available:
            download_url = \
                    self.url + '/grid-updates-v' + self.latest_version + '.tgz'
            if self.verbosity > 1:
                print("INFO: Downloading", download_url)
            try:
                remote_file = urlopen(download_url)
            except HTTPError as exc:
                print('ERROR: Could not download the tarball:', exc,
                        file=sys.stderr)
                exit(1)
            local_file = os.path.join(self.output_dir, 'grid-updates-v' + \
                                        self.latest_version + '.tgz')
            try:
                with open(local_file,'wb') as output:
                    output.write(remote_file.read())
            except IOError as exc:
                print('ERROR: Could not write to local file:', exc,
                        file=sys.stderr)
                exit(1)
            else:
                if self.verbosity > 0:
                    print('Success: downloaded an update to %s.' % \
                            os.path.abspath(local_file))
        else:
            if self.verbosity > 0:
                print('No update available.')


def repair_share(verbosity, sharename, repair_uri, mode):
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
        exit(1)
    if verbosity > 3:
        print('DEBUG: Running urlopen(%s, %s).' % (repair_uri, params))
    try:
        f = urlopen(repair_uri, params)
    except HTTPError as exc:
        # TODO Doesn't catch all errors
        print('ERROR: Could not run %s for %s: %s', (mode, sharename, exc),
                                                        file=sys.stderr)
        exit(1)
    else:
        if mode == 'deep-check':
            # deep-check returns multiple JSON objects, 1 per line
            result = f.readlines()
        elif mode == 'one-check':
            # one-check returns a single JSON object
            result = f.read()
        return result
    finally:
        # TODO This can cause: UnboundLocalError: local variable 'f'
        # referenced before assignment
        f.close()

def parse_result(verbosity, result, mode, unhealthy):
    """Parse JSON response from Tahoe deep-check operation.
    Optionally prints status output; returns number of unhealthy shares.
    """
    #   [u'check-and-repair-results', u'cap', u'repaircap',
    #   u'verifycap', u'path', u'type', u'storage-index']
    if mode == 'deep-check':
        if not 'check-and-repair-results' in \
                json.loads(result).keys():
            # This would be the final 'stats' line.
            return 'unchecked', unhealthy
        uritype   = json.loads(result)['type']
        path   = json.loads(result)['path']
        status = json.loads(result) \
                    ['check-and-repair-results'] \
                    ['post-repair-results'] \
                    ['summary']
        # Print
        if verbosity > 1:
            if uritype == 'directory' and not path:
                print('  <root>: %s' % status)
            else:
                print('  %s: %s' % (path[0], status))
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


def parse_opts(argv):

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
    default_list_uri = 'URI:DIR2-RO:t4fs6cqxaoav3r767ce5t6j3h4:'\
            'gvjawwbjljythw4bjhgbco4mqn43ywfshdi2iqdxyhqzovrqazua'
    default_news_uri = 'URI:DIR2-RO:hx6754mru4kjn5xhda2fdxhaiu:'\
            'hbk4u6s7cqfiurqgqcnkv2ckwwxk4lybuq3brsaj2bq5hzajd65q'
    default_script_uri = 'URI:DIR2-RO:mjozenx3522pxtqyruekcx7mh4:'\
            'eaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a'
    default_comrepair_uri = 'URI:DIR2-RO:ysxswonidme22ireuqrsrkcv4y:'\
            'nqxg7ihxnx7eqoqeqoy7xxjmsqq6vzfjuicjtploh4k7mx6viz3a'
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
        print('INFO: No configuration files found.')
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
            help = "Synchronize the local list of introducers with the " \
                    "subscription's.")
    action_opts.add_option('-m', '--merge-introducers',
            action = 'store_true',
            dest = "merge",
            default = False,
            help = 'Downloads and merges list of introducers into your '\
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
    # TODO rename
    other_opts.add_option('--comrepair-uri',
            action = 'store',
            dest = 'comrepair_uri',
            default = comrepair_uri,
            help = 'Override default location of additional repair subscription.')
    other_opts.add_option('-o', '--output-dir',
            action = 'store',
            dest = 'output_dir',
            default = output_dir,
            help = 'Override default output directory (%s) for script '\
                    'update downloads.' % os.getcwd())
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


def main(opts, args):
    # Parse tahoe options (find web.static for NEWS files)
    tahoe_cfg_path = os.path.join(opts.tahoe_node_dir, 'tahoe.cfg')
    tahoe_config = SafeConfigParser({'web.static': 'public_html'})
    # TODO figure out why try..except doesn't work
    #try:
    #    tahoe_config.read(tahoe_cfg_path)
    #except ConfigParser.NoSectionError:
    #    print('ERROR: Could not parse tahoe.cfg.', file=sys.stderr)
    #    exit(1)
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
        exit(1)

    # Tahoe node dir validity check (in addition to the above tahoe.cfg check)
    if not os.access(opts.tahoe_node_dir, os.W_OK):
        print("ERROR: Need write access to", opts.tahoe_node_dir,
                file=sys.stderr)
        exit(1)

    # ACTION PARSING AND EXECUTION
    # ============================

    # Check for at least 1 mandatory option
    if not opts.version \
    and not opts.merge \
    and not opts.sync \
    and not opts.news \
    and not opts.repair \
    and not opts.check_version \
    and not opts.download_update \
    and not opts.comrepair:
        print('ERROR: You need to specify an action. Please see %s --help.' % \
                sys.argv[0], file=sys.stderr)
        exit(1)

    if opts.version:
        print('grid-updates version: %s.' % __version__)
        exit(0)

    # conflicting options
    if opts.merge and opts.sync:
        print('ERROR: --merge-introducers & --sync-introducers are' \
            ' mutually exclusive actions.', file=sys.stderr)
        exit(1)

    # generate URI dictionary
    def gen_full_tahoe_uri(uri):
        return opts.tahoe_node_url + '/uri/' + uri
    uri_dict = {'list': (opts.list_uri, gen_full_tahoe_uri(opts.list_uri)),
                'news': (opts.news_uri, gen_full_tahoe_uri(opts.news_uri)),
                'script': (opts.script_uri,
                            gen_full_tahoe_uri(opts.script_uri)),
                'comrepair': (opts.comrepair_uri,
                            gen_full_tahoe_uri(opts.comrepair_uri))
                }

    # Check URI validity
    for uri in uri_dict.values():
        if not re.match('^URI:', uri[0]):
            print( "'%s' is not a valid Tahoe URI. Aborting." % uri[0])
            exit(1)

    if opts.verbosity > 2:
        print("DEBUG: Tahoe node dir is", opts.tahoe_node_dir)

    # Run actions
    # -----------
    if opts.repair:
        # Iterate over known tahoe directories and all files within.
        if opts.verbosity > 0:
            print("-- Repairing the grid-updates Tahoe shares. --")
        mode = 'deep-check'
        unhealthy = 0
        # shuffle() to even out chances of all shares to get repaired
        # (Is this useful?)
        sharelist = uri_dict.keys()
        random.shuffle(sharelist)
        for sharename in sharelist:
            repair_uri = uri_dict[sharename][1]
            results = repair_share(opts.verbosity, sharename,
                                            repair_uri, mode)
            if opts.verbosity >1:
                print('INFO: Post-repair results for: %s' % sharename)
            for result in results:
                if sys.version_info[0] == 3:
                    result = str(result, encoding='ascii')
                status, unhealthy = parse_result(opts.verbosity, result,
                                                        mode, unhealthy)
            if opts.verbosity > 0:
                if unhealthy == 1:
                    sub = 'object'
                else:
                    sub = 'objects'
        if opts.verbosity > 0:
            print("Deep-check of grid-updates shares completed: ' \
                                '%d %s unhealthy." % (unhealthy, sub))

    if opts.comrepair:
        # --community-repair
        if opts.verbosity > 0:
            print("-- Repairing Tahoe shares. --")
        # TODO This action should probably be renamed to something less
        # specific, because there is a variety of use cases for it that don't
        # have to be community oriented.
        unhealthy = 0
        url = uri_dict['comrepair'][1] + '/community-repair.json.txt'
        subscriptionfile = tahoe_dl_file(opts.verbosity, url).read()
        # shuffle() to even out chances of all shares to get repaired
        sharelist = json.loads(subscriptionfile)['community-shares']
        random.shuffle(sharelist)
        for share in sharelist:
            sharename  = share['name']
            repair_uri = gen_full_tahoe_uri(share['uri'])
            mode       = share['mode']
            # TODO: turn repair_share method a function?
            if mode == 'deep-check':
                results = repair_share(opts.verbosity, sharename, repair_uri,
                                                                        mode)
                for result in results:
                    if sys.version_info[0] == 3:
                        result = str(result, encoding='ascii')
                    status, unhealthy = parse_result(opts.verbosity, result,
                                                            mode, unhealthy)
                if opts.verbosity > 1:
                    if unhealthy == 1:
                        sub = 'object'
                    else:
                        sub = 'objects'
                    print("  Deep-check completed: %d %s unhealthy." \
                                                    % (unhealthy, sub))
            if mode == 'one-check':
                result = repair_share(opts.verbosity, sharename,
                                                            repair_uri, mode)
                status, unhealthy = parse_result(opts.verbosity, result,
                                                            mode, unhealthy)
                if opts.verbosity > 1:
                    print("  Status: %s" % status)
        print('Repairs have completed (unhealthy: %d).' % unhealthy)


    if opts.merge or opts.sync:
        # Debug info
        if opts.merge and opts.verbosity > 2:
            print('DEBUG: Selected action: --merge-introducers')
        if opts.sync and opts.verbosity > 2:
            print('DEBUG: Selected action: --sync-introducers')
        try:
            intlist = List(opts.verbosity,
                    opts.tahoe_node_dir, uri_dict['list'][1])
            if intlist.lists_differ():
                intlist.backup_original()
                if opts.merge:
                    intlist.merge_introducers()
                elif opts.sync:
                    intlist.sync_introducers()
        except:
            if opts.verbosity > 1:
                print("DEBUG: Couldn't finish introducer list operation." \
                    " Continuing...")
        else:
            if opts.verbosity > 0:
                print('Successfully updated the introducer list.')
    if opts.news:
        try:
            if opts.verbosity > 2:
                print('DEBUG: Selected action: --download-news')
            news = News(opts.verbosity,
                    opts.tahoe_node_dir,
                    web_static_dir,
                    uri_dict['news'][1])
            news.download_news()
            news.extract_tgz()
            news.news_differ()
            # Copy in any case to make easily make sure that all versions
            # (escpecially the HTML version) are always present:
            news.install_files()
            news.remove_temporary()
        except:
            if opts.verbosity > 2:
                print("DEBUG: Couldn't finish news update operation." \
                    " Continuing...")
        else:
            if opts.verbosity > 0:
                print('Successfully updated news.')

    if opts.check_version or opts.download_update:
        try:
            # __init__ checks for new version
            update = Updates(opts.verbosity,
                    opts.output_dir,
                    uri_dict['script'][1])
            if opts.check_version:
                update.print_versions()
            if opts.download_update:
                update.download_update()
        except:
            if opts.verbosity > 2:
                print("DEBUG: Couldn't finish version check operation." \
                    " Continuing...")
        else:
            if opts.verbosity > 1:
                print('DEBUG: Successfully ran script update operation.')


if __name__ == "__main__":
    try:
        (opts, args) = parse_opts(sys.argv)
        main(opts, args)
    except KeyboardInterrupt:
        print("\ngrid-updates interrupted by user.")
        exit(1)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

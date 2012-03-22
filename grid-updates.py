#!/usr/bin/env python

"""grid-updates is a helper script for Tahoe-LAFS nodes."""

from __future__ import print_function
try:
    from ConfigParser import SafeConfigParser
except ImportError:
    from configparser import SafeConfigParser
from shutil import copyfile, rmtree
import json
import optparse
import os
import platform
import re
import sys
import tarfile
import tempfile # use os.tmpfile()?
try:
    #from urlparse import urlparse
    from urllib import urlopen
    from urllib import urlencode
    from urllib2 import HTTPError
except:
    from urllib.request import urlopen
    from urllib.parse import urlencode
    #from urllib.parse import urlparse
    from urllib.error import HTTPError

__author__ = "darrob"
__license__ = "Public Domain"
__version__ = "1.0.0a"
__maintainer__ = "darrob"
__email__ = "darrob@mail.i2p"
__status__ = "Development"

class List:
    # TODO compare lists first? don't backup identical lists?
    def __init__(self, verbosity, nodedir, url):
        self.verbosity = verbosity
        self.nodedir = nodedir
        self.url = url
        if self.verbosity > 0: print("-- Updating introducers --")
        self.old_list = []
        self.new_introducers = []
        self.introducers = os.path.join(self.nodedir, 'introducers')
        self.introducers_bak = self.introducers + '.bak'
        (self.old_introducers, self.old_list) = self.read_existing_list()
        self.new_list = self.download_new_list()

    def read_existing_list(self):
        """Read the local introducers file as a single string (to be written
        again) and as individual lines. """
        if self.verbosity > 2:
            print('DEBUG: Reading the local introducers file.')
        try:
            with open(self.introducers, 'r') as f:
                old_introducers = f.read()
                old_list = old_introducers.splitlines()
        except IOError as e:
            print('WARN: cannot read local introducers files:', e)
            print('WARN: Are you sure you have a compatible version of Tahoe-LAFS?')
            if self.verbosity > 1:
                print('INFO: Pretending to have read an empty introducers list.')
            old_introducers = ''
            old_list = []
        return (old_introducers, old_list)

    def download_new_list(self):
        """Download an introducers list from the Tahoe grid; return a list of
        strings."""
        url = os.path.join(self.url, 'introducers')
        if self.verbosity > 1: print("INFO: Downloading", url)
        try:
            response = urlopen(url)
        except HTTPError as e:
            print('ERROR: Could not download the introducers list:', e)
        else:
            # convert to buffer, needed for Python 3
            new_list = (b"response.read().split('\n')")
            return new_list

    def filter_new_list(self):
        """Compile a list of new introducers (not yet present in local
        file)."""
        for line in self.new_list:
            if re.match("^pb:\/\/", line):
                self.new_introducers.append(line)
        if self.verbosity > 3:
            print(self.new_introducers)

    def backup_original(self):
        """Copy the old introducers file to introducers.bak."""
        try:
            with open(self.introducers_bak, 'w') as f:
                f.write(self.old_introducers)
        except IOError:
            print('ERROR: Cannot create backup file introducers.bak')
            exit(1)
        else:
            if self.verbosity > 2:
                print('DEBUG: Created backup of local introducers.')

    def merge_introducers(self):
        """Add newly discovered introducers to the local introducers file."""
        try:
            with open(self.introducers, 'a') as f:
                for new_introducer in self.new_introducers:
                    if new_introducer not in self.old_list:
                        if self.verbosity > 0:
                            print("New introducer added: %s" % new_introducer)
                            f.write(new_introducer + '\n')
        except IOError as e:
            print('ERROR: Could not write to introducer file: %s' % e)
            exit(1)

    def replace_introducers(self):
        """Write the downloaded list of introducers to the local file
        (overwriting the existing file)."""
        try:
            with open(self.introducers, 'w') as f:
                for new_introducer in self.new_introducers:
                    f.write(new_introducer + '\n')
        except IOError as e:
            print('ERROR: Could not write to introducer file: %s' % e)
            exit(1)

class News:
    def __init__(self, verbosity, nodedir, web_static_dir, url):
        self.verbosity = verbosity
        self.nodedir = nodedir
        self.web_static = web_static_dir
        self.url = url
        if self.verbosity > 0: print("-- Updating NEWS --")
        self.local_news = os.path.join(self.nodedir, 'NEWS')
        self.tempdir = tempfile.mkdtemp()
        self.local_archive = os.path.join(self.tempdir, 'NEWS.tgz')

    def download_news(self):
        """Download NEWS.tgz file to local temporary file."""
        url = os.path.join(self.url, 'NEWS.tgz')
        if self.verbosity > 1: print("INFO: Downloading", url)
        try:
            remote_file = urlopen(url)
        except:
            print("ERROR: Couldn't find %s." % url)
            exit(1)
        with open(self.local_archive,'wb') as output:
            output.write(remote_file.read())

    def extract_tgz(self):
        """Extract NEWS.tgz archive into temporary directory."""
        if self.verbosity > 2:
            print('DEBUG: Extracting %s to %s.' % \
                    (self.local_archive, self.tempdir))
        try:
            tar = tarfile.open(self.local_archive, 'r:gz')
            for file in ['NEWS', 'NEWS.html', 'NEWS.atom']:
                tar.extract(file, self.tempdir)
            tar.close()
        except:
            print('ERROR: Could not extract NEWS.tgz archive.')
            exit(1)

    def news_differ(self):
        """Compare NEWS files and print to stdout if they differ (if allowed
        by verbosity level)."""
        # TODO convoluted; can probably be solved with a single try..except
        if os.access(self.local_news, os.F_OK):
            try:
                ln = open(self.local_news, 'r+')
            except IOError as e:
                print('ERROR: Cannot access NEWS file: %s' % e)
                exit(1)
            else:
                with open(os.path.join(self.tempdir, 'NEWS'), 'r') as tn:
                    if ln.read() != tn.read():
                        if self.verbosity > 2:
                            print('DEBUG: NEWS files differ.')
                        if self.verbosity > 0:
                            tn.seek(0)
                            for line in tn.readlines():
                                print('  | ' + line, end=' ')
                    else:
                        if self.verbosity > 1:
                            print('INFO: NEWS files seem to be identical.')
                if self.verbosity > 2:
                    print('DEBUG: Successfully extracted and compared NEWS files.')
            finally:
                ln.close()
        else:
            with open(os.path.join(self.tempdir, 'NEWS'), 'r') as tn:
                if self.verbosity > 2:
                    print('DEBUG: No NEWS file found in node directory.')
                if self.verbosity > 0:
                    for line in tn.readlines():
                        print('  | ' + line, end=' ')

    def install_files(self):
        """Copy extracted NEWS files to their intended locations."""
        try:
            copyfile(os.path.join(self.tempdir, 'NEWS'), self.local_news)
            for file in ['NEWS.html', 'NEWS.atom']:
                copyfile(os.path.join(self.tempdir, file),
                        os.path.join(self.nodedir, self.web_static, file))
        except:
            print("ERROR: Couldn't copy one or more NEWS files into the" \
                  "node directory.")
            exit(1)
        else:
            if self.verbosity > 2:
                print('DEBUG: Copied NEWS files into the node directory.')

    def remove_temporary(self):
        """Clean up temporary NEWS files."""
        try:
            rmtree(self.tempdir)
        except:
            print("ERROR: Couldn't remove temporary dir: %s." % self.tempdir)
        else:
            if self.verbosity > 2:
                print('DEBUG: Removed temporary dir: %s.' % self.tempdir)

class Updates:
    def __init__(self, verbosity, output_dir, url):
        self.verbosity = verbosity
        self.output_dir = output_dir
        self.url = url
        if self.verbosity > 0: print("-- Looking for script updates --")
        self.dir_url = self.url + '/?t=json'
        if self.new_version_available():
            self.new_version_available = True
        else:
            self.new_version_available = False

    def get_version_number(self):
        """Determine latest available version number by parsing the Tahoe
        directory."""
        if self.verbosity > 1: print("INFO: Checking for new version.")
        if self.verbosity > 2:
            print('DEBUG: Parsing Tahoe dir: %s.' % self.dir_url)
        # list Tahoe dir
        try:
            request = urlopen(self.dir_url)
        except HTTPError as e:
            print('ERROR: Could not access the Tahoe directory:', e)
        else:
            json_dir = request.read()
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
                    os.path.join(self.url, 'grid-updates-v' + self.latest_version + '.tgz')
            if self.verbosity > 1:
                print("INFO: Downloading", download_url)
            try:
                remote_file = urlopen(download_url)
            except HTTPError as e:
                print('ERROR: Could not download the tarball:', e)
                exit(1)
            local_file = os.path.join(self.output_dir, 'grid-updates-v' + \
                                        self.latest_version + '.tgz')
            try:
                with open(local_file,'wb') as output:
                    output.write(remote_file.read())
            except IOError as e:
                print('ERROR: Could not write to local file:', e)
                exit(1)
            else:
                if self.verbosity > 0:
                    print('Success: downloaded an update to %s.' % \
                            os.path.abspath(local_file))
        else:
            if self.verbosity > 0:
                print('No update available.')


def repair_shares(verbosity, uri_dict):
    """Run a deep-check including repair and add-lease on the grid-update
    shares."""
    # TODO catch: <html><head><title>Page Not Found</title></head><body>Sorry, but I couldn't find the object you requested.</body></html>
    if verbosity > 0: print("-- Repairing the grid-updates Tahoe shares. --")
    if verbosity > 2:
        print('DEBUG: This is the output of the repair operations:')
    for uri in list(uri_dict.keys()):
        repair_uri = uri_dict[uri][1]
        if verbosity > 0: print("Repairing", repair_uri)
        params = urlencode({'t': 'stream-deep-check',
            'repair': 'true', 'add-lease': 'true'}).encode('ascii')
        f = urlopen(repair_uri, params)
        if verbosity > 2:
            print(f.read())
        f.close()
        #try:
        #    f = urlopen(repair_uri, params)
        #    # TODO parse output
        #    print f.read()
        #except HTTPError as e:
        #    print 'ERROR: Could not repair %s URI: %s' % (uri, e)
        #    break
        #else:
        #    f.close()

def main():
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
        default_tahoe_node_dir = os.path.join(os.environ['USERPROFILE'], ".tahoe")
        config_locations = [
                os.path.join(os.environ['APPDATA'], 'grid-updates', 'config.ini'),
                ]
    else:
        default_tahoe_node_dir = os.path.join(os.environ['HOME'], ".tahoe")
        config_locations = [
                os.path.join(os.environ['HOME'], ".config", 'grid-updates', 'config.ini'),
                os.path.join('/etc', 'grid-updates', 'config.ini'),
                os.path.join(os.getcwd(), 'config.ini'),
                ]

    # Default settings
    #tahoe_node_dir = os.path.abspath('testdir')
    default_tahoe_node_url = 'http://127.0.0.1:3456'
    default_list_uri = 'URI:DIR2-RO:t4fs6cqxaoav3r767ce5t6j3h4:'\
            'gvjawwbjljythw4bjhgbco4mqn43ywfshdi2iqdxyhqzovrqazua'
    default_news_uri = 'URI:DIR2-RO:hx6754mru4kjn5xhda2fdxhaiu:'\
            'hbk4u6s7cqfiurqgqcnkv2ckwwxk4lybuq3brsaj2bq5hzajd65q'
    default_script_uri = 'URI:DIR2-RO:mjozenx3522pxtqyruekcx7mh4:'\
            'eaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a'

    # Configparser
    # uses defaults (above) if not found in config file
    config = SafeConfigParser({
        'tahoe_node_dir': default_tahoe_node_dir,
        'tahoe_node_url': default_tahoe_node_url,
        'list_uri': default_list_uri,
        'news_uri': default_news_uri,
        'script_uri': default_script_uri,
        })
    config.read(config_locations)

    # Optparse
    # defaults to values from Configparser
    parser = optparse.OptionParser()
    # actions
    action_opts = optparse.OptionGroup(
        parser, 'Actions',
        'These arguments control which actions will be executed.')
    action_opts.add_option('-m', '--merge-introducers',
            action = 'store_true',
            dest = "merge",
            default = False,
            help = 'Downloads and merges list of introducers into your '\
                    'local list.')
    action_opts.add_option('-r', '--replace-introducers',
            action = 'store_true',
            dest = "replace",
            default = False,
            help = 'Downloads and installs list of introducers.')
    action_opts.add_option('-n', '--download-news',
            action = 'store_true',
            dest = "news",
            default = False,
            help = 'Downloads news feed.')
    action_opts.add_option('-R', '--repair-subscriptions',
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
    parser.add_option_group(action_opts)
    # options
    other_opts = optparse.OptionGroup(
        parser, 'Options',
        'These arguments can override various settings.')
    other_opts.add_option('-d', '--node-dir',
            action = 'store',
            dest = "tahoe_node_dir",
            default = config.get('OPTIONS', 'tahoe_node_dir'),
            help = 'Specify the Tahoe node directory.')
    other_opts.add_option('-u', '--node-url',
            action = 'store',
            dest = 'tahoe_node_url',
            default = config.get('OPTIONS', 'tahoe_node_url'),
            help = "Specify the Tahoe gateway node's URL.")
    other_opts.add_option('--list-uri',
            action = 'store',
            dest = 'list_uri',
            default = config.get('OPTIONS', 'list_uri'),
            help = 'Override default location of introducers list.')
    other_opts.add_option('--news-uri',
            action = 'store',
            dest = 'news_uri',
            default = config.get('OPTIONS', 'news_uri'),
            help = 'Override default location of news list.')
    other_opts.add_option('--script-uri',
            action = 'store',
            dest = 'script_uri',
            default = config.get('OPTIONS', 'script_uri'),
            help = 'Override default location of script releases.')
    other_opts.add_option('-o', '--output-dir',
            action = 'store',
            dest = 'output_dir',
            default = os.getcwd(),
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
    # parse arguments
    (opts, args) = parser.parse_args()

    # Parse tahoe options
    tahoe_cfg_path = os.path.join(opts.tahoe_node_dir, 'tahoe.cfg')
    tahoe_config = SafeConfigParser({'web.static': 'public_html'})
    # TODO figure out why try..except doesn't work
    #try:
    #    tahoe_config.read(tahoe_cfg_path)
    #except ConfigParser.NoSectionError:
    #    print('ERROR: Could not parse tahoe.cfg.')
    #    exit(1)
    #else:
    #    print(tahoe_config.get('node', 'web.static'))
    #    web_static_dir = os.path.abspath(
    #            os.path.join(
    #                    opts.tahoe_node_dir,
    #                    tahoe_config.get('node', 'web.static')))
    if os.access(tahoe_cfg_path, os.R_OK):
        tahoe_config.read(tahoe_cfg_path)
        web_static_dir = os.path.abspath(
                os.path.join(
                        opts.tahoe_node_dir,
                        tahoe_config.get('node', 'web.static')))
    else:
        print('ERROR: Could not parse tahoe.cfg. Not a valid Tahoe node.')
        exit(1)

    # tahoe node dir validity check (in addition to the above tahoe.cfg check)
    if not os.access(opts.tahoe_node_dir, os.W_OK):
        print("ERROR: Need write access to", opts.tahoe_node_dir)
        exit(1)

    # DEBUG
    if opts.verbosity > 2:
        print('DEBUG: The following options have been set:')
        for opt in sorted(opts.__dict__.keys()):
            print('  %s\t-> %s' % (opt, opts.__dict__[opt]))
        print('  web.static\t-> ' + web_static_dir)

    # Check for at least 1 mandatory option
    if not opts.version \
    and not opts.merge \
    and not opts.replace \
    and not opts.news \
    and not opts.repair \
    and not opts.check_version \
    and not opts.download_update:
        print('ERROR: You need to specify an action. Please see %s --help.' % \
                sys.argv[0])
        exit(1)

    if opts.version:
        print('grid-updates version: %s.' % __version__)
        exit(0)

    # conflicting options
    if opts.merge and opts.replace:
        print('ERROR: --merge-introducers & --replace-introducers are' \
            ' mutually exclusive actions.')
        exit(1)

    # generate URI dictionary
    def gen_full_tahoe_uri(uri):
        return opts.tahoe_node_url + '/uri/' + uri
    uri_dict = {'list': (opts.list_uri, gen_full_tahoe_uri(opts.list_uri)),
            'news': (opts.news_uri, gen_full_tahoe_uri(opts.news_uri)),
            'script': (opts.script_uri, gen_full_tahoe_uri(opts.script_uri))}

    # Check URI validity
    for uri in uri_dict.values():
        if not re.match('^URI:', uri[0]):
            print( "'%s' is not a valid Tahoe URI. Aborting." % uri[0])
            exit(1)

    if opts.verbosity > 1: print("DEBUG: Tahoe node dir is", opts.tahoe_node_dir)

    # run actions
    if opts.merge or opts.replace:
        # Debug info
        if opts.merge and opts.verbosity > 2:
            print('DEBUG: Selected action: --merge-introducers')
        if opts.replace and opts.verbosity > 2:
            print('DEBUG: Selected action: --replace-introducers')
        try:
            list = List(opts.verbosity, opts.tahoe_node_dir, uri_dict['list'][1])
            # convert to a buffer, needed for Python 3
            b"list.filter_new_list()"
            list.backup_original()
            if opts.merge:
                list.merge_introducers()
            elif opts.replace:
                list.replace_introducers()
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
            news = News(opts.verbosity, opts.tahoe_node_dir, web_static_dir, uri_dict['news'][1])
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

    if opts.repair:
        # TODO
        repair_shares(opts.verbosity, uri_dict)
        #try:
        #    if opts.verbosity > 2:
        #        print 'DEBUG: Selected action: --repair-subscriptions'
        #    repair_shares(opts.verbosity, uri_dict)
        #except:
        #    if opts.verbosity > 2:
        #        print "DEBUG: Couldn't finish repair operation." \
        #            " continuing..."
        #else:
        #    if opts.verbosity > 2:
        #        print 'DEBUG: Successfully ran repair operation.'

    if opts.check_version or opts.download_update:
        try:
            # __init__ checks for new version
            up = Updates(opts.verbosity, opts.output_dir, uri_dict['script'][1])
            if opts.check_version: up.print_versions()
            if opts.download_update: up.download_update()
        except:
            if opts.verbosity > 2:
                print("DEBUG: Couldn't finish version check operation." \
                    " Continuing...")
        else:
            if opts.verbosity > 1:
                print('DEBUG: Successfully ran script update operation.')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\ngrid-updates interrupted by user.")
        exit(1)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
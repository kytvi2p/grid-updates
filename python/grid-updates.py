#!/usr/bin/python

""" grid-updates is a helper script for Tahoe-LAFS nodes."""

from ConfigParser import SafeConfigParser
from shutil import copyfile, rmtree
import filecmp
import json
import optparse
import os
import re
import tarfile
import tempfile # use os.tmpfile()?
import urllib
import urllib2

__author__ = "darrob"
__license__ = "Public Domain"
__version__ = "1.0.0a"
__maintainer__ = "darrob"
__email__ = "darrob@mail.i2p"
__status__ = "Development"

class List:
    def __init__(self, verbose, nodedir, url):
        self.verbose = verbose
        self.nodedir = nodedir
        self.url = url
        if self.verbose: print "INFO: Tahoe node dir is", self.nodedir
        self.old_list = []
        self.new_introducers = []
        self.introducers = self.nodedir + '/introducers'
        self.introducers_bak = self.introducers + '.bak'
        # run functions
        self.read_existing_list()
        self.new_list = self.download_new_list()

    def read_existing_list(self):
        """ Read the local introducers file as a single string (to be written
        again) and as individual lines. """
        try:
            f = open(self.introducers, 'r')
            self.old_introducers = f.read()
            self.old_list = self.old_introducers.splitlines()
            f.close()
        except IOError:
            print 'ERROR: cannot read local introducers files.'
            exit(1)

    def download_new_list(self):
        """ Download an introducers list from the Tahoe grid; return a list of
        strings."""
        # TODO exceptions
        url = self.url + '/introducers'
        if self.verbose: print "INFO: trying to download", url
        response = urllib2.urlopen(url)
        new_list = response.read().split('\n')
        return new_list

    def filter_new_list(self):
        """ Compile a list of new introducers (not yet present in local
        file)."""
        for line in self.new_list:
            if re.match("^pb:\/\/", line):
                self.new_introducers.append(line)

    def backup_original(self):
        """ Copy the old introducers file to introducers.bak."""
        try:
            f = open(self.introducers_bak, 'w')
            f.write(self.old_introducers)
            f.close()
        except IOError:
            print 'ERROR: cannot create backup file introducers.bak'
            exit(1)

    def merge_introducers(self):
        """ Add newly discovered introducers to the local introducers file."""
        with open(self.introducers, 'a') as f:
            for new_introducer in self.new_introducers:
                if new_introducer not in self.old_list:
                    print "New introducer added: %s" % new_introducer
                    f.write(new_introducer + '\n')

    def replace_introducers(self):
        """ Write the downloaded list of introducers to the local file
        (overwriting the existing file)."""
        with open(self.introducers, 'w') as f:
            for new_introducer in self.new_introducers:
                f.write(new_introducer + '\n')

class News:
    def __init__(self, verbose, nodedir, url):
        self.verbose = verbose
        self.nodedir = nodedir
        self.url = url
        self.local_news = self.nodedir + '/NEWS'
        self.tempdir = tempfile.mkdtemp()
        self.local_archive = self.tempdir + '/NEWS.tgz'

    def download_news(self):
        """ Download NEWS.tgz file to local temporary file."""
        url = self.url + '/NEWS.tgz'
        if self.verbose: print "INFO: trying to download", url
        remote_file = urllib2.urlopen(url)
        with open(self.local_archive,'wb') as output:
            output.write(remote_file.read())

    def extract_tgz(self):
        """ Extract NEWS.tgz archive into temporary directory."""
        # TODO exceptions
        tar = tarfile.open(self.local_archive, 'r:gz')
        for file in ['NEWS', 'NEWS.html', 'NEWS.atom']:
            tar.extract(file, self.tempdir)
        tar.close()

    def install_files(self):
        """ Copy extracted NEWS files to their intended locations."""
        # TODO exceptions
        copyfile(self.tempdir + '/NEWS', self.local_news)
        for file in ['NEWS.html', 'NEWS.atom']:
            copyfile(self.tempdir + '/' + file, self.nodedir + \
                    '/public_html/' + file)
        # TODO parse web.static (public_html) dir from tahoe.cfg?

    def news_differ(self):
        """ Determine if downloaded NEWS differ from already present local
        NEWS."""
        if os.access(self.local_news, os.R_OK):
            if not filecmp.cmp(self.local_news, self.tempdir + '/NEWS'):
                return True
            else:
                return False
        else:
            # file doesn't exist; return True to copy over downloaded version
            return True

    def print_news(self):
        """ Print new NEWS (plaintext version) to stdout."""
        with open(self.tempdir + '/NEWS', 'r') as file:
            for line in file:
                print line,

    def remove_temporary(self):
        """ Clean up temporary NEWS files."""
        rmtree(self.tempdir)

class Updates:
    def __init__(self, verbose, output_dir, url):
        self.verbose = verbose
        self.output_dir = output_dir
        self.url = url
        self.dir_url = self.url + '/?t=json'
        if self.new_version_available():
            self.new_version_available = True
        else:
            self.new_version_available = False

    def get_version_number(self):
        """ Determine latest available version number by parsing the Tahoe
        directory."""
        if self.verbose: print "INFO: checking for new version..."
        # list Tahoe dir
        request = urllib2.urlopen(self.dir_url)
        json_dir = request.read()
        # parse json index of dir
        file_list = json.loads(json_dir)[1]['children'].keys()
        # parse version numbers
        version_numbers = []
        for filename in file_list:
            if re.match("^grid-updates-v.*\.tgz$", filename):
                v = (re.sub(r'^grid-updates-v(.*)\.tgz', r'\1', filename))
                version_numbers.append(v)
        latest_version = sorted(version_numbers)[-1]
        if self.verbose:
            print 'INFO: current version: %s; newest available: %s.' % \
                    (__version__, latest_version)
        return latest_version

    def new_version_available(self):
        """ Determine if the local version is smaller than the available
        version."""
        self.latest_version = self.get_version_number()
        if __version__ < self.latest_version:
            return True
        else:
            return False

    def check_update(self):
        """ Print current and available version numbers."""
        if self.new_version_available:
            print 'There is a new version available: %s (currently %s).' % \
                    (self.latest_version, __version__)

    def download_update(self):
        """ Download script tarball."""
        # TODO configurable output dir
        if self.new_version_available:
            download_url = self.url + '/grid-updates-v' + self.latest_version \
                    + '.tgz'
            if self.verbose: print "INFO: trying to download", download_url
            remote_file = urllib2.urlopen(download_url)
            try:
                local_file = self.output_dir + '/grid-updates-v' + \
                    self.latest_version + '.tgz'
                output = open(local_file,'wb')
                output.write(remote_file.read())
            except:
                print 'ERROR' # TODO
            else:
                print 'Success: downloaded an update to %s.' \
                    % os.path.abspath(local_file)

def repair_shares(verbose, uri_dict):
    """ Run a deep-check including repair and add-lease on the grid-update
    shares."""
    for uri in uri_dict.keys():
        repair_uri = uri_dict[uri][1]
        if verbose: print "INFO: Repairing", repair_uri
        params = urllib.urlencode({'t': 'stream-deep-check',
            'repair': 'true', 'add-lease': 'true'})
        f = urllib.urlopen(repair_uri, params)
        #print f.read()
        f.close()

def main():

    # Parse settings:
    #   1. Set default fall-backs.
    #   2. Parse configuration files.
    #       (Apply defaults if necessary.)
    #   3. Parse command line options.
    #       (Use values from 2. as defaults.)

    # Default settings
    tahoe_node_dir = os.path.abspath('testdir')
    tahoe_node_url = 'http://127.0.0.1:3456'
    list_uri = 'URI:DIR2-RO:t4fs6cqxaoav3r767ce5t6j3h4:'\
            'gvjawwbjljythw4bjhgbco4mqn43ywfshdi2iqdxyhqzovrqazua'
    news_uri = 'URI:DIR2-RO:hx6754mru4kjn5xhda2fdxhaiu:'\
            'hbk4u6s7cqfiurqgqcnkv2ckwwxk4lybuq3brsaj2bq5hzajd65q'
    script_uri = 'URI:DIR2-RO:mjozenx3522pxtqyruekcx7mh4:'\
            'eaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a'

    # Configparser
    # uses defaults (above) if not found in config file
    config = SafeConfigParser({
        'tahoe_node_dir': tahoe_node_dir,
        'tahoe_node_url': tahoe_node_url,
        'list_uri': list_uri,
        'news_uri': news_uri,
        'script_uri': script_uri,
        })
    config.read('config.ini')

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
            default = config.get('global', 'tahoe_node_dir'),
            help = 'Specify the Tahoe node directory.')
    other_opts.add_option('-u', '--node-url',
            action = 'store',
            dest = 'tahoe_node_url',
            default = config.get('global', 'tahoe_node_url'),
            help = "Specify the Tahoe gateway node's URL.")
    other_opts.add_option('--list-uri',
            action = 'store',
            dest = 'list_uri',
            default = config.get('global', 'list_uri'),
            help = 'Override default location of introducers list.')
    other_opts.add_option('--news-uri',
            action = 'store',
            dest = 'news_uri',
            default = config.get('global', 'news_uri'),
            help = 'Override default location of news list.')
    other_opts.add_option('--script-uri',
            action = 'store',
            dest = 'script_uri',
            default = config.get('global', 'script_uri'),
            help = 'Override default location of script releases.')
    other_opts.add_option('-o', '--output-dir',
            action = 'store',
            dest = 'output_dir',
            default = os.getcwd(),
            help = 'Override default output directory (%s) for script '\
                    'update downloads.' % os.getcwd())
    parser.add_option_group(other_opts)
    # remaining
    parser.add_option('-v', '--verbose',
            dest = "verbose",
            action = "store_true",
            default = False,
            help = 'Display more verbose output.')
    parser.add_option('-V', '--version',
            dest = "version",
            action = "store_true",
            default = False,
            help = 'Display version information.')
    # parse arguments
    (opts, args) = parser.parse_args()

    # DEBUG
    if opts.verbose:
        print 'INFO: the following options have been set:'
        for opt in sorted(opts.__dict__.keys()):
            print '  %s\t-> %s' % (opt, opts.__dict__[opt])

    if opts.version:
        print 'grid-updates version: %s.' % __version__
        exit(0)
        # TODO license information?

    # conflicting options
    if opts.merge and opts.replace:
        # TODO better message
        print 'Error: choose either -m or -r.'
        exit(1)
        # TODO raise exception?

    # tahoe node dir validity check
    if not os.access(tahoe_node_dir + '/node.url', os.F_OK):
        print "ERROR: node.url not found. Not a valid Tahoe node."
        exit(1)
    if not os.access(tahoe_node_dir, os.W_OK):
        print "ERROR: need write access to", tahoe_node_dir

    # generate URI dictionary
    def generate_full_tahoe_uri(uri):
        return tahoe_node_url + '/uri/' + uri
    global uri_dict
    uri_dict = {'list': (opts.list_uri, generate_full_tahoe_uri(opts.list_uri)),
            'news': (opts.news_uri, generate_full_tahoe_uri(opts.news_uri)),
            'script': (opts.script_uri, generate_full_tahoe_uri(opts.script_uri))}

    # run actions
    if opts.merge:
        if opts.verbose: print 'INFO: Selected action: --merge-introducers'
        list = List(opts.verbose, opts.tahoe_node_dir, uri_dict['list'][1])
        list.filter_new_list()
        list.backup_original()
        list.merge_introducers()
    elif opts.replace:
        if opts.verbose: print 'INFO: Selected action: --replace-introducers'
        list = List(opts.verbose, opts.tahoe_node_dir, uri_dict['list'][1])
        list.filter_new_list()
        list.backup_original()
        list.replace_introducers()

    if opts.news:
        if opts.verbose: print 'INFO: Selected action: --download-news'
        news = News(opts.verbose, opts.tahoe_node_dir, uri_dict['news'][1])
        news.download_news()
        news.extract_tgz()
        if news.news_differ():
            news.print_news()
        else:
            if opts.verbose:
                print "INFO: the NEWS file is unchanged."
        # Copy in any case to make easily make sure that all versions
        # (escpecially the HTML version) are always present:
        news.install_files()
        news.remove_temporary()

    if opts.repair:
        if opts.verbose: print 'INFO: Selected action: --repair-subscriptions'
        repair_shares(opts.verbose, uri_dict)

    if opts.check_version or opts.download_update:
        # __init__ checks for new version
        up = Updates(opts.verbose, opts.output_dir, uri_dict['script'][1])
        if opts.check_version:
            up.check_update()
        if opts.download_update:
            up.download_update()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "\ngrid-updates interrupted by user."
        exit(1)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

#!/usr/bin/env python

""" grid-updates is a helper script for Tahoe-LAFS nodes."""

from ConfigParser import SafeConfigParser
from shutil import copyfile, rmtree
import filecmp
import json
import optparse
import os
import re
import sys
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
    def __init__(self, verbosity, nodedir, url):
        self.verbosity = verbosity
        self.nodedir = nodedir
        self.url = url
        if self.verbosity > 1: print "INFO: Tahoe node dir is", self.nodedir
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
            with open(self.introducers, 'r') as f:
                self.old_introducers = f.read()
                self.old_list = self.old_introducers.splitlines()
        except IOError, e:
            print 'ERROR: cannot read local introducers files:', e
            exit(1)

    def download_new_list(self):
        """ Download an introducers list from the Tahoe grid; return a list of
        strings."""
        url = self.url + '/introducers'
        if self.verbosity > 1: print "INFO: trying to download", url
        # TODO exceptions
        response = urllib2.urlopen(url)
        new_list = response.read().split('\n')
        return new_list

    def filter_new_list(self):
        """ Compile a list of new introducers (not yet present in local
        file)."""
        for line in self.new_list:
            if re.match("^pb:\/\/", line):
                self.new_introducers.append(line)
        if self.verbosity > 3:
            print self.new_introducers

    def backup_original(self):
        """ Copy the old introducers file to introducers.bak."""
        try:
            with open(self.introducers_bak, 'w') as f:
                f.write(self.old_introducers)
        except IOError:
            print 'ERROR: cannot create backup file introducers.bak'
            exit(1)
        else:
            if self.verbosity > 2:
                print 'DEBUG: created backup of local introducers.'

    def merge_introducers(self):
        """ Add newly discovered introducers to the local introducers file."""
        # TODO exceptions
        with open(self.introducers, 'a') as f:
            for new_introducer in self.new_introducers:
                if new_introducer not in self.old_list:
                    print "New introducer added: %s" % new_introducer
                    f.write(new_introducer + '\n')

    def replace_introducers(self):
        """ Write the downloaded list of introducers to the local file
        (overwriting the existing file)."""
        # TODO exceptions
        with open(self.introducers, 'w') as f:
            for new_introducer in self.new_introducers:
                f.write(new_introducer + '\n')

class News:
    # TODO improve diff'ing
    def __init__(self, verbosity, nodedir, url):
        self.verbosity = verbosity
        self.nodedir = nodedir
        self.url = url
        self.local_news = self.nodedir + '/NEWS'
        self.tempdir = tempfile.mkdtemp()
        self.local_archive = self.tempdir + '/NEWS.tgz'

    def download_news(self):
        """ Download NEWS.tgz file to local temporary file."""
        url = self.url + '/NEWS.tgz'
        if self.verbosity > 1: print "INFO: trying to download", url
        try:
            remote_file = urllib2.urlopen(url)
        except:
            print "ERROR: couldn't find %s." % url
            exit(1)
        with open(self.local_archive,'wb') as output:
            output.write(remote_file.read())

    def extract_tgz(self):
        """ Extract NEWS.tgz archive into temporary directory."""
        # TODO exceptions
        #tar = tarfile.open(self.local_archive, 'r:gz')
        with tarfile.open(self.local_archive, 'r:gz') as tar:
            for file in ['NEWS', 'NEWS.html', 'NEWS.atom']:
                tar.extract(file, self.tempdir)

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
        try:
            rmtree(self.tempdir)
        except:
            print "ERROR: couldn't remove temporary dir: %s." % self.tempdir

class Updates:
    def __init__(self, verbosity, output_dir, url):
        self.verbosity = verbosity
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
        if self.verbosity > 1: print "INFO: checking for new version..."
        # list Tahoe dir
        try:
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
            if self.verbosity > 1:
                print 'INFO: current version: %s; newest available: %s.' % \
                        (__version__, latest_version)
        except urllib2.HTTPError, e:
            print 'ERROR: could not access the Tahoe directory:', e
        else:
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
            if self.verbosity > 0:
                print 'There is a new version available: %s (currently %s).' \
                        % (self.latest_version, __version__)

    def download_update(self):
        """ Download script tarball."""
        if self.new_version_available:
            download_url = self.url + '/grid-updates-v' + self.latest_version \
                    + '.tgz'
            if self.verbosity > 1:
                print "INFO: trying to download", download_url
            try:
                remote_file = urllib2.urlopen(download_url)
            except urllib2.HTTPError, e:
                print 'ERROR: could not download the tarball:', e
                exit(1)
            local_file = self.output_dir + '/grid-updates-v' + \
                self.latest_version + '.tgz'
            try:
                with open(local_file,'wb') as output:
                    output.write(remote_file.read())
            except IOError, e:
                print 'ERROR: could not write to local file:', e
                exit(1)
            else:
                print 'Success: downloaded an update to %s.' \
                    % os.path.abspath(local_file)

def repair_shares(verbosity, uri_dict):
    """ Run a deep-check including repair and add-lease on the grid-update
    shares."""
    # TODO catch: <html><head><title>Page Not Found</title></head><body>Sorry, but I couldn't find the object you requested.</body></html>
    if verbosity > 2:
        print 'DEBUG: this is the output of the repair operations:'
    for uri in uri_dict.keys():
        repair_uri = uri_dict[uri][1]
        if verbosity > 0: print "Repairing", repair_uri
        params = urllib.urlencode({'t': 'stream-deep-check',
            'repair': 'true', 'add-lease': 'true'})
        f = urllib.urlopen(repair_uri, params)
        if verbosity > 2:
            print f.read()
        f.close()
        #try:
        #    f = urllib.urlopen(repair_uri, params)
        #    # TODO parse output
        #    print f.read()
        #except urllib2.HTTPError, e:
        #    print 'ERROR: could not repair %s URI: %s' % (uri, e)
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

    # DEBUG
    if opts.verbosity > 2:
        print 'DEBUG: the following options have been set:'
        for opt in sorted(opts.__dict__.keys()):
            print '  %s\t-> %s' % (opt, opts.__dict__[opt])

    # Check for at least 1 mandatory option
    if not opts.version \
    and not opts.merge \
    and not opts.replace \
    and not opts.news \
    and not opts.repair \
    and not opts.check_version \
    and not opts.download_update:
        print 'ERROR: You need to specify an action. Please see %s --help.' % \
                sys.argv[0]
        exit(1)

    if opts.version:
        print 'grid-updates version: %s.' % __version__
        exit(0)

    # conflicting options
    if opts.merge and opts.replace:
        print 'ERROR: --merge-introducers & --replace-introducers are' \
            ' mutually exclusive actions.'
        exit(1)

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
    try:
        if opts.merge:
                if opts.verbosity > 2:
                    print 'DEBUG: Selected action: --merge-introducers'
                list = List(opts.verbosity, opts.tahoe_node_dir, uri_dict['list'][1])
                list.filter_new_list()
                list.backup_original()
                list.merge_introducers()
        elif opts.replace:
            if opts.verbosity > 2:
                print 'DEBUG: Selected action: --replace-introducers'
            list = List(opts.verbosity, opts.tahoe_node_dir, uri_dict['list'][1])
            list.filter_new_list()
            list.backup_original()
            list.replace_introducers()
    except:
        if opts.verbosity > 1:
            print "DEBUG: Couldn't finish introducer list operation." \
                " Continuing..."
    else:
        if opts.verbosity > 2:
            print 'DEBUG: successfully ran introducer list operation.'

    if opts.news:
        try:
            if opts.verbosity > 2:
                print 'DEBUG: Selected action: --download-news'
            news = News(opts.verbosity, opts.tahoe_node_dir, uri_dict['news'][1])
            news.download_news()
            news.extract_tgz()
            if news.news_differ():
                news.print_news()
            else:
                if opts.verbosity > 0:
                    print "The NEWS file is unchanged."
            # Copy in any case to make easily make sure that all versions
            # (escpecially the HTML version) are always present:
            news.install_files()
            news.remove_temporary()
        except:
            if opts.verbosity > 2:
                print "DEBUG: Couldn't finish news update operation." \
                    " Continuing..."
        else:
            if opts.verbosity > 2:
                print 'DEBUG: successfully ran news operation.'

    if opts.repair:
        repair_shares(opts.verbosity, uri_dict)
        exit(0)
        try:
            if opts.verbosity > 2:
                print 'DEBUG: Selected action: --repair-subscriptions'
            repair_shares(opts.verbosity, uri_dict)
        except:
            if opts.verbosity > 2:
                print "DEBUG: couldn't finish repair operation." \
                    " continuing..."
        else:
            if opts.verbosity > 2:
                print 'DEBUG: successfully ran repair operation.'

    if opts.check_version or opts.download_update:
        try:
            # __init__ checks for new version
            up = Updates(opts.verbosity, opts.output_dir, uri_dict['script'][1])
            if opts.check_version: up.check_update()
            if opts.download_update: up.download_update()
        except:
            if opts.verbosity > 2:
                print "DEBUG: couldn't finish version check operation." \
                    " Continuing..."
        else:
            if opts.verbosity > 2:
                print 'DEBUG: successfully ran script update operation.'

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "\ngrid-updates interrupted by user."
        exit(1)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

#!/usr/bin/env python

"""grid-updates is a helper script for Tahoe-LAFS nodes."""

from __future__ import print_function
import optparse
import os
import platform
import re
import sys
# Maybe this is better than try -> except?
if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser
    from urllib2 import ProxyHandler, install_opener, build_opener
else:
    from configparser import ConfigParser as SafeConfigParser
    from urllib.request import ProxyHandler, install_opener, build_opener

from gridupdates.introducers import Introducers
from gridupdates.makenews import MakeNews
from gridupdates.news import News
from gridupdates.patchwebui import PatchWebUI
from gridupdates.update import Update
from gridupdates import repairs
from gridupdates.functions import find_datadir
from gridupdates.functions import find_webstatic_dir
from gridupdates.functions import gen_full_tahoe_uri
from gridupdates.functions import is_root
from gridupdates.functions import proxy_configured


__author__ = ['darrob', 'KillYourTV']
__license__ = "Public Domain"
__version__ = "1.0.0git"
__maintainer__ = ['darrob', 'KillYourTV']
__email__ = ['darrob@mail.i2p', 'killyourtv@mail.i2p']
__status__ = "Development"

__patch_version__ = '1.8.3-gu5'


def determine_tahoe_node_url(tahoe_node_dir, node_url_cli):
    """
    Parse ~/.tahoe/node.url and use its value unless its overridden by
    --node-url.
    """
    # remove trailing slashes to be able to compare the strings and to avoid
    # double slashes in later URL's (which would fail).
    node_url_cli = re.sub(r'/$', '', node_url_cli)
    node_url_file = os.path.join(tahoe_node_dir, 'node.url')
    try:
        with open(node_url_file, 'r') as nuf:
            node_url_parsed = nuf.readlines()[0].strip()
            # remove trailing slashes to be able to compare the strings and to
            # avoid double slashes in later URL's (which would fail).
            node_url_parsed = re.sub(r'/$', '', node_url_parsed)
    except IOError:
        print('ERROR: %s not found.' % node_url_file, file=sys.stderr)
        sys.exit(1)
    if node_url_cli != node_url_parsed:
        # Prefer node URL specified on the command line over parsed URL
        return node_url_cli
    else:
        return node_url_parsed

# Config parsing
# ==============
# 1. set hard-coded defaults (get_default_config())
# 2. find and read config files (parse_config_files())
# 3. parse command line arguments (parse_args())

def get_default_config():
    """Set default configuration values."""
    # OS-dependent settings
    #for k in os.environ: print "%s: %s" %(k, os.environ[k])
    operating_system = platform.system()
    if operating_system == 'Windows':
        default_tahoe_node_dir = os.path.join(os.environ['USERPROFILE'],
                                                        ".tahoe")
    else:
        default_tahoe_node_dir = os.path.join(os.environ['HOME'], ".tahoe")

    # 1. Default settings
    default_config = {
            'tahoe_node_dir' : default_tahoe_node_dir,
            'tahoe_node_url' : 'http://127.0.0.1:3456',
            'list_uri'       : 'URI:DIR2-RO:t4fs6cqxaoav3r767ce5t6j3h4:gvjawwbjljythw4bjhgbco4mqn43ywfshdi2iqdxyhqzovrqazua',
            'news_uri'       : 'URI:DIR2-RO:hx6754mru4kjn5xhda2fdxhaiu:hbk4u6s7cqfiurqgqcnkv2ckwwxk4lybuq3brsaj2bq5hzajd65q',
            'script_uri'     : 'URI:DIR2-RO:mjozenx3522pxtqyruekcx7mh4:eaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a',
            'comrepair_uri'  : 'URI:DIR2-RO:ysxswonidme22ireuqrsrkcv4y:nqxg7ihxnx7eqoqeqoy7xxjmsqq6vzfjuicjtploh4k7mx6viz3a',
            'output_dir'     : os.path.abspath(os.getcwd())
            }
    return default_config

def parse_config_files(argv):
    """Parse options given in config files."""
    default_config = get_default_config()

    operating_system = platform.system()
    if operating_system == 'Windows':
        config_locations = [
                os.path.join(os.environ['APPDATA'],
                                        'grid-updates',
                                        'config.ini')]
    else:
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
    # 2. Configparser
    # uses defaults (above) if not found in config file
    config = SafeConfigParser({
        'tahoe_node_dir' : default_config['tahoe_node_dir'],
        'tahoe_node_url' : default_config['tahoe_node_url'],
        'list_uri'       : default_config['list_uri'],
        'news_uri'       : default_config['news_uri'],
        'script_uri'     : default_config['script_uri'],
        'comrepair_uri'  : default_config['comrepair_uri'],
        'output_dir'     : default_config['output_dir']
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
        # Set standard fallback values if no config files found
        config.read(available_cfg_files)
        default_config['tahoe_node_dir'] = config.get('OPTIONS', 'tahoe_node_dir')
        default_config['tahoe_node_url'] = config.get('OPTIONS', 'tahoe_node_url')
        default_config['list_uri']       = config.get('OPTIONS', 'list_uri')
        default_config['news_uri']       = config.get('OPTIONS', 'news_uri')
        default_config['script_uri']     = config.get('OPTIONS', 'script_uri')
        default_config['comrepair_uri']  = config.get('OPTIONS', 'comrepair_uri')
        default_config['output_dir']     = config.get('OPTIONS', 'output_dir')
    return default_config

def parse_args(argv):
    """Parse options given on the command line."""

    default_config = parse_config_files(argv)

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
    action_opts.add_option('-R', '--community-repair',
            action = 'store_true',
            dest = "comrepair",
            default = False,
            help = 'Retrieve a list of shares and maintain/repair them.')
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
    other_opts.add_option('-d', '--node-directory',
            action = 'store',
            dest = "tahoe_node_dir",
            default = default_config['tahoe_node_dir'],
            help = 'Specify the Tahoe node directory.')
    other_opts.add_option('-u', '--node-url',
            action = 'store',
            dest = 'tahoe_node_url',
            default = default_config['tahoe_node_url'],
            help = "Specify the Tahoe gateway node's URL.")
    other_opts.add_option('--list-uri',
            action = 'store',
            dest = 'list_uri',
            default = default_config['list_uri'],
            help = 'Override default location of introducers list.')
    other_opts.add_option('--news-uri',
            action = 'store',
            dest = 'news_uri',
            default = default_config['news_uri'],
            help = 'Override default location of news list.')
    other_opts.add_option('--script-uri',
            action = 'store',
            dest = 'script_uri',
            default = default_config['script_uri'],
            help = 'Override default location of script releases.')
    other_opts.add_option('--comrepair-uri',
            action = 'store',
            dest = 'comrepair_uri',
            default = default_config['comrepair_uri'],
            help = ('Override default location of additional repair '
                    'subscription.'))
    other_opts.add_option('--format',
            action = 'store',
            dest = 'update_format',
            default = 'tar',
            help = ('Specify in which format to download the update.'))
    other_opts.add_option('-o', '--output-dir',
            action = 'store',
            dest = 'output_dir',
            default = default_config['output_dir'],
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
        print("DEBUG: Patch directory is", find_datadir())

    return (opts, args)

def main():
    """Main function: run selected actions."""

    proxy_support = ProxyHandler({})
    opener = build_opener(proxy_support)
    install_opener(opener)

    # Parse config files and command line arguments
    (opts, args) = parse_args(sys.argv)

    # ACTION PARSING AND EXECUTION
    # ============================

    if opts.version:
        print('grid-updates version: %s.' % __version__)
        sys.exit(0)

    # Run actions allowed to root, then exit
    if is_root():
        print("WARN: You're running grid-updates as root. Only certain actions"
                " will be available.")
        if opts.patch_ui or opts.undo_patch_ui:
            webui = PatchWebUI(opts.tahoe_node_url, opts.verbosity)
            if opts.patch_ui:
                webui.run_action('patch', 'None')
            elif opts.undo_patch_ui:
                webui.run_action('undo', 'None')
        else:
            print("ERROR: Illegal action for root account.", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # Check for at least 1 mandatory option
    if (not opts.merge
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

    # conflicting options
    if opts.merge and opts.sync:
        print('ERROR: --merge-introducers & --sync-introducers are '
            'mutually exclusive actions.', file=sys.stderr)
        sys.exit(2)

    # Check Tahoe node dir validity
    if os.access(opts.tahoe_node_dir, os.W_OK):
        web_static_dir = find_webstatic_dir(opts.tahoe_node_dir)
        if not web_static_dir:
            sys.exit(1)
    else:
        print("ERROR: Need write access to", opts.tahoe_node_dir,
                file=sys.stderr)
        sys.exit(1)

    tahoe_node_url = determine_tahoe_node_url(opts.tahoe_node_dir,
                                                opts.tahoe_node_url)

    if proxy_configured():
        print("WARNING: Found (and unset) the 'http_proxy' variable.")

    # generate URI dictionary
    uri_dict = {'list': (opts.list_uri,
                                    gen_full_tahoe_uri(
                                            tahoe_node_url,
                                            opts.list_uri)),
                'news': (opts.news_uri,
                                    gen_full_tahoe_uri(
                                            tahoe_node_url,
                                            opts.news_uri)),
                'script': (opts.script_uri,
                                    gen_full_tahoe_uri(
                                            tahoe_node_url,
                                            opts.script_uri)),
                'comrepair': (opts.comrepair_uri,
                                    gen_full_tahoe_uri(
                                            tahoe_node_url,
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
    if opts.merge or opts.sync:
        intlist = Introducers(opts.tahoe_node_dir,
                        uri_dict['list'][1],
                        opts.verbosity)
        if opts.sync:
            intlist.run_action('sync')
        elif opts.merge:
            intlist.run_action('merge')
    if opts.news:
        news = News(opts.tahoe_node_dir,
                    web_static_dir,
                    tahoe_node_url,
                    uri_dict['news'][1],
                    opts.verbosity)
        news.run_action()
    if opts.check_version or opts.download_update:
        update = Update(__version__,
                                opts.output_dir,
                                uri_dict['script'][1],
                                opts.verbosity)
        if opts.check_version:
            update.run_action('check')
        elif opts.download_update:
            update.run_action('download', opts.update_format)
    if opts.patch_ui or opts.undo_patch_ui:
        webui = PatchWebUI(__patch_version__,
                                        tahoe_node_url,
                                        opts.verbosity)
        if opts.patch_ui:
            webui.run_action('patch', web_static_dir)
        elif opts.undo_patch_ui:
            webui.run_action('undo', web_static_dir)
    if opts.mknews_md_file:
        mknews = MakeNews(opts.verbosity)
        mknews.run_action(opts.mknews_md_file, opts.output_dir)
    if opts.repair:
        repairs.repair_action(uri_dict, opts.verbosity)
    if opts.comrepair:
        repairs.comrepair_action(tahoe_node_url,
                uri_dict, opts.verbosity)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\ngrid-updates interrupted by user.")
        sys.exit(1)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

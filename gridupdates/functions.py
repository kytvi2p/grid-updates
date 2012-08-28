from __future__ import print_function
from shutil import copyfile
from shutil import rmtree
import ctypes # TODO import only needed function?
import imp
import json
import os
import platform
import re
import sys
# Maybe this is better than try -> except?
if sys.version_info[0] == 2:
    import ConfigParser
    from ConfigParser import SafeConfigParser
    from urllib2 import HTTPError
    from urllib2 import urlopen
    from urllib2 import URLError
else:
    import configparser as ConfigParser
    from configparser import ConfigParser as SafeConfigParser
    from urllib.request import urlopen
    from urllib.error import HTTPError
    from urllib.error import URLError

def is_root():
    """
    Check if grid-updates is running with root permissions.
    """
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return is_admin

def gen_full_tahoe_uri(node_url, uri):
    """Generate a complete, accessible URL from a Tahoe URI."""
    return node_url + '/uri/' + uri

def create_web_static_dir(web_static_dir):
    """
    This function will create the directory configured with the
    'web.static' variable in ~/.tahoe/tahoe.cfg.

    This location is used to store our news items for later display in
    the WebUI.
    """
    try:
        os.mkdir(web_static_dir)
    except (IOError, os.error) as exc:
        print("ERROR: %s while creating %s" % (exc, web_static_dir),
                                                    file=sys.stderr)
        return False
    else:
        install_news_stub(web_static_dir)

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
    except URLError as urlexc:
        print("ERROR: %s while downloading %s." % (urlexc, url),
                                               file= sys.stderr)
        sys.exit(1)
    else:
        return response

def is_valid_introducer(uri):
    """Check if the introducer address has the correct format."""
    if re.match(r'^pb:\/\/.*@', uri):
        return True
    else:
        return False

def proxy_configured():
    """Determine if the http_proxy environment variable is set."""
    try:
        if os.environ["http_proxy"]:
            return True
    except KeyError:
        return False

def is_literal_file(result):
    """Check for LIT files, which cannot be checked."""
    if not json.loads(result)['storage-index']:
        return True
    else:
        return False

def is_frozen():
    """
    If grid-updates has been 'frozen' with py2exe, bb-freeze, freeze or the
    like, the path returned by sys.argv[0] will NOT be the path of the
    executable. __file__ is not in the py2exe executable either.  Instead the
    path returned will be '.'.

    If a py2exe'd grid-updates is added to the system path in Windows
    (recommended), we cannot assume that the grid-updates directory is '.' --
    most of the time it won't be.

    This function will figure out whether grid-updates is running as a frozen
    application or not.  Currently we only 'freeze' with py2exe but here we'll
    check for multiple methods of freezing.
    """
    return (hasattr(sys, "frozen") or # new py2exe
           hasattr(sys, "importers") # old py2exe
           or imp.is_frozen("__main__")) # tools/freeze

def get_installed_dir():
    """ Determine true path of grid-updates."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(sys.argv[0])

def find_datadir():
    """Determine datadir (e.g. /usr/share) from the location of grid-updates."""
    bindir = get_installed_dir()
    # When processed with py2exe:
    if (is_frozen() or os.path.exists( os.path.join(bindir, 'share',
                                                  'tahoe.css.patched'))):
        datadir = os.path.join(bindir, 'share')
    # When installed the normal way:
    else:
        datadir = os.path.join(bindir, '..', 'share', 'grid-updates')
    if not os.path.exists(datadir):
        print('ERROR: Does not exist: %s.' % datadir, file=sys.stderr)
    datadir = os.path.abspath(datadir)
    return datadir

def find_tahoe_dir(tahoe_node_url):
    """Determine the location of the tahoe installation directory and included
    'web' directory by parsing the tahoe web console."""
    webconsole = urlopen(tahoe_node_url)
    match = re.search(r'.*\ \'(.*__init__.py)', webconsole.read().decode('utf8'))
    if match:
        tahoe_dir = os.path.dirname(match.group(1))
        return tahoe_dir
    else:
        print('ERROR: Cannot find node directory.', file=sys.stderr)
        return False

def find_web_static_dir(tahoe_node_dir):
    """Get web.static directory from tahoe.cfg."""
    tahoe_cfg_path = os.path.join(tahoe_node_dir, 'tahoe.cfg')
    tahoe_config = SafeConfigParser({'web.static': 'public_html'})
    try:
        tahoe_config.read(tahoe_cfg_path)
        web_static_dir = os.path.abspath(
                os.path.join(
                        tahoe_node_dir,
                        tahoe_config.get('node', 'web.static')))
        if not os.path.exists(web_static_dir):
            create_web_static_dir(web_static_dir)
        else:
            if not os.path.isdir(web_static_dir):
                print("ERROR: %s is a file but it should be a directory." %
                        web_static_dir, file=sys.stderr)
                return False

    except ConfigParser.NoSectionError:
        print('ERROR: Could not parse tahoe.cfg. Not a valid Tahoe node.',
                file=sys.stderr)
        return False
    else:
        return web_static_dir

def get_tahoe_version(tahoe_node_url):
    """Determine Tahoe-LAFS version number from web console."""
    webconsole = urlopen(tahoe_node_url)
    match = re.search(r'allmydata-tahoe:\ (.*),', webconsole.read().decode('utf'))
    version = match.group(1)
    return version

def remove_temporary_dir(directory, verbosity=0):
    """Remove a (temporary) directory."""
    try:
        rmtree(directory)
    except (IOError, os.error):
        print("ERROR: Couldn't remove temporary dir: %s." % directory,
                file=sys.stderr)
    else:
        if verbosity > 2:
            print('DEBUG: Removed temporary dir: %s.' % directory)

def set_tahoe_node_url(cli_node_url, tahoe_node_dir):
    """
    Parse ~/.tahoe/node.url and use its value unless its overridden by
    --node-url.
    """
    # Prefer node URL specified on the command line over parsed URL
    if cli_node_url is not None:
        cli_node_url = re.sub(r'/$', '', cli_node_url)
        return cli_node_url
    # remove trailing slashes to be able to compare the strings and to avoid
    # double slashes in later URL's (which would fail).
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
    return node_url_parsed

def json_list_is_valid(json_list, verbosity=0):
    """Investigates a JSON list's validity."""
    try:
        keys = json.loads(json_list).keys()
    except ValueError as ve:
        print("ERROR: Can't parse JSON list:", ve)
        if verbosity > 2:
            print(json_list)
        return False
    except:
        print("ERROR: JSON data is invalid (Unexpected Error).")
        if verbosity > 2:
            print(json_list)
        return False
    else:
        if verbosity > 3:
            print('DEBUG: JSON list seems to be valid. Found %d keys.' %
                    len(keys))
        return True

def subscription_list_is_valid(json_list, verbosity=0):
    """Investigates a share list's JSON validity."""
    if json_list_is_valid(json_list):
        keys = json.loads(json_list).keys()
        for uri in list(keys):
            try:
                json.loads(json_list)[uri]['name']
            except TypeError:
                print("ERROR: Can't parse JSON list.", file=sys.stderr)
                return False
        if verbosity > 3:
            print('DEBUG: Subscription list seems to be valid. '
                    'Found %d keys.' % len(keys))
        return True
    else:
        return False

def install_news_stub(web_static_dir):
    """Copy a placeholder NEWS.html file to Tahoe's web.static directory to
    avoid 404 Errors (e.g. in the Iframe)."""
    targetfile = os.path.join(web_static_dir, 'NEWS.html')
    if not os.access(targetfile, os.F_OK):
        news_stub_file = os.path.join(find_datadir(), 'news-stub.html')
        copyfile(news_stub_file, targetfile)

#!/usr/bin/env python

from __future__ import print_function
from shutil import copyfile, rmtree
import ctypes # TODO import only needed function?
import imp
import json
import os
import platform
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

def is_root():
    """
    Check if grid-updates is running with root permissions.

    Exception for XP systems: this function will always return False.
    """
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        # It is notoriously difficult to run many applications under restricted
        # accounts on Windows XP.  Therefore, we do not check if user is an
        # admin on XP; most users on XP _are_ going to be admins.
        if not 'XP' in platform.win32_ver():
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            is_admin = False
    return is_admin

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
    match = re.search(r'.*\ \'(.*__init__.pyc)', webconsole.read())
    tahoe_dir = os.path.dirname(match.group(1))
    return tahoe_dir

def find_webstatic_dir(tahoe_node_dir):
    """Get web.static directory from tahoe.cfg."""
    tahoe_cfg_path = os.path.join(tahoe_node_dir, 'tahoe.cfg')
    tahoe_config = SafeConfigParser({'web.static': 'public_html'})
    try:
        tahoe_config.read(tahoe_cfg_path)
        web_static_dir = os.path.abspath(
                os.path.join(
                        tahoe_node_dir,
                        tahoe_config.get('node', 'web.static')))
    # TODO except ConfigParser.NoSectionError: doesn't work
    except:
        print('ERROR: Could not parse tahoe.cfg. Not a valid Tahoe node.',
                file=sys.stderr)
        return False
    else:
        return web_static_dir

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
        print('ERROR: Could not run %s for %s: %s', (mode, sharename, exc),
                                                        file=sys.stderr)
        sys.exit(1)
    except URLError as urlexc:
        print("ERROR: %s while running %s for %s." % (urlexc, mode, sharename),
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

def parse_result(result, mode, unhealthy, verbosity=0):
    """Parse JSON response from Tahoe deep-check operation.
    Optionally prints status output; returns number of unhealthy shares.
    """
    #   [u'check-and-repair-results', u'cap', u'repaircap',
    #   u'verifycap', u'path', u'type', u'storage-index']
    if mode == 'deep-check':
        # Check for expected result line
        if not ('check-and-repair-results' in
                list(json.loads(result).keys())):
            # This would be the final 'stats' line.
            return 'unchecked', unhealthy
        if is_literal_file(result):
            print('  %s: (literal file)' %
                    ('/'.join(json.loads(result)['path'])))
            return 'unchecked', unhealthy
        path    = json.loads(result)['path']
        uritype = json.loads(result)['type']
        status  = (json.loads(result)
                    ['check-and-repair-results']
                    ['post-repair-results']
                    ['summary'])
        # Print
        if verbosity > 1:
            if uritype == 'directory' and not path:
                print('  <root>: %s' % status)
            else:
                print('  %s: %s' % ('/'.join(path), status))
        # Count unhealthy
        if status.startswith('Unhealthy'):
            unhealthy += 1
        return status, unhealthy
    elif mode == 'one-check':
        if is_literal_file(result):
            return 'unchecked (literal file)', unhealthy
        status = json.loads(result)['post-repair-results']['summary']
        # Count unhealthy
        if status.startswith('Unhealthy'):
            unhealthy += 1
        return status, unhealthy

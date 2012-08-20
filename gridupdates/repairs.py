from __future__ import print_function
import json
import random
import re
import sys
# Maybe this is better than try -> except?
if sys.version_info[0] == 2:
    from urllib import urlencode
    from urllib2 import HTTPError
    from urllib2 import urlopen
    from urllib2 import URLError
else:
    from urllib.request import urlopen
    from urllib.parse import urlencode
    from urllib.error import HTTPError
    from urllib.error import URLError

from gridupdates.functions import gen_full_tahoe_uri
from gridupdates.functions import is_literal_file
from gridupdates.functions import tahoe_dl_file
from gridupdates.functions import json_list_is_valid

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
        print('ERROR: Could not run %s for %s: %s' % (mode, sharename, exc),
                                                        file=sys.stderr)
        return
    except URLError as urlexc:
        print("ERROR: %s while running %s for %s." % (urlexc, mode, sharename),
                                                               file=sys.stderr)
        return
    except KeyboardInterrupt:
        sys.exit(1)
    except:
        print("ERROR: Could not run %s on %s." % (mode, sharename),
                                                    file=sys.stderr)
        return
    else:
        if mode == 'deep-check':
            # deep-check returns multiple JSON objects, 1 per line
            result = response.readlines()
        elif mode == 'one-check':
            # one-check returns a single JSON object
            result = response.read()
        return result

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

def repair_action(uri_dict, verbosity=0):
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
        if not results:
            return
        if verbosity > 1:
            print('INFO: Post-repair results for: %s' % sharename)
        for result in results:
            status, unhealthy = parse_result(result.decode('utf8'),
                                                mode, unhealthy, verbosity)
    # Print summary
    if unhealthy == 1:
        sub = 'object'
    else:
        sub = 'objects'
    if verbosity > 0:
        print("Deep-check of grid-updates shares completed: "
                            "%d %s unhealthy." % (unhealthy, sub))

class RepairList(object):
    """
    The --repair-list command. Repair all shares in the subscription file.

    This will download a json file and repair the included shares. The json
    file must include the repair mode to be used.  Known modes are one-check,
    deep-check and level-check.

    level-check is a custom mode that tries to be a limited version of
    deep-check. It will repair a directory structure as far as the configured
    number of levels allows.
    """

    def __init__(self, tahoe_node_url, subscription_uri, verbosity=0):
        self.verbosity = verbosity
        self.tahoe_node_url = tahoe_node_url
        self.subscription_uri = subscription_uri
        if verbosity > 0:
            print("-- Repairing Tahoe shares. --")
        self.unhealthy = 0

    def run_action(self):
        shares = self.dl_sharelist()
        sharelist = json.loads(shares).keys()
        # shuffle() to even out chances of all shares to get repaired
        random.shuffle(sharelist)
        for uri in sharelist:
            sharename  = json.loads(shares)[uri]['name']
            repair_uri = gen_full_tahoe_uri(self.tahoe_node_url, uri)
            mode  = json.loads(shares)[uri]['mode']
            if mode == 'deep-check':
                self.deep_check(sharename, repair_uri, mode)
            elif mode == 'one-check':
                self.one_check(sharename, repair_uri, mode)
            elif mode.startswith('level-check '):
                self.level_check(sharename, repair_uri, mode)
            else:
                print("ERROR: Unknown repair mode: '%s'." % mode, file=sys.stderr)
                return
        if self.verbosity > 0:
            print('Repairs have completed (unhealthy: %d).' % self.unhealthy)

    def dl_sharelist(self):
        url = self.subscription_uri + '/repair-list.json.txt'
        shares = tahoe_dl_file(url, self.verbosity).read().decode('utf8')
        if json_list_is_valid(shares):
            return shares
        else:
            return

    def add_subdir_items(self, repair_uris, sharename):
        """
        This function checks if a given item is a directory and adds its contents
        to the directory.
        """
        shareuri = repair_uris[sharename]
        dir_req = urlopen(shareuri + '?t=json').read().decode('utf8')
        if not json.loads(dir_req)[0] == 'dirnode':
            if self.verbosity > 2:
                print('DEBUG: Skipping %s' % sharename)
            return repair_uris
        for child in json.loads(dir_req)[1]['children']:
            childname = sharename + '/' + child
            if self.verbosity > 2:
                print('DEBUG: Adding %s to repair list' % childname)
            repair_uris[childname] = shareuri + '/' + child
        return repair_uris

    def one_check(self, sharename, repair_uri, mode):
        result = repair_share(sharename, repair_uri, mode, self.verbosity)
        if not result:
            return
        status, self.unhealthy = parse_result(result.decode('utf8'), mode,
                                                    self.unhealthy, self.verbosity)
        if self.verbosity > 1:
            print("  Status: %s" % status)

    def deep_check(self, sharename, repair_uri, mode):
        results = repair_share(sharename, repair_uri, mode, self.verbosity)
        if not results:
            return
        for result in results:
            status, self.unhealthy = parse_result(result.decode('utf8'),
                                                mode, self.unhealthy, self.verbosity)

    def level_check(self, sharename, repair_uri, mode):
        levels = int(re.sub(r'level-check\ (\d+)', r'\1', mode))
        if self.verbosity > 1:
            print('INFO: Will check %d levels deep.' % levels)
        mode = 'one-check' # all item will be one-checked
        repair_uris = {}
        repair_uris[sharename] = repair_uri # add root dir
        added = []
        while levels > 0: # keep adding items of subdirectories
            for item in list(repair_uris.keys()):
                if not item in added:
                    repair_uris = self.add_subdir_items(repair_uris, item)
                added.append(item)
            levels = levels - 1
        for item in sorted(list(repair_uris.keys())):
            if self.verbosity > 2:
                print('Will repair %s.' % sorted(list(repair_uris.keys())))
            self.one_check(item, repair_uris[item], mode)

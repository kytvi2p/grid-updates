#!/usr/bin/env python

from __future__ import print_function
import json
import random
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

from Modules.Functions import gen_full_tahoe_uri
from Modules.Functions import is_literal_file
from Modules.Functions import tahoe_dl_file

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

def comrepair_action(tahoe_node_url, uri_dict, verbosity=0):
    """The --community-repair command. Repair all shares in the uri_dict."""
    if verbosity > 0:
        print("-- Repairing Tahoe shares. --")
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
            if not results:
                return
            for result in results:
                status, unhealthy = parse_result(result.decode('utf8'),
                                                    mode, unhealthy, verbosity)
        if mode == 'one-check':
            result = repair_share(sharename, repair_uri, mode, verbosity)
            if not result:
                return
            status, unhealthy = parse_result(result.decode('utf8'), mode,
                                                        unhealthy, verbosity)
            if verbosity > 1:
                print("  Status: %s" % status)
    if verbosity > 0:
        print('Repairs have completed (unhealthy: %d).' % unhealthy)

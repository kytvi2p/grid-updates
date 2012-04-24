"""grid-updates is a helper script for Tahoe-LAFS nodes."""

from __future__ import print_function
import os
import re
import sys
# Maybe this is better than try -> except?
if sys.version_info[0] == 2:
    from urllib2 import ProxyHandler, install_opener, build_opener
else:
    from urllib.request import ProxyHandler, install_opener, build_opener

from gridupdates.version import __version__
from gridupdates.introducers import Introducers
from gridupdates.makenews import MakeNews
from gridupdates.news import News
from gridupdates.patchwebui import PatchWebUI
from gridupdates.update import Update
from gridupdates import repairs
from gridupdates.functions import find_webstatic_dir
from gridupdates.functions import gen_full_tahoe_uri
from gridupdates.functions import is_root
from gridupdates.functions import proxy_configured
from gridupdates.functions import determine_tahoe_node_url
from gridupdates.config import parse_args


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
    and not opts.repairlist
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
                'repairlist': (opts.repairlist_uri,
                                    gen_full_tahoe_uri(
                                            tahoe_node_url,
                                            opts.repairlist_uri))
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
    if opts.repairlist:
        repairs.repairlist_action(tahoe_node_url,
                uri_dict['repairlist'][1], opts.verbosity)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\ngrid-updates interrupted by user.")
        sys.exit(1)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

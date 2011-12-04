% GRID-UPDATES(1) User Commands
% darrob <darrob@mail.i2p>, killyourtv <kytv@mail.i2p>
% December 2011

NAME
====

grid-updates -- Helper Script for Tahoe-LAFS Nodes

SYNOPSIS
========

**grid-updates** [*OPTIONS*] *ACTION*

DESCRIPTION
===========

*grid-updates* is a script intended to help keep Tahoe-LAFS nodes'
configurations up-to-date.  It can retrieve updated lists of introducers as
well as simple news updates.

ACTIONS
=======

-m, \--merge-introducers
:   Merge your node's local introducers list with the subscription's.

-r, \--replace-introducers
:   Replace your node's local list of introducers with the master list.

-n, \--download-news
:   Retrieve news. These will be stored in [node directory]/NEWS and new
	contents will be printed to stdout. If you run this script as a cron job,
	the news will be emailed to you.

\--check-version
:   Check for a new version of this script on the grid.

\--download-update *[target_directory]*
:   Download a new version of this script from the grid to the specified
    directory (implies `--check-update`).

-R, \--repair-subscriptions
:   Maintain or repair the health of the subscription service's URIs.

OPTIONS
=======

-d *directory*, \--node-directory *directory*
:   Specify the node directory (default: ~/.tahoe),

\--list-uri *URI*
:   Override the default location of the introducers list.

\--news-uri *URI*
:   Override the default location of the NEWS file,

\--script-uri *URI*
:   Override the default location of script updates.

-v, \--verbose
:   Display more verbose output.

-V, \--version
:   Display version information.

-h, \--help
:   Print usage information.

NOTES
=====

*URIs*, in this context, can be either Tahoe-LAFS directories like

    URI:DIR2-RO:22s6zidugdxaeikq6lakbxbcci:mgrc3nfnygslyqrh7hds22usp6hbn3pulg5bu2puv6y3wpoaaqqq

or regular Eepsite URLs like http://example.i2p/.

ERRORS
======

If the script repeatedly fails to retrieve a file from the grid, the share may
be damaged. Try running `--repair-subscriptions` which will attempt to
deep-check the share. If that doesn't help, you will most likely have to find
new URIs to subscribe to. Use `--check-version` to see if there is a new
version of *grid-updates* available, which may already include new default
URIs.  You can also ask in #tahoe-lafs (on Irc2P) and check the DeepWiki or
http://killyourtv.i2p.

FILES
=====

*~/.tahoe/NEWS*  
*~/.tahoe/introducers*

BUGS
====

Please report bugs in #tahoe-lafs on Irc2p or via email (see below).

SEE ALSO
========

The *grid-updates* git repository: http://git.repo.i2p/w/grid-updates.git

TODO: The *README* document?

LICENSE
=======

*grid-updates* has been released into the public domain. This means that you can
do whatever you please with it.


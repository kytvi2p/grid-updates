% GRID-UPDATES(1) User Commands
% darrob <darrob@mail.i2p>, killyourtv <kytv@mail.i2p>
% December 2011

NAME
====

grid-updates - Helper Script for Tahoe-LAFS Nodes

SYNOPSIS
========

**grid-updates** [*OPTIONS*] *ACTION*

DESCRIPTION
===========

*grid-updates* is a shell script intended to help keep Tahoe-LAFS nodes'
configurations up-to-date.  It can retrieve lists of introducers as well as
news feeds from the Tahoe grid.  This is useful for any public grid that
relies solely on volunteers.

ACTIONS
=======

-m, \--merge-introducers
:   Merge your node's local introducers list with the subscription's.

-r, \--replace-introducers
:   Replace your node's local list of introducers with the master list.

-n, \--download-news
:   Retrieve the news feed.  See the **NEWS** section below.

\--check-version
:   Check for a new version of this script on the grid.

\--download-update *[target_directory]*
:   Download a new version of this script from the grid to the specified
    directory (implies `--check-update`).

-R, \--repair-subscriptions
:   Maintain or repair the health of the subscription service's URIs.

OPTIONS
=======

-c *config file*, \--config *config file*
:   Specify a grid-updates config file. See **CONFIG FILES** section below.

-d *directory*, \--node-directory *directory*
:   Specify the node directory (default: *~/.tahoe*),

\--list-uri *URI*
:   Override the default location of the introducers list.

\--news-uri *URI*
:   Override the default location of the NEWS.tgz file.

\--script-uri *URI*
:   Override the default location of script updates.

\--download-tool *[eepget|wget|fetch|curl]*
:   Specifiy the desired download tool. Without this option *grid-updates* will
    try to find the best available tool automatically.

\--no-proxy
:   Disable proxy when downloading from non-tahoe URIs

-v, \--verbose
:   Display more verbose output.

-V, \--version
:   Display version information.

-h, \--help
:   Print usage information.

CONFIG FILES
============

*grid-updates* will look for configuration files in $XDG_CONFIG_HOME and
$XDG_CONFIG_DIRS.

Accepted options are:

LISTURI = *URI*
:    Same as \--list-uri option above
NEWSURI = *URI*
:    Same as \--news-uri option above
SCRIPTURI = *URI*
:    Same as \--script-uri option above
HTTP_PROXY = *address*
:    (The default is 127.0.0.1:4444)
DOWNLOAD_TOOL = *name*
:    Same as \--download-tool option above
USE_PROXY = *yes*/*no*
:    "USE_PROXY = no" equals the \--no-proxy option above. Default is *yes*.

NOTES
=====

*URIs*, in this context, can be either Tahoe-LAFS directories like  
`URI:DIR2-RO:22s6zidugdxaeikq6lakbxbcci:mgrc3nfnygslyqrh7hds22usp6hbn3pulg5bu2puv6y3wpoaaqqq`  
or regular FQDNs like `http://example.i2p/` or `http://www.example.com/`.

ERRORS
======

If the script repeatedly fails to retrieve a file from the grid, the share may
be damaged.  Run `--repair-subscriptions` which will attempt to deep-check the
share.

If that doesn't help, you will most likely have to find new URIs to subscribe
to.

Use `--check-version` to see if there is a new version of *grid-updates*
available, which may already include new default URIs.

Finally, you can check on IRC, mailing lists and Wikis for updated
information.

NEWS
====

If you choose to download the news feed, *grid-updates* will place a plain text
version of it in your node's directory and print it to stdout.

Furthermore, it will place an HTML version of it in your node's web server's
*/static* directory, so you can access it at
http://127.0.0.1:3456/static/NEWS.html.

The Atom news feed (http://127.0.0.1:3456/static/NEWS.atom) can be used by a
regular feed reader to check for *grid-updates* news.  (Please note, however,
that you cannot "refresh" the feed with a regular news reader.  These files
have to always be fetched by *grid-updates* first.)

FILES
=====

*~/.tahoe/introducers*  
*~/.tahoe/NEWS*  
*~/.tahoe/public_html/NEWS.html*  
*~/.tahoe/public_html/NEWS.atom*  
*\$XDG_CONFIG_HOME/grid-updates/config* (most commonly ~/.config)  
*\$XDG_CONFIG_DIRS/grid-updates/config* (most commonly /etc/xdg)  

BUGS
====

Please report bugs in #tahoe-lafs on Irc2p or via email (see below).

SEE ALSO
========

The *grid-updates* git repository: http://git.repo.i2p/w/grid-updates.git

The README on the grid:

    URI:DIR2-RO:mjozenx3522pxtqyruekcx7mh4:eaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a/README.html

Information about Tahoe-LAFS for I2P and the I2P grid: http://killyourtv.i2p

LICENSE
=======

*grid-updates* has been released into the public domain. This means that you can
do whatever you please with it.


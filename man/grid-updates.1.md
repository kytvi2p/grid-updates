% GRID-UPDATES(1) User Commands
% darrob <darrob@mail.i2p>, KillYourTV <killyourtv@mail.i2p>
% March 2012

NAME
====

grid-updates - Helper Script for Tahoe-LAFS Nodes

SYNOPSIS
========

**grid-updates** [*OPTIONS*] *ACTIONS*

DESCRIPTION
===========

*grid-updates* is a Python script intended to help keep Tahoe-LAFS nodes'
configurations up-to-date.  It can retrieve lists of introducers as well as
news feeds from the Tahoe grid.  This is useful for any public grid that relies
solely on volunteers.

ACTIONS
=======

-s, \--sync-introducers
:   Synchronize your node's local list of introducers with the master list.

-m, \--merge-introducers
:   Merge your node's local introducers list with the subscription's.

-n, \--download-news
:   Retrieve the news feed.  See the **NEWS** section below.

-r, \--repair-subscriptions
:   Maintain or repair the health of the subscription service's URIs.

-R, \--community-repair
:   Retrieve a list of shares and maintain/repair them.

\--patch-tahoe
:   Patch the Tahoe-LAFS web console to display the grid-updates news feed in
    an Iframe.

\--undo-patch-tahoe
:   Remove the grid-updates patch to the Tahoe web console and restore its
    original version.

\--make-news *file*
:   Create a *grid-updates*-compatible NEWS.tgz file from a Markdown source
    file.

\--check-version
:   Check for a new version of this script on the grid.

\--download-update
:   Download a new version of this script from the grid to the specified
    directory (implies `--check-update`).

OPTIONS
=======

-c *config file*, \--config *config file*
:   Specify a grid-updates config file. See **CONFIG FILES** section below.

-u *URL*, \--node-url *URL*
:   Specify the gateway node's URL (default: http://127.0.0.1:3456),

-d *directory*, \--node-directory *directory*
:   Specify the node directory (default: *~/.tahoe*),

\--list-uri *URI*
:   Override the default location of the introducers list.

\--news-uri *URI*
:   Override the default location of the NEWS.tgz file.

\--script-uri *URI*
:   Override the default location of script updates.

\--comrepair-uri *URI*
:   Override the default location of the \--community-repair subscription file.

-v
:   Increase verbosity of output.

-V, \--version
:   Display version information.

-h, \--help
:   Print usage information.

CONFIG FILES
============

*grid-updates* will look for configuration files in
$XDG_CONFIG_HOME/grid-updates/config.ini and
$XDG_CONFIG_DIRS/grid-updates/config.ini.

All options must be listed below the section `[OPTIONS]`.

Accepted options are:

tahoe\_node\_dir = *directory*
:    Same as \--node-dir above
tahoe\_node\_url = *URL*
:    Same as \--node-url above
list_uri = *URI*
:    Same as \--list-uri option above
news_uri = *URI*
:    Same as \--news-uri option above
script_uri = *URI*
:    Same as \--script-uri option above
comrepair_uri = *URI*
:    Same as \--comrepair-uri option above

NOTES
=====

*URIs*, in this context, are Tahoe-LAFS directories like, for example
`URI:DIR2-RO:22s6zidugdxaeikq6lakbxbcci:mgrc3nfnygslyqrh7hds22usp6hbn3pulg5bu2puv6y3wpoaaqqq`.

NEWS
====

If you choose to download the news feed, *grid-updates* will place a plain text
version of it in your node's directory and print it to stdout. This is intended
to be sent by cron mail.

There is also an HTML version of the news feed that you can view in a web
browser. You can access it either directly
(http://127.0.0.1:3456/static/NEWS.html) or have it be displayed on your Tahoe
node's web console. You can prepare the console by running `grid-updates
--patch-tahoe` once.

The Atom news feed (http://127.0.0.1:3456/static/NEWS.atom) can be used by
regular feed readers to check for *grid-updates* news.  (Please note, however,
that you cannot "refresh" the feed with regular news readers.  These files have
to always be fetched by *grid-updates* first.)

SHARE HEALTH
============

All *grid-updates* subscriptions reside on the Tahoe grid, which means that
they need to be maintained (renewal of leases, repairs).  Please contribute to
their maintenance by running `--repair-subscriptions` from time to time.

If the script repeatedly fails to retrieve files from the grid, the share may
be damaged and you will have to find a new set of URIs to subscribe to.  One
way to possibly get them is to run `--check-version` to see if there is a new
version of *grid-updates* available.  Newer versions might already include new
default URIs.

INFORMATION FOR SUBSCRIPTION MAINTAINERS
========================================

If you want to offer a *grid-updates* subscription service, you will have to
provide users with URIs to directories that contain the subscription files. The
available subscription types are the news feed (called **NEWS.tgz**), the
introducer list (called **introducers.json.txt**) and the community repair list
of shares (called **community-repair.json.txt**). Please note that
*grid-updates* expects the URIs of directories, not of the files themselves. It
will append the filenames itself.

FILES
=====

* *~/.tahoe/introducers*  
* *~/.tahoe/NEWS*  
* *~/.tahoe/public_html/NEWS.html*  
* *~/.tahoe/public_html/NEWS.atom*  
* *\$XDG_CONFIG_HOME/grid-updates/config* (most commonly ~/.config)  
* *\$XDG_CONFIG_DIRS/grid-updates/config* (most commonly /etc/xdg)  

BUGS
====

Please report bugs in #tahoe-lafs on Irc2p or via email (see below).

SEE ALSO
========

The *grid-updates* Git repositories:

* http://darrob.i2p/grid-updates/  
* http://git.repo.i2p/r/grid-updates.git  
* http://killyourtv.i2p/git/grid-updates.git

The README on the grid:

    URI:DIR2-RO:mjozenx3522pxtqyruekcx7mh4:eaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a/README.html

Information about Tahoe-LAFS for I2P and the I2P grid: http://killyourtv.i2p

LICENSE
=======

*grid-updates* has been released into the public domain. This means that you can
do whatever you please with it.


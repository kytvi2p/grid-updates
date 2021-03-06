% GRID-UPDATES(1) User Commands
% darrob <darrob@mail.i2p>, KillYourTV <killyourtv@mail.i2p>
% September 2012

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

-r, \--repair
:   Maintain the health of Tahoe shares listed in a subscription.

\--patch-tahoe
:   Patch the Tahoe-LAFS web console to display the grid-updates news feed in
    an Iframe.

\--undo-patch-tahoe
:   Remove the grid-updates patch to the Tahoe web console and restore its
    original version.

\--make-news *file*
:   Create a *grid-updates*-compatible NEWS.tgz file from a reStructuredText
    source file.

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

\--format *tar|deb|zip|exe|py2exe*
:   Specify in which format to download the update. Choices are: 'tar' (unix source
	archive), 'deb' (Debian package), 'zip' (Windows source archive),
	'exe' (Windows installer [requires Python]),
	'py2exe' (Windows installer [doesn't require Python]).

\--list-uri *FILE CAP*
:   Override the default location of the introducers list.

\--news-uri *FILE CAP*
:   Override the default location of the NEWS.tgz file.

\--script-uri *DIR CAP*
:   Override the default location of script updates.

\--repairlist-uri *FILE CAP*
:   Override the default location of the \--repair subscription file.

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
list_uri = *FILE CAP*
:    Same as \--list-uri option above
news_uri = *FILE CAP*
:    Same as \--news-uri option above
script_uri = *DIR CAP*
:    Same as \--script-uri option above
comrepair_uri = *FILE CAP*
:    Same as \--comrepair-uri option above

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

INFORMATION FOR SUBSCRIPTION MAINTAINERS
========================================

If you want to offer a *grid-updates* subscription service, you will have to
provide users with the URIs of your subscription files.  They can be either in
the form *DIR CAP/filename* or the the file cap itself.  In the latter case you
must make sure to create mutable files.

For the specific requirements of the JSON lists, please see the included
example files in the share directory.

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

**ERROR: Can't parse JSON list: No JSON object could be decoded**
:   Currently Tahoe doesn't return JSON data if it encounters exceptions (see
    Trac ticket #1799). If you see this **grid-updates** error, you can rerun
    your command in debug mode (`-vvv`) to see Tahoe's actual response.

	This error is most likely to occur during *deep-check* operations. If it
	does, it probably encountered the *NotEnoughSharesError* error, which means
	that a file was unrecoverable. You should investigate the problem using
	Tahoe directly.

**ERROR: Could not run one-check for testfile: HTTP Error 410: Gone**
:   This error is related to the one above but happens during *one-check*
    operations.  If a file is not retrievable (due to not enough remaining
    shares) Tahoe responds with HTTP error 410.

Please report bugs in #tahoe-lafs on Irc2p or via email (see below).


SEE ALSO
========

The *grid-updates* Git repositories:

* http://darrob.i2p/grid-updates/  
* http://git.repo.i2p/r/grid-updates.git  
* http://killyourtv.i2p/git/grid-updates.git

The README on the grid:

    URI:DIR2-RO:hgh5ylzzj6ey4a654ir2yxxblu:hzk3e5rbsefobeqhliytxpycop7ep6qlscmw4wzj5plicg3ilotq/README.html

Information about Tahoe-LAFS for I2P and the I2P grid: http://killyourtv.i2p

LICENSE
=======

*grid-updates* has been released into the public domain. This means that you can
do whatever you please with it.


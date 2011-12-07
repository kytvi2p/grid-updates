Introduction to grid-updates
============================

`grid-updates` is a script intended to help keep Tahoe-LAFS nodes'
configurations up-to-date.

Introducers
-----------

For nodes that support [multiple introducers], it retrieves and installs an
up-to-date list of introducers.

On public grids (especially the one on I2P) all nodes, even introducers, are
run by volunteers and may disappear at any given time.  Maintaining a list of
all known introducers and distributing it to all participants of the grid will
ensure the best possible connectivity for everyone.

News
----

Using grid-updates you can optionally receive a news feed that we intend to use
for important information regarding the grid.

Some volunteers decide to add storage nodes to the grid, but don't configure
them correctly.  Unfortunately, there is currently no way to contact them.
This script is supposed to alleviate that.

Download
========

grid-updates is available from its [git repository] ([git mirror])
or the [Tahoe grid] [^1].

Installation
============

See [INSTALL.md] for information on how to install grid-updates.

Usage
====

Running the script
------------------

`grid-updates` was designed as a cron job script but can be run manually just
as well.

Run this script with either `--merge-introducers` or `--replace-introducers` to
make sure your Tahoe-LAFS node will know about as many introducers as possible.

If you also want to receive news relevant to the grid, add the
`--download-news` action.  It will fetch and display (email if run by a cron
job) a NEWS file from the grid.  This is recommended.

The list is stored on the grid itself and -- like all other shares -- needs
maintenance and repairs [^2].  If you can, please also add the
`--repair-subscriptions` action to your cron job, or run it separately every
once in a while.  This is necessary to keep the service available.

Please refer to the [man page] for detailed usage information.

Example cron job setup
----------------------

     0 0 *   * * grid-updates --merge-introducers --download-news --check-version
    30 0 */2 * * grid-updates --repair-subscriptions

Authors
=======

* darrob [<darrob@mail.i2p>](mailto:darrob@mail.i2p)
* KillYourTV [<killyourtv@mail.i2p>](mailto:killyourtv@mail.i2p)

License
=======

`grid-updates` has been released into the public domain. You may do what you
wish with it.

Support
=======

For Bug reports and support join [#tahoe-lafs] on Irc2P or send an email.

[^1]: The Tahoe URI of the script is
      `URI:DIR2-RO:mjozenx3522pxtqyruekcx7mh4:eaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a`
[^2]: See also the tahoe-repair-all.sh script at
      [killyourtv.i2p](http://killyourtv.i2p/tahoe-lafs/scripts/)

[multiple introducers]: http://killyourtv.i2p/tag/multiple_introducer/ "Info on multiple introducers"
[git repository]: http://git.repo.i2p/w/grid-updates.git "git repository"
[git mirror]: http://killyourtv.i2p/tahoe-lafs/grid-updates/ "Alternative download location"
[Tahoe grid]: http://127.0.0.1:3456/uri/URI%3ADIR2-RO%3Amjozenx3522pxtqyruekcx7mh4%3Aeaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a/ "Tahoe share"
[INSTALL.md]: INSTALL.md
[man page]: man/grid-updates.1.md
[#tahoe-lafs]: irc://irc.postman.i2p/tahoe-lafs "IRC channel"

Introduction to grid-updates
============================

`grid-updates` is a shell script intended to help keep [Tahoe-LAFS] nodes'
configurations up-to-date.  It can retrieve lists of introducers[^1] as well
as news feeds from the Tahoe grid.  This is useful for any public grid that
relies solely on volunteers.

On some public grids (especially the one on I2P) all nodes, even introducers,
are run by volunteers and may disappear at any given time.  Maintaining a list
of all known introducers and distributing it to all participants of the grid
will ensure the best possible connectivity for everyone.

Download
========

grid-updates is available from its [git repository] ([git mirror 1],
[git-mirror 2]) or the [Tahoe grid][^2].

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

If you also want to receive the news feed, add the `--download-news` action.
It will fetch and display (email if run by a cron job) the news feed from the
grid.  It will also allow you to few the news your browser and to be notified
of news by an Atom news feed in a regular feed reader.  This is recommended.

The list, news and script installation files are stored on the grid itself and
-- like all other shares -- need maintenance and repairs[^3].  If you can,
please also add the `--repair-subscriptions` action to your cron job, or run it
separately every once in a while.  This is necessary to keep the service
available.

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

[^1]: You need at least Tahoe version 1.8.3 patched for multiple introducer
	  support. See
	  [killyourtv.i2p](http://killyourtv.i2p/tag/multiple_introducer/).
[^2]: The Tahoe URI of the script is
      `URI:DIR2-RO:mjozenx3522pxtqyruekcx7mh4:eaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a`
[^3]: See also the tahoe-repair-all.sh script at
      [killyourtv.i2p](http://killyourtv.i2p/tahoe-lafs/scripts/)

[Tahoe-LAFS]: http://www.tahoe-lafs.org "The Least-Authority File System"
[git repository]: http://darrob.i2p/grid-updates/grid-updates.git "Git repository"
[git mirror 1]: http://git.repo.i2p/w/grid-updates.git "Git mirror 1"
[git mirror 2]: http://killyourtv.i2p/tahoe-lafs/grid-updates/ "Git mirror 2"
[Tahoe grid]: http://127.0.0.1:3456/uri/URI%3ADIR2-RO%3Amjozenx3522pxtqyruekcx7mh4%3Aeaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a/ "Tahoe share"
[INSTALL.md]: INSTALL.md
[man page]: man/grid-updates.1.md
[#tahoe-lafs]: irc://irc.postman.i2p/tahoe-lafs "IRC channel"

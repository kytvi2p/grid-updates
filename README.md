Introduction
============

`grid-updates.sh` is a script intended to help keep Tahoe-LAFS nodes'
configurations up-to-date.

Introducers
-----------

For nodes that support [multiple introducers][mi], it retrieves and installs an
up-to-date list of introducers.

On public grids (especially the one on I2P) all nodes, even introducers, are
run by volunteers and may disappear at any given time.  Maintaining a list of
all known introducers and distributing it to all participants of the grid will
ensure the best possible connectivity for everyone.

News
----

Using grid-updates.sh you can optionally receive a news feed that we intend to
use for important information regarding the grid.

Some volunteers decide to add storage nodes to the grid, but don't configure
them correctly.  Unfortunately, there is currently no way to contact them.
This script is supposed to alleviate that.

Installation
============

See INSTALL.md for information on how to install grid-updates.

Download
========

grid-updates is available from its [git repository][g] ([mirror][m])
or the Tahoe grid ([URI:DIR2-RO:mjozenx3522pxtqyruekcx7mh4:eaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a][t]).

Authors
=======

* darrob [<darrob@mail.i2p>](mailto:darrob@mail.i2p)
* KillYourTV [<killyourtv@mail.i2p>](killyourtv@mail.i2p)

License
=======

`grid-updates.sh` has been released into the public domain. You may do what you
wish with it.

Support
=======

For Bug reports and support join [#tahoe-lafs][irc] on Irc2P or send an email.

[mi]: http://killyourtv.i2p/tag/multiple_introducer/ "Info on multiple introducers"
[g]: http://git.repo.i2p/w/grid-updates.git "git repository"
[m]: http://killyourtv.i2p/tahoe-lafs/grid-updates/ "Alternative download location"
[t]: http://127.0.0.1:3456/uri/URI%3ADIR2-RO%3Amjozenx3522pxtqyruekcx7mh4%3Aeaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a/ "Tahoe share"
[irc]: irc://irc.postman.i2p/tahoe-lafs "IRC channel"

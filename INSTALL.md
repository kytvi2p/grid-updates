Setup notes for grid-updates
============================

See [README.md] and the [man page] for more information about grid-updates.

Requirements
------------

Bourne-compatible shell, Tahoe-LAFS

Installation
------------

`grid-updates` is a shell script, so you can run it by calling it directly or
adding it to your PATH.

It is probably more conventient to run `make install` which will install the
the script and a man page to your system.

If you run Debian it is advisable to build a deb package instead: `fakeroot
debian/rules binary`. This will build a package that you can install using
`dpkg`. It will include the script and all documentation.

Permissions
-----------

For this script to work, it needs read and write permissions to your Tahoe-LAFS
node's directory (typically `~/.tahoe`).  It will update your introducers file
(if you ask it to) and make a backup of it.  If you also fetch the news file,
the script will write it to `~/.tahoe/NEWS` .


[README.md]: README.md
[man page]: man/grid-updates.1.md

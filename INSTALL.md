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
[[maintenance and repairs|tahoe-repair-all]].  If you can, please also add the
`--repair-subscriptions` action to your cron job, or run it separately every
once in a while.  This is necessary to keep the service available.

Example cron job setup
----------------------

     0 0 *   * * grid-updates --merge-introducers --download-news --check-version
    30 0 */2 * * grid-updates --repair-subscriptions

[README.md]: README.md
[man page]: man/grid-updates.1.md

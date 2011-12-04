Setup notes for grid-updates
============================

See README.md for more information about grid-updates.

Requirements
------------

Bourne-compatible shell, Tahoe-LAFS

Installation
------------

Currently we distribute grid-updates as a simple shell script so all you need
to do is move it to a location in your PATH or add it to your PATH.

You can expect a convenient installation routine using `make` in the very near
future and Debian packages a little further down the line.

Permissions
-----------

For this script to work, it needs read and write permissions to your Tahoe-LAFS
node's directory (typically `~/.tahoe`).  It will update your introducers file
(if you ask it to) and make a backup of it.  If you also fetch the news file,
the script will write it to `~/.tahoe/NEWS` .

Running the script
------------------

grid-updates.sh was designed as a cron job script but can be run manually just
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

     0 0 *   * * grid-updates.sh --merge-introducers --download-news --check-version
    30 0 */2 * * grid-updates.sh --repair-subscriptions

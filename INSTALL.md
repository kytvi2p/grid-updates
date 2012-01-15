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

After you have installed grid-updates, consider running `grid-updates
--patch-tahoe`.  This will apply a small patch to Tahoe-LAFS's web console to
make it display grid-update's news in an Iframe.

Permissions
-----------

For this script to work, it needs read and write permissions to your Tahoe-LAFS
node's directory (typically `~/.tahoe`).  It will update your introducers file
(if you ask it to) and make a backup of it.

If you also fetch the news file, the script will write a plain text version to
`~/.tahoe/NEWS`.  It will also place an HTML version and an Atom news feed into
your Tahoe node's `web.static` directory (typically  `~/.tahoe/public_html`).
You can view NEWS.html and NEWS.atom in your node's [/static] directory, or
(having patched Tahoe's Web UI) right on your node's [front page].


[README.md]: README.md
[man page]: man/grid-updates.1.md
[/static]: http://127.0.0.1:3456/static/
[front page]: http://127.0.0.1:3456

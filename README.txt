Introduction to grid-updates
============================

``grid-updates`` is a Python script intended to help keep `Tahoe-LAFS`_ nodes'
configurations up-to-date. It can retrieve lists of introducers [1]_ as well as
news feeds from the Tahoe grid. This is useful for any public grid that relies
solely on volunteers.

On some public grids (especially the one on I2P) all nodes, even
introducers, are run by volunteers and may disappear at any given time.
Maintaining a list of all known introducers and distributing it to all
participants of the grid will ensure the best possible connectivity for
everyone.

Furthermore, there is no reliable way to contact node operators. This is
why we want to encourage users to subscribe to a news feed relevant to
their Tahoe grid. We hope it's going to be a way to inform unknown node
operators about their wrongly configured nodes, necessary updates,
recommended configuration changes and such.

.. _Tahoe-LAFS:  http://www.tahoe-lafs.org


Download
========

``grid-updates`` can be downloaded from any of the following locations.

-  `Project Eepsite`_
-  Tahoe grid: `URI:DIR2-RO:hgh5ylzzj6ey4a654ir2yxxblu:hzk3e5rbsefobeqhliytxpycop7ep6qlscmw4wzj5plicg3ilotq`_
-  Git

   -  `Git repository`_ (`Gitweb`_)
   -  `Git mirror 1 <http://darrob.i2p/grid-updates/grid-updates.git>`_
   -  `Git mirror 2 <http://killyourtv.i2p/git/grid-updates.git>`_ (`Gitweb 2`_ )

.. _Project Eepsite:  http://killyourtv.i2p/grid-updates/
.. _`URI:DIR2-RO:hgh5ylzzj6ey4a654ir2yxxblu:hzk3e5rbsefobeqhliytxpycop7ep6qlscmw4wzj5plicg3ilotq`: http://127.0.0.1:3456/uri/URI%3ADIR2-RO%3Ahgh5ylzzj6ey4a654ir2yxxblu%3Ahzk3e5rbsefobeqhliytxpycop7ep6qlscmw4wzj5plicg3ilotq/
.. _Git repository:  http://git.repo.i2p/r/grid-updates.git
.. _Gitweb: http://git.repo.i2p/w/grid-updates.git
.. _Gitweb 2: http://killyourtv.i2p/gitweb/?p=grid-updates.git


Installation
============

See `INSTALL.txt`_ for information on how to install
grid-updates.


Usage
=====

Running the script
------------------

``grid-updates`` was designed as a cron job script but can be run
manually just as well.

Run this script with either ``--sync-introducers`` or
``--merge-introducers`` to make sure your Tahoe-LAFS node will know
about as many introducers as possible.

If you also want to receive the news feed, add the ``--download-news``
action. It will fetch and display (email if run by a cron job) the news
feed from the grid. It will also allow you to view the news your browser
(using ``--patch-tahoe`` even in Tahoe's web console) and to be notified
of news by a regular news reader using an Atom news feed. Following the
grid-updates news is recommended.

``--repair`` is another subscription-based service. It will download a list of
shares and check/repair them. This is supposed to make it easier for a
community or group of people to support each other's Tahoe shares.  (The
default subscription includes shares such as the DeepWiki on the I2P grid.)

Please refer to the `man page`_  for detailed usage information.

Example cron job setup
----------------------

 ::

  0  0 *   * * grid-updates --sync-introducers --download-news --check-version
  30 0 */2 * * grid-updates --repair


Authors
=======

-  darrob <darrob@mail.i2p>
-  KillYourTV <killyourtv@mail.i2p>


License
=======

``grid-updates`` has been released into the public domain. You may do
what you wish with it.


Support
=======

For Bug reports and support join
`#tahoe-lafs <irc://irc.postman.i2p/tahoe-lafs>`_ on Irc2P or send an
email.

.. [1]
   You need at least Tahoe version 1.8.3 patched for multiple introducer
   support. See <http://killyourtv.i2p/tag/multiple_introducer/>

.. _man page: man/grid-updates.1.md
.. _INSTALL.txt: INSTALL.txt

#!/usr/bin/env python

from __future__ import print_function
from datetime import datetime
from shutil import copyfile
from uuid import uuid4
import os
import re
import subprocess
import sys
import tarfile
import tempfile # use os.tmpfile()?
# Maybe this is better than try -> except?
if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser
    from urllib import urlencode
    from urllib2 import HTTPError
    from urllib2 import urlopen
    from urllib2 import URLError
else:
    from configparser import ConfigParser as SafeConfigParser
    from urllib.request import urlopen
    from urllib.parse import urlencode
    from urllib.error import HTTPError
    from urllib.error import URLError

from gridupdates.functions import find_datadir
from gridupdates.functions import remove_temporary_dir

class MakeNews(object):
    """This class implements the --make-news function of grid-updates."""

    def __init__(self, verbosity=0):
        self.verbosity = verbosity
        self.tempdir = tempfile.mkdtemp()
        if self.verbosity > 2:
            print('DEBUG: tempdir is: %s' % self.tempdir)
        # check for pandoc and markdown
        # find template locations
        self.datadir = find_datadir()

    def run_action(self, md_file, output_dir):
        """Call this method to execute the desired action (--make-news). It
        will run the necessary methods."""
        copyfile(md_file, os.path.join(self.tempdir, 'NEWS'))
        md_file = os.path.join(self.tempdir, 'NEWS')
        html_file = self.compile_md(md_file)
        if not html_file:
            print('ERROR: Could not compile HTML version.', file=sys.stderr)
        else:
            atom_file = self.compile_atom()
            include_list = [md_file, html_file, atom_file]
            self.make_tarball(include_list, output_dir)
        remove_temporary_dir(self.tempdir, self.verbosity)


    def compile_md(self, mdfile):
        """Compile an HTML version of the Markdown source of NEWS; return the
        file path."""
        source = mdfile
        output_html = os.path.join(self.tempdir, 'NEWS.html')
        pandoc_tmplt = os.path.join(self.datadir, 'pandoc-template.html')
        try:
            subprocess.call(["pandoc",
                            "-w", "html",
                            "-r", "markdown",
                            "--email-obfuscation", "none",
                            "--template", pandoc_tmplt,
                            "--output", output_html,
                            source])
        except OSError as ose:
            print("ERROR: Couldn't run pandoc subprocess: %s" % ose)
        else:
            return output_html

    def compile_atom(self):
        """Create an Atom news feed file from a template by adding the current
        date and an UUID (uuid4 is supposed to be generated randomly); returns
        the file path."""
        atom_tmplt = os.path.join(self.datadir, 'NEWS.atom.template')
        output_atom = os.path.join(self.tempdir, 'NEWS.atom')
        with open(atom_tmplt, 'r') as f:
            formatted = f.read()
        # insert date
        now = datetime.now()
        formatted = re.sub(r'REPLACEDATE', now.isoformat(), formatted)
        # insert UUID
        uuid = str(uuid4())
        formatted = re.sub(r'REPLACEID', uuid, formatted)
        with open(output_atom, 'w') as f:
            f.write(formatted)
        return output_atom

    def make_tarball(self, include_list, output_dir):
        """Add files from a list to NEWS.tgz in --output-dir; remove directory
        structure."""
        tarball = os.path.join(output_dir, 'NEWS.tgz')
        tar = tarfile.open(tarball, mode='w:gz')
        try:
            for item in include_list:
                tarinfo = tar.gettarinfo(item, arcname=os.path.basename(item))
                tarinfo.uid = tarinfo.gid = 0
                tarinfo.uname = tarinfo.gname = "root"
                tar.addfile(tarinfo, open(item, 'rb'))
            if self.verbosity > 0:
                print('Successfully created %s' % tarball)
        finally:
            tar.close()

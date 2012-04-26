from __future__ import print_function
from shutil import copyfile
import os
import re
import sys
import tarfile
import tempfile # use os.tmpfile()?
# Maybe this is better than try -> except?
if sys.version_info[0] == 2:
    from urllib2 import HTTPError
    from urllib2 import urlopen
    from urllib2 import URLError
else:
    from urllib.request import urlopen
    from urllib.error import HTTPError
    from urllib.error import URLError

from gridupdates.functions import remove_temporary_dir

class News(object):
    """This class implements the --download-news function of grid-updates."""

    def __init__(self, tahoe_node_dir, web_static_dir, tahoe_node_url,
                                                    url, verbosity=0):
        self.verbosity = verbosity
        if self.verbosity > 0:
            print("-- Updating NEWS --")
        self.tahoe_node_dir = tahoe_node_dir
        self.web_static = web_static_dir
        self.tahoe_node_url = tahoe_node_url
        if not os.path.exists(web_static_dir):
            os.mkdir(web_static_dir)
        self.url = url
        self.local_news = os.path.join(self.tahoe_node_dir, 'NEWS')
        self.tempdir = tempfile.mkdtemp()
        self.local_archive = os.path.join(self.tempdir, 'NEWS.tgz')

    def run_action(self):
        """Call this method to execute the desired action (--download-news). It
        will run the necessary methods."""
        if self.verbosity > 2:
            print('DEBUG: Selected action: --download-news')
        if not self.download_news():
            return
        if not self.extract_tgz():
            return
        if self.news_differ():
            self.print_news()
        else:
            if self.verbosity > 0:
                print('There are no news.')
        # adjust Atom links to point to the configured node URL
        self.fix_atom_links()
        # Copy in any case to make easily make sure that all versions
        # (escpecially the HTML version) are always present:
        self.install_files()

    def download_news(self):
        """Download NEWS.tgz file to local temporary file."""
        url = self.url + '/NEWS.tgz'
        if self.verbosity > 1:
            print("INFO: Downloading news from the Tahoe grid.")
        if self.verbosity > 2:
            print("INFO: Downloading", url)
        try:
            response = urlopen(url).read()
        except HTTPError:
            print("ERROR: Couldn't find %s." % url, file=sys.stderr)
            return False
        except URLError as urlexc:
            print("ERROR: %s while looking for %s." % (urlexc, url),
                                                    file=sys.stderr)
            return False
        else:
            with open(self.local_archive,'wb') as output:
                output.write(response)
            return True

    def extract_tgz(self):
        """Extract NEWS.tgz archive into temporary directory."""
        if self.verbosity > 2:
            print('DEBUG: Extracting %s to %s.' %
                    (self.local_archive, self.tempdir))
        try:
            tar = tarfile.open(self.local_archive, 'r:gz')
        except tarfile.TarError:
            print('ERROR: Could not extract NEWS.tgz archive.', file=sys.stderr)
            return False
        else:
            for newsfile in ['NEWS', 'NEWS.html', 'NEWS.atom']:
                try:
                    tar.extract(newsfile, self.tempdir)
                except KeyError:
                    print("ERROR: '%s' not found in archive. Cannot continue." %
                            newsfile, file=sys.stderr)
                    return False
            tar.close()
            return True

    def fix_atom_links(self):
        """This methode replaces the placeholder TAHOENODEURL with the actual
        node URL parsed by or passed to grid-updates."""
        atom_file = os.path.join(self.tempdir, 'NEWS.atom')
        with open(atom_file, 'r+') as atom:
            content = atom.read()
            formatted = re.sub(r'TAHOENODEURL', self.tahoe_node_url, content)
            atom.seek(0)
            atom.write(formatted)

    def news_differ(self):
        """Compare the local and newly downloaded NEWS files to determine of
        there are new news. Return True/False."""
        try:
            locnews = open(self.local_news, 'r')
        except IOError:
            if self.verbosity > 2:
                print('DEBUG: No NEWS file found in node directory.')
            differ = True
        else:
            with open(os.path.join(self.tempdir, 'NEWS'), 'r') as tempnews:
                if locnews.read() != tempnews.read():
                    if self.verbosity > 2:
                        print('DEBUG: NEWS files differ.')
                    differ = True
                else:
                    if self.verbosity > 2:
                        print('DEBUG: NEWS files seem to be identical.')
                    differ = False
                locnews.close()
        return differ

    def print_news(self):
        """Print the contents of the newly downloaded NEWS file in the
        temporary directory."""
        with open(os.path.join(self.tempdir, 'NEWS'), 'r') as tempnews:
            for line in tempnews.readlines():
                print('  | ' + line, end='')
            print("The NEWS file (printed above) is located here: %s." %
                    os.path.join(self.tahoe_node_dir, 'NEWS'))

    def install_files(self):
        """Copy extracted NEWS files to their intended locations."""
        try:
            copyfile(os.path.join(self.tempdir, 'NEWS'), self.local_news)
            for newsfile in ['NEWS.html', 'NEWS.atom']:
                copyfile(os.path.join(self.tempdir, newsfile),
                        os.path.join(self.tahoe_node_dir,
                                        self.web_static,
                                        newsfile))
        except (IOError, os.error):
            print("ERROR: Couldn't copy one or more NEWS files into the "
                  "node directory.", file=sys.stderr)
        else:
            if self.verbosity > 2:
                print('DEBUG: Copied NEWS files into the node directory.')
        finally:
            remove_temporary_dir(self.tempdir, self.verbosity)

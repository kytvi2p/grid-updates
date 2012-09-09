from __future__ import print_function
import json
import os
import sys

from gridupdates.functions import tahoe_dl_file
from gridupdates.functions import is_valid_introducer
from gridupdates.functions import subscription_list_is_valid

class Introducers(object):
    """This class implements the introducer list related functions of
    grid-updates."""

    def __init__(self, nodedir, url, verbosity=0):
        self.verbosity = verbosity
        self.nodedir = nodedir
        self.url = url
        if self.verbosity > 0:
            print("-- Updating introducers --")
        self.old_list = []
        self.introducers = os.path.join(self.nodedir, 'introducers')
        self.introducers_bak = self.introducers + '.bak'
        (self.old_introducers, self.old_list) = self.read_existing_list()
        json_response = tahoe_dl_file(self.url, verbosity)
        self.intro_dict = self.create_intro_dict(json_response)

    def run_action(self, mode):
        """Call this method to execute the desired action (--merge-introducers
        or --sync-introducers)."""
        if not self.intro_dict:
            if self.verbosity > 2:
                print('DEBUG: introducer list appears to be empty. Aborting.')
            return
        if mode == 'merge':
            if self.lists_differ():
                if self.expired_intros and self.verbosity > 1:
                    for intro in self.expired_intros:
                        print("INFO: Introducer not in subscription list: %s"
                                                                        % intro)
                if self.new_intros:
                    self.backup_original()
                    self.merge_introducers()
                else:
                    if self.verbosity > 0:
                        print('Introducer list already up-to-date.')
        if mode == 'sync':
            if self.lists_differ():
                self.backup_original()
                self.sync_introducers()

    def create_intro_dict(self, json_response):
        """Compile a dictionary of introducers (uri->name,active) from a JSON
        object."""
        intro_dict = {}
        try:
            new_list = json_response.read().decode('utf8')
        except:
            # TODO specific exception
            print("ERROR: Couldn't read introducer list.",
                    file=sys.stderr)
            return
        if not subscription_list_is_valid(new_list, self.verbosity):
            return
        for uri in json.loads(new_list).keys():
            name = json.loads(new_list)[uri]['name']
            active = json.loads(new_list)[uri]['active']
            if is_valid_introducer(uri):
                if self.verbosity > 2:
                    print('DEBUG: Valid introducer address: %s' % uri)
                intro_dict[uri] = (name, active)
            else:
                if self.verbosity > 0:
                    print("WARN: '%s' is not a valid Tahoe-LAFS introducer "
                            "address. Skipping.")
        return intro_dict

    def read_existing_list(self):
        """Read the local introducers file as a single string (to be written
        again) and as individual lines. """
        if self.verbosity > 2:
            print('DEBUG: Reading the local introducers file.')
        try:
            with open(self.introducers, 'r') as intlist:
                old_introducers = intlist.read()
                old_list = old_introducers.splitlines()
        except IOError as exc:
            print('WARN: Cannot read local introducers files:', exc,
                    file=sys.stderr)
            print('WARN: Are you sure you have a compatible version of '
                    'Tahoe-LAFS?', file=sys.stderr)
            print('WARN: Pretending to have read an empty introducers list.',
                    file=sys.stderr)
            old_introducers = ''
            old_list = []
        return (old_introducers, old_list)

    def backup_original(self):
        """Copy the old introducers file to introducers.bak."""
        try:
            with open(self.introducers_bak, 'w') as intbak:
                intbak.write(self.old_introducers)
        except IOError:
            print('ERROR: Cannot create backup file introducers.bak',
                    file=sys.stderr)
            sys.exit(1)
        else:
            if self.verbosity > 2:
                print('DEBUG: Created backup of local introducers.')

    def lists_differ(self):
        """Compile lists of introducers: all active, locally missing and
        expired."""
        self.subscription_uris = []
        for introducer in list(self.intro_dict.keys()):
            # only include active introducers
            if self.intro_dict[introducer][1]:
                self.subscription_uris.append(introducer)
            else:
                if self.verbosity > 2:
                    print('INFO: Skipping disabled introducer: %s' %
                            self.intro_dict[introducer][0])
        if sorted(self.subscription_uris) == sorted(self.old_list):
            if self.verbosity > 0:
                print('Introducer list already up-to-date.')
            return False
        # Compile lists of new (to be added and outdated (to be removed) #
        # introducers
        self.new_intros = list(set(self.subscription_uris) - set(self.old_list))
        self.expired_intros = list(set(self.old_list) -
                set(self.subscription_uris))
        return True

    def merge_introducers(self):
        """Add newly discovered introducers to the local introducers file;
        remove nothing."""
        try:
            with open(self.introducers, 'a') as intlist:
                for new_intro in self.new_intros:
                    if self.intro_dict[new_intro][1]:
                        if self.verbosity > 0:
                            print('New introducer: %s.' %
                                    self.intro_dict[new_intro][0])
                        intlist.write(new_intro + '\n')
        except IOError as exc:
            print('ERROR: Could not write to introducer file: %s' % exc,
                    file=sys.stderr)
            sys.exit(1)
        else:
            if self.verbosity > 0:
                print('Successfully updated the introducer list.'
                      ' Changes will take effect upon restart of the node.')

    def sync_introducers(self):
        """Add and remove introducers in the local list to make it identical to
        the subscription's."""
        try:
            with open(self.introducers, 'w') as intlist:
                for introducer in self.subscription_uris:
                    intlist.write(introducer + '\n')
        except IOError as exc:
            print('ERROR: Could not write to introducer file: %s' %
                    exc, file=sys.stderr)
            sys.exit(1)
        else:
            if self.verbosity > 0:
                for introducer in self.new_intros:
                    print('Added introducer: %s' %
                            self.intro_dict[introducer][0])
                for introducer in self.expired_intros:
                    if introducer in self.intro_dict:
                        print('Removed introducer: %s' %
                                self.intro_dict[introducer][0])
                    else:
                        print('Removed unknown introducer: %s' % introducer)
                print('Successfully updated the introducer list.'
                      ' Changes will take effect upon restart of the node.')

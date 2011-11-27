#!/bin/sh

# Example (cron) script for a Tahoe-LAFS introducer subscription service

# This script retrieves and installs an up-to-date list of introducers for
# Tahoe-LAFS nodes that support multiple introducers.  See
# http://killyourtv.i2p/tahoe-lafs/ for more information.
#
# Run this script with either --update-merge or --update-replace as a cron job
# to make sure your Tahoe-LAFS node will get the most reliable connection to
# the I2P grid as possible.
#
# The list is stored on the grid itself and -- like all other shares -- needs
# maintenance and repairs.  If you can, please also add a cron job running
# --check-list every once in a while.  This is in everyones interest.

########################################## Configuration #############################################
# Change this to your Tahoe-LAFS node's directory (default: ~/.tahoe).
TAHOE_NODE_DIR="$HOME/.tahoe"

# Location of the subscription list
LISTFURL='URI:DIR2-RO:22s6zidugdxaeikq6lakbxbcci:mgrc3nfnygslyqrh7hds22usp6hbn3pulg5bu2puv6y3wpoaaqqq'
######################################################################################################

print_help () {
cat << EOF
Usage: $0 COMMAND

Commands:
    --update-merge:   Merge your local introducers list with the
                      subscription's
    --update-replace: Replace your local list of introducers with the master
                      list
    --check-list:     Maintain or repair the health of the subscrition
                      service's FURL
    --help:           Print this help text

Errors:
	If the script repeatedly fails to retrieve the list from Tahoe-LAFS,
the share may be damaged.  Try running --check-list which will try to repair
the list.  If that does not help, you will most likely have to find a new FURL
to subscribe to.  Ask in #tahoe-lafs on Irc2P, check the DeepWiki and/or
http://killyourtv.i2p.

EOF
}

if [ $# -ne 1 ]; then
	echo "Error: wrong number of arguments." >&2
	print_help
	exit 1
fi


download_list () {
	tahoe cp "$LISTFURL"/introducers "$TAHOE_NODE_DIR"/introducers.subscription > /dev/null ||
	(echo "Error retrieving the list.  Try again or check the share's integrity.  See \`$0 --help.\`" >&2 ; return 1)
}

replace_list () {
	# Make the local list identical to the subscriber one.
	download_list || return
	if [ -f "$TAHOE_NODE_DIR"/introducers ]; then          # Make backup
		echo "# This is a backup of $TAHOE_NODE_DIR/introducers. It was created by $0 on $(date -u)." > $TAHOE_NODE_DIR/introducers.bak
		cat "$TAHOE_NODE_DIR/introducers" >> "$TAHOE_NODE_DIR/introducers.bak"
	fi
	mv -f "$TAHOE_NODE_DIR"/introducers{.subscription,}    # install list
}

merge_list () {
	# Add new FURLs in the subscribed list to the local list.
	# This resembles I2P's address book's system.
	download_list || return
	[ -f "$TAHOE_NODE_DIR"/introducers ] && cp -f "$TAHOE_NODE_DIR"/introducers{,.bak}  # make backup
	cat $TAHOE_NODE_DIR/introducers{.subscription,.bak} | sort -u > $TAHOE_NODE_DIR/introducers  # merge
	rm $TAHOE_NODE_DIR/introducers.subscription
}

check_list () {
	tahoe deep-check --repair --add-lease "$LISTFURL"
}

case $1 in
	--update-merge)
		merge_list && echo "Success: the list has been retrieved and merged."
	;;
	--update-replace)
		replace_list && echo "Success: the list has been retrieved."
	;;
	--check-list)
		check_list
	;;
	--help)
		print_help
	;;
	*)
		echo "Unknown command."
		print_help
	;;
esac

#!/bin/sh

# Example (cron) script for a Tahoe-LAFS introducer subscription service

# Introduction
# ============
# This script retrieves and installs an up-to-date list of introducers for
# Tahoe-LAFS nodes that support multiple introducers.  See
# http://killyourtv.i2p/tahoe-lafs/ for more information.
#
# Run this script with either --update-merge or --update-replace as a cron job
# to make sure your Tahoe-LAFS node will get the most reliable connection to
# the I2P grid as possible.
#
# The list is stored on the grid itself and -- like all other shares -- needs
# maintenance and repairs.  If you can, please also add the --check-list
# function to your cron job, or run it separately every once in a while.  This
# is in everyone's interest.
#
# If you also want to receive news relevant to the grid, add the --fetch-news
# option.  It will fetch and display a NEWS file from the grid.  This is
# recommended.

# Setup notes
# ===========
# For this script to work, it needs read and write permissions to your
# Tahoe-LAFS node's directory (typically ~/.tahoe).  It will update your
# introdcers file (if you ask it to) and make a backup of it.  If you also
# fetch news, the script will write them to a file called I2PNEWS.

########################################## Configuration #############################################
# Change this to your Tahoe-LAFS node's directory (default: ~/.tahoe).
TAHOE_NODE_DIR="$HOME/.tahoe"

# Location of the subscription list
LISTFURL='URI:DIR2-RO:22s6zidugdxaeikq6lakbxbcci:mgrc3nfnygslyqrh7hds22usp6hbn3pulg5bu2puv6y3wpoaaqqq'
NEWSFURL='URI:DIR2-RO:vi2xzmrimvcyjdoypphdwxqbte:g7lpf2v6vyvl4w5udgpriiawg6ofmbazktvxmspesvkqtmujr2rq'
######################################################################################################

print_help () {
cat << EOF
Usage: $0 OPTION

Options:
    --update-merge:   Merge your local introducers list with the
                      subscription's
    --update-replace: Replace your local list of introducers with the master
                      list
    --check-list:     Maintain or repair the health of the subscription
                      service's FURL
    --fetch-news:     Retrieve news regarding the I2P grid.  These will be
                      stored in $TAHOE_NODE_DIR/I2PNEWS.  If you run this
                      script as a cron job, the news will also be emailed to
                      you.
    --help:           Print this help text

Errors:
	If the script repeatedly fails to retrieve the list from Tahoe-LAFS,
the share may be damaged.  Try running --check-list which will try to repair
the list.  If that does not help, you will most likely have to find a new FURL
to subscribe to.  Ask in #tahoe-lafs on Irc2P, check the DeepWiki and/or
http://killyourtv.i2p.

EOF
}

if [ $# -lt 1 ]; then
	echo "Error: need an option." >&2
	print_help
	exit 1
fi

download_list () {
	TMPLIST=$(mktemp)
	tahoe cp "$LISTFURL"/introducers $TMPLIST > /dev/null ||
	echo "Error retrieving the list.  Try again or check the share's integrity. See \`$0 --help.\`" >&2
}

backup_list () {
	if [ -f "$TAHOE_NODE_DIR"/introducers ]; then # Make backup
		echo "# This is a backup of $TAHOE_NODE_DIR/introducers. It was created by $0 on $(date -u)." > $TAHOE_NODE_DIR/introducers.bak
		cat "$TAHOE_NODE_DIR/introducers" >> "$TAHOE_NODE_DIR/introducers.bak"
	fi
}

merge_list () {
	# Add new FURLs in the subscribed list to the local list.
	# This resembles I2P's address book's system.
	download_list
	backup_list
	cat $TAHOE_NODE_DIR/introducers.bak $TMPLIST \
		| grep -v '^#' | sort -u > $TAHOE_NODE_DIR/introducers  # merge
	#rm $TMPLIST
}

replace_list () {
	# Make the local list identical to the subscribed one.
	download_list
	backup_list
	mv -f $TMPLIST "$TAHOE_NODE_DIR"/introducers    # install list
}

check_list () {
	tahoe deep-check --repair --add-lease "$LISTFURL"
}

fetch_news () {
	TMPNEWS=$(mktemp)
	if tahoe get $NEWSFURL/NEWS $TMPNEWS 2> /dev/null ; then
		if ! diff -N $TAHOE_NODE_DIR/I2PNEWS $TMPNEWS > /dev/null ; then
			cp -f $TMPNEWS $TAHOE_NODE_DIR/I2PNEWS
			echo "There are NEWS!"
			echo "The contents of $TAHOE_NODE_DIR/I2PNEWS follow:"
			cat $TAHOE_NODE_DIR/I2PNEWS
		fi
	else
		echo "Error: couldn't fetch the news file."
		exit 1
	fi
}

opt_merge_list=0
opt_replace_list=0
opt_check_list=0
opt_fetch_news=0
while [ $# -gt 0 ] ; do
	case $1 in
		--update-merge)
			opt_merge_list=1
			shift
		;;
		--update-replace)
			opt_replace_list=1
			shift
		;;
		--check-list)
			opt_check_list=1
			shift
		;;
		--fetch-news)
			opt_fetch_news=1
			shift
		;;
		--help)
			print_help
			exit
		;;
		*)
			echo "Unknown option." >&2
			print_help
			exit 1
		;;
	esac
done

[ $opt_check_list -eq 1 ] && check_list
[ $opt_fetch_news -eq 1 ] && fetch_news
if [ $opt_merge_list -eq 1 ] && [ $opt_replace_list -eq 0 ]; then
	merge_list && echo "Success: the list has been retrieved and merged."
elif [ $opt_merge_list -eq 0 ] && [ $opt_replace_list -eq 1 ]; then
	replace_list && echo "Success: the list has been retrieved."
elif [ $opt_merge_list -eq 1 ] && [ $opt_replace_list -eq 1 ]; then
	echo "Error: --update-merge and --update-replace are mutually exclusive." >&2
	print_help
	exit 1
fi

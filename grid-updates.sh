#!/bin/sh

# Example (cron) script for a Tahoe-LAFS introducer subscription service

# Introduction
# ============
# This script retrieves and installs an up-to-date list of introducers for
# Tahoe-LAFS nodes that support multiple introducers.  See
# http://killyourtv.i2p/tahoe-lafs/ for more information.
#
# Run this script with either --merge-introdcers or --replace-introdcers as a
# cron job to make sure your Tahoe-LAFS node will get the most reliable
# connection to the I2P grid as possible.
#
# The list is stored on the grid itself and -- like all other shares -- needs
# maintenance and repairs.  If you can, please also add the --check-list
# option to your cron job, or run it separately every once in a while.  This
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

############################### Configuration #################################
# Location (directory) of the subscription list:
LISTFURL='URI:DIR2-RO:22s6zidugdxaeikq6lakbxbcci:mgrc3nfnygslyqrh7hds22usp6hbn3pulg5bu2puv6y3wpoaaqqq'
# Location (directory) of the NEWS file:
NEWSFURL='URI:DIR2-RO:vi2xzmrimvcyjdoypphdwxqbte:g7lpf2v6vyvl4w5udgpriiawg6ofmbazktvxmspesvkqtmujr2rq'
###############################################################################


print_help () {
cat << EOF
Usage: $0 OPTION

Options:
    -m, --merge-introducers       Merge your local introducers list with the
                                  subscription's
    -r, --replace-introducers     Replace your local list of introducers with the
                                  master list
    -c, --check-list              Maintain or repair the health of the subscription
                                  service's FURL
    -n, --fetch-news              Retrieve news regarding the I2P grid.  These
                                  will be stored in [node directory]/I2PNEWS.
                                  If you run this script as a cron job, the
                                  news will also be emailed to you.
    -d [directory],               Specify the node directory (default: ~/.tahoe)
    --node-directory [directory]
    -h, --help                    Print this help text

Errors:
    If the script repeatedly fails to retrieve the list from Tahoe-LAFS, the
share may be damaged.  Try running --check-list which will try to repair the
list.  If that does not help, you will most likely have to find a new FURL to
subscribe to.  Ask in #tahoe-lafs on Irc2P, check the DeepWiki and/or
http://killyourtv.i2p.

EOF
}

TAHOE=$(which tahoe)
[ -z $TAHOE ] && echo "Error: tahoe executable not found." >&2 && exit 1

if [ $# -lt 1 ]; then
	echo "Error: need an option." >&2
	print_help
	exit 1
fi

check_permissions () {
	if [ ! -w $TAHOE_NODE_DIR/introducers ]; then
		echo "Error: need write permissions to $TAHOE_NODE_DIR/introducers to be able to update the file." >&2
		exit 1
	fi
}

download_list () {
	TMPLIST=$(mktemp)
	if ! $TAHOE cp "$LISTFURL"/introducers $TMPLIST > /dev/null ; then
		echo "Error retrieving the list.  Try again or check the share's integrity. See \`$0 --help.\`" >&2
		exit 1
	fi
}

backup_list () {
	LISTBAK="$TAHOE_NODE_DIR/introducers.bak"
	if [ ! -w $LISTBAK ] && ! touch $LISTBAK ; then
		echo "Error: need write permissions to $LISTBAK to be able to update the file." >&2
		exit 1
	fi
	echo "# This is a backup of $TAHOE_NODE_DIR/introducers. It was created by $0 on $(date -u)." > $LISTBAK
	cat "$TAHOE_NODE_DIR/introducers" >> $LISTBAK
}

merge_list () {
	# Add new FURLs in the subscribed list to the local list.
	# This resembles I2P's address book's system.
	check_permissions || exit 1
	download_list || exit 1
	backup_list || exit 1
	cat $TAHOE_NODE_DIR/introducers.bak $TMPLIST \
		| grep -v '^#' | sort -u > $TAHOE_NODE_DIR/introducers  # merge
	#rm $TMPLIST
}

replace_list () {
	# Make the local list identical to the subscribed one.
	check_permissions || exit 1
	download_list || exit 1
	backup_list || exit 1
	mv -f $TMPLIST "$TAHOE_NODE_DIR"/introducers    # install list
}

check_list () {
	$TAHOE deep-check --repair --add-lease "$LISTFURL"
}

fetch_news () {
	TMPNEWS=$(mktemp)
	if [ -w $TMPNEWS ]; then
		if $TAHOE get $NEWSFURL/NEWS $TMPNEWS 2> /dev/null ; then
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
	else
		echo "Error: couldn't create temporary news file."
		exit 1
	fi
}

opt_merge_list=0
opt_replace_list=0
opt_check_list=0
opt_fetch_news=0
while [ $# -gt 0 ] ; do
	case $1 in
		--node-directory|-d)
			TAHOE_NODE_DIR=$2
			shift 2
		;;
		--merge-introducers|-m)
			opt_merge_list=1
			shift
		;;
		--replace-introducers|-r)
			opt_replace_list=1
			shift
		;;
		--check-list|-c)
			opt_check_list=1
			shift
		;;
		--fetch-news|-n)
			opt_fetch_news=1
			shift
		;;
		--help|-h)
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


if [ -z $TAHOE_NODE_DIR ]; then
	TAHOE_NODE_DIR="$HOME/.tahoe"
else
	if [ ! -d $TAHOE_NODE_DIR ]; then
		echo "Error: $TAHOE_NODE_DIR does not exist." >&2
		exit 1
	fi
fi
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

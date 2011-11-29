#!/bin/sh

# Example (cron) script for a Tahoe-LAFS introducer subscription service

# Introduction
# ============
# This script retrieves and installs an up-to-date list of introducers for
# Tahoe-LAFS nodes that support multiple introducers.  See
# http://killyourtv.i2p/tahoe-lafs/ for more information.
#
# Run this script with either --merge-introducers or --replace-introducers as a
# cron job to make sure your Tahoe-LAFS node will get the most reliable
# connection to the I2P grid as possible.
#
# The list is stored on the grid itself and -- like all other shares -- needs
# maintenance and repairs.  If you can, please also add the
# --check-subscriptions option to your cron job, or run it separately every
# once in a while.  This is in everyone's interest.
#
# If you also want to receive news relevant to the grid, add the --fetch-news
# option.  It will fetch and display a NEWS file from the grid.  This is
# recommended.

# Setup notes
# ===========
# For this script to work, it needs read and write permissions to your
# Tahoe-LAFS node's directory (typically ~/.tahoe).  It will update your
# introducers file (if you ask it to) and make a backup of it.  If you also
# fetch news, the script will write them to a file called NEWS.

############################### Configuration #################################
# Location (directory) of the subscription list:
DEFAULT_LISTFURL='URI:DIR2-RO:22s6zidugdxaeikq6lakbxbcci:mgrc3nfnygslyqrh7hds22usp6hbn3pulg5bu2puv6y3wpoaaqqq'
# Location (directory) of the NEWS file:
DEFAULT_NEWSFURL='URI:DIR2-RO:vi2xzmrimvcyjdoypphdwxqbte:g7lpf2v6vyvl4w5udgpriiawg6ofmbazktvxmspesvkqtmujr2rq/Latest'
###############################################################################


# Initialize early so that checking for uninitialized variables can be done
if [ -z "$TAHOE_NODE_DIR" ]; then
	TAHOE_NODE_DIR="$HOME/.tahoe"
else
	if [ ! -d "$TAHOE_NODE_DIR" ]; then
		echo "Error: $TAHOE_NODE_DIR does not exist." >&2
		exit 1
	fi
fi
[ -z "$NEWSFURL" ] && NEWSFURL=$DEFAULT_NEWSFURL
[ -z "$LISTFURL" ] && LISTFURL=$DEFAULT_LISTFURL

# abort if any variables aren't initialized to try to prevent any surprises
set -o nounset  # same as set -u
set -e # abort if there are any uncaught errors along the way


print_help () {
cat << EOF
Usage: $0 OPTION

Options:
    -m, --merge-introducers       Merge your local introducers list with the
                                  subscription's
    -r, --replace-introducers     Replace your local list of introducers with the
                                  master list
    -c, --check-subscriptions     Maintain or repair the health of the subscription
                                  service's FURL
    -n, --fetch-news              Retrieve news regarding the I2P grid.  These
                                  will be stored in [node directory]/NEWS.
                                  If you run this script as a cron job, the
                                  news will also be emailed to you.
    -d [directory],               Specify the node directory (default: ~/.tahoe)
    --node-directory [directory]
    --list-furl [FURL]            Overwrite default location of introducers
                                  list
    --news-furl [FURL]            Overwrite default location of news file
    -h, --help                    Print this help text

Errors:
    If the script repeatedly fails to retrieve the list from Tahoe-LAFS, the
    share may be damaged.  Try running --check-subscriptions which will try to
    repair the list.  If that does not help, you will most likely have to find
    a new FURL to subscribe to.  Ask in #tahoe-lafs on Irc2P, check the
    DeepWiki and/or http://killyourtv.i2p.

EOF
}

TAHOE=$(which tahoe)
[ -z "$TAHOE" ] && echo "Error: tahoe executable not found." >&2 && exit 1

if [ $# -lt 1 ]; then
	echo "Error: need an option." >&2
	print_help
	exit 1
fi

check_permissions () {
	if [ -e "$TAHOE_NODE_DIR/introducers" ] && [ ! -w "$TAHOE_NODE_DIR/introducers" ]; then
		echo "Error: need write permissions to $TAHOE_NODE_DIR/introducers to be able to update the file." >&2
		exit 1
	fi
}

download_list () {
	TMPLIST=$(mktemp)
	if ! "$TAHOE" cp "$LISTFURL"/introducers $TMPLIST > /dev/null ; then
		echo "Error retrieving the list.  Try again or check the share's integrity. See \`$0 --help.\`" >&2
		exit 1
	fi
}

backup_list () {
	if [  -e "$TAHOE_NODE_DIR/introducers" ]; then
		LISTBAK="$TAHOE_NODE_DIR/introducers.bak"
		if [ ! -w "$LISTBAK" ] && ! touch "$LISTBAK" ; then
			echo "Error: need write permissions to $LISTBAK to be able to update the file." >&2
			exit 1
		fi
		echo "# This is a backup of $TAHOE_NODE_DIR/introducers. It was created by `basename $0` on $(date -u)." > "$LISTBAK"
		cat "$TAHOE_NODE_DIR/introducers" >> "$LISTBAK"
	fi
}

merge_list () {
	if [ ! -e "$TAHOE_NODE_DIR/introducers" ]; then
		echo "Unable to find $TAHOE_NODE_DIR/introducers. Retrieving a new list."
		replace_list
	else
		# Add new FURLs in the subscribed list to the local list.
		# This resembles I2P's address book's system.
		check_permissions
		download_list
		backup_list
		cat "$TAHOE_NODE_DIR/introducers.bak" "$TMPLIST" \
			| grep '^pb://' | sort -u > "$TAHOE_NODE_DIR/introducers"  # merge
		echo "Success: the list has been retrieved and merged."
		exit 0
		#rm $TMPLIST
	fi
}

replace_list () {
	# Make the local list identical to the subscribed one.
	check_permissions
	download_list
	backup_list
	mv -f "$TMPLIST" "$TAHOE_NODE_DIR/introducers"    # install list
	echo "Success: the list has been retrieved."
}

check_subscriptions () {
	$TAHOE deep-check --repair --add-lease "$LISTFURL"
	$TAHOE deep-check --repair --add-lease "$NEWSFURL"
}

print_news () {
	echo "There are NEWS!"
	diff --ignore-all-space --ignore-blank-lines --new-file "$OLDNEWS" "$TAHOE_NODE_DIR/NEWS" | grep -e "^>\s.\+" | sed 's/^>\s//'
}

fetch_news () {
	TMPNEWS=$(mktemp)
	OLDNEWS=$(mktemp)
	if [ -w "$TMPNEWS" ]; then
		if "$TAHOE" get "$NEWSFURL/NEWS" "$TMPNEWS" 2> /dev/null ; then
			if ! diff -N "$TAHOE_NODE_DIR/NEWS" "$TMPNEWS" > /dev/null ; then
				if [ -e "$TAHOE_NODE_DIR/NEWS" ]; then
					cp -f "$TAHOE_NODE_DIR/NEWS" "$OLDNEWS"
				fi
				cp -f "$TMPNEWS" "$TAHOE_NODE_DIR/NEWS" > /dev/null
				print_news
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
opt_check_subscriptions=0
opt_fetch_news=0
while [ $# -gt 0 ] ; do
	case $1 in
		--node-directory|-d)
			TAHOE_NODE_DIR=$2
			shift 2
		;;
		--list-furl)
			LISTFURL=$2
			shift 2
		;;
		--news-furl)
			NEWSFURL=$2
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
		--check-subscriptions|-c)
			opt_check_subscriptions=1
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

[ $opt_check_subscriptions -eq 1 ] && check_subscriptions
[ $opt_fetch_news -eq 1 ] && fetch_news
if [ $opt_merge_list -eq 1 ] && [ $opt_replace_list -eq 0 ]; then
	merge_list
elif [ $opt_merge_list -eq 0 ] && [ $opt_replace_list -eq 1 ]; then
	replace_list
elif [ $opt_merge_list -eq 1 ] && [ $opt_replace_list -eq 1 ]; then
	echo "Error: --update-merge and --update-replace are mutually exclusive." >&2
	print_help
	exit 1
fi

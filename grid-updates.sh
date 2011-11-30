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
# --check-subscriptions action to your cron job, or run it separately every
# once in a while.  This is in everyone's interest.
#
# If you also want to receive news relevant to the grid, add the --fetch-news
# action.  It will fetch and display a NEWS file from the grid.  This is
# recommended.

# Setup notes
# ===========
# For this script to work, it needs read and write permissions to your
# Tahoe-LAFS node's directory (typically ~/.tahoe).  It will update your
# introducers file (if you ask it to) and make a backup of it.  If you also
# fetch news, the script will write them to a file called NEWS.

############################### Configuration #################################
# Default location (directory) of the subscription list:
LISTFURL='URI:DIR2-RO:22s6zidugdxaeikq6lakbxbcci:mgrc3nfnygslyqrh7hds22usp6hbn3pulg5bu2puv6y3wpoaaqqq'
# Default location (directory) of the NEWS file:
NEWSFURL='URI:DIR2-RO:vi2xzmrimvcyjdoypphdwxqbte:g7lpf2v6vyvl4w5udgpriiawg6ofmbazktvxmspesvkqtmujr2rq/Latest'
# Default location (directory) of script releases:
SCRIPTFURL='URI:DIR2-RO:mjozenx3522pxtqyruekcx7mh4:eaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a'
###############################################################################

VERSION='0.0'

###############################################################################
# Stop multiple instances from running simultaneously
###############################################################################
if [ -w /var/lock ]; then  # the default lock directory in Linux
        LOCKDIR="/var/lock/grid-updates.lck"
else
        LOCKDIR="/tmp/grid-updates.lck"   # but maybe not elsewhere...
fi
PIDFILE="${LOCKDIR}/PID"
ENO_SUCCESS=0;
ENO_GENERAL=1;
ENO_LOCKFAIL=2;
ENO_RECVSIG=3;

#trap 'ECODE=$?; echo "[`basename $0`] Exit: ${ECODE}" >&2' 0

if mkdir "${LOCKDIR}"  > /dev/null 2>&1 ; then
       trap 'ECODE=$?;
       rm -rf "${LOCKDIR}"' 0
       touch $PIDFILE
       echo $$ > "${PIDFILE}"
       trap 'echo "ERROR: Killed by a signal $ECODE $ENO_RECVSIG" >&2
            exit ${ENO_RECVSIG}' 1 2 3 15
else
       # lock failed, check if it's stale
       OTHERPID="$(cat "${PIDFILE}")"

       if [ $? != 0 ]; then
               echo "ERROR: Another instance of `basename $0` is active with PID ${OTHERPID}" >&2
               exit ${ENO_LOCKFAIL}
       fi

       if ! kill -0 ${OTHERPID} >/dev/null 2>&1; then
               #stale lock, removing it and restarting
               [ $opt_verbose ] && echo "INFO: Removing stale PID ${OTHERPID}" >&2
               rm -rf ${LOCKDIR}
               [ $opt_verbose ] && echo "INFO: [`basename $0`] restarting" >&2
               exec "$0" "$@"
       else
               #lock is valid and OTHERPID is active
               echo "ERROR: Another instance of `basename $0` is active with PID ${OTHERPID}" >&2
               exit ${ENO_LOCKFAIL}
       fi
fi

print_help () {
cat << EOF
Usage: $0 ACTION

Actions:
    -m, --merge-introducers     Merge your local introducers list with the
                                subscription's
    -r, --replace-introducers   Replace your local list of introducers with the
                                master list
    -c, --check-subscriptions   Maintain or repair the health of the subscription
                                service's FURL
    -n, --fetch-news            Retrieve news regarding the I2P grid.  These
                                will be stored in [node directory]/NEWS.
                                If you run this script as a cron job, the
                                news will also be emailed to you.
    --check-update              Check for a new version of this script on the
                                grid
    --download-update           Download a new version of this script from the
        [target directory]      grid (implies --check-update)
Options:
    -d [directory],             Specify the node directory (default: ~/.tahoe)
    --node-directory [directory]
    --list-furl [FURL           Overwrite default location of introducers
                                list
    --news-furl [FURL]          Overwrite default location of news file
    --script-furl [FURL]        Overwrite default location of script updates
    -v, --verbose               Display more verbose output
    -V, --version               Display version information
    -h, --help                  Print this help text

Errors:
    If the script repeatedly fails to retrieve the list from Tahoe-LAFS, the
    share may be damaged.  Try running --check-subscriptions which will try to
    repair the list.  If that does not help, you will most likely have to find
    a new FURL to subscribe to.  Ask in #tahoe-lafs on Irc2P, check the
    DeepWiki and/or http://killyourtv.i2p.

EOF
}

TAHOE=$(which tahoe)
[ -z "$TAHOE" ] && echo "ERROR: tahoe executable not found." >&2 && exit 1

check_if_tahoe_node () {
	if [ -d $TAHOE_NODE_DIR ]; then
		if [ ! -e $TAHOE_NODE_DIR/tahoe.cfg ]; then
			echo "WARNING: $TAHOE_NODE_DIR doesn't look like a tahoe node"
		fi
		return 0
	else
		echo "ERROR: $TAHOE_NODE_DIR is not a directory." >&2
		exit 1
	fi
}

if [ -z "$TAHOE_NODE_DIR" ]; then
	TAHOE_NODE_DIR="$HOME/.tahoe"
	check_if_tahoe_node
fi

# abort if any variables aren't initialized to try to prevent any surprises
set -o nounset  # same as set -u
set -e # abort if there are any uncaught errors along the way

check_permissions () {
	if [ -e "$TAHOE_NODE_DIR/introducers" ] && [ ! -w "$TAHOE_NODE_DIR/introducers" ]; then
		echo "ERROR: need write permissions to $TAHOE_NODE_DIR/introducers to be able to update the file." >&2
		exit 1
	fi
}

download_list () {
	[ $opt_verbose ] && echo "INFO: Attempting to download introducers list..."
	TMPLIST=$(mktemp)
	if [ ! -w $TMPLIST ]; then
		echo "Error: could not write to temporary file $TMPLIST."
		exit 1
	fi
	if ! "$TAHOE" get "$LISTFURL"/introducers "$TMPLIST" 2> /dev/null ; then
		echo "ERROR retrieving the list.  Try again or check the share's integrity. See \`$0 --help.\`" >&2
		exit 1
	fi
}

backup_list () {
	if [ -e "$TAHOE_NODE_DIR/introducers" ]; then
		LISTBAK="$TAHOE_NODE_DIR/introducers.bak"
		if [ ! -w "$LISTBAK" ] && ! touch "$LISTBAK" 2> /dev/null ; then
			echo "ERROR: need write permissions to $LISTBAK to be able to update the file." >&2
			exit 1
		fi
		echo "# This is a backup of $TAHOE_NODE_DIR/introducers. It was created by `basename $0` on $(date -u)." > "$LISTBAK"
		cat "$TAHOE_NODE_DIR/introducers" >> "$LISTBAK"
		return 0
	fi
}

merge_list () {
	if [ ! -e "$TAHOE_NODE_DIR/introducers" ]; then
		if [ $opt_verbose ]; then
			echo "INFO: Unable to find $TAHOE_NODE_DIR/introducers. Retrieving a new list."
		fi
		replace_list
		return 0
	else
		# Add new FURLs in the subscribed list to the local list.
		# This resembles I2P's address book's system.
		check_permissions
		download_list
		backup_list
		cat "$TAHOE_NODE_DIR/introducers.bak" "$TMPLIST" \
			| grep '^pb://' | sort -u > "$TAHOE_NODE_DIR/introducers"  # merge
		[ $opt_verbose ] && echo "INFO: Success: the list has been retrieved and merged."
		return 0
		#rm $TMPLIST
	fi
}

replace_list () {
	# Make the local list identical to the subscribed one.
	check_permissions
	download_list
	backup_list
	mv -f "$TMPLIST" "$TAHOE_NODE_DIR/introducers"    # install list
	[ $opt_verbose ] && echo "INFO: Success: the list has been retrieved."
	return 0
}

check_subscriptions () {
	if [ $opt_verbose ]; then
		echo "INFO: Beginning to check subscription shares"
		echo "INFO: 1. Checking subscription share"
		"$TAHOE" deep-check -v --repair --add-lease "$LISTFURL" | \
			while read line ; do echo "$line" | sed 's/^/INFO:\ \ \ \ /'; done
		echo "INFO: 2. Checking NEWS share"
		"$TAHOE" deep-check -v --repair --add-lease "$NEWSFURL" | \
			while read line ; do echo "$line" | sed 's/^/INFO:\ \ \ \ /'; done
		echo "INFO: 3. Checking scripts share"
		"$TAHOE" deep-check -v --repair --add-lease "$SCRIPTFURL" | \
			while read line ; do echo "$line" | sed 's/^/INFO:\ \ \ \ /'; done
		return 0
	else
		"$TAHOE" deep-check --repair --add-lease "$LISTFURL" > /dev/null
		"$TAHOE" deep-check --repair --add-lease "$NEWSFURL" > /dev/null
		"$TAHOE" deep-check --repair --add-lease "$SCRIPTFURL" > /dev/null
		return 0
	fi
}

print_news () {
	# if new NEWS...
	if ! diff -N "$TAHOE_NODE_DIR/NEWS" "$TMPNEWS" > /dev/null ; then
		# move old news aside
		if [ -e "$TAHOE_NODE_DIR/NEWS" ]; then
			cp -f "$TAHOE_NODE_DIR/NEWS" "$OLDNEWS"
		fi
		# put new news into place
		cp -f "$TMPNEWS" "$TAHOE_NODE_DIR/NEWS" > /dev/null
		# print
		diff --ignore-all-space --ignore-blank-lines --new-file \
			"$OLDNEWS" "$TAHOE_NODE_DIR/NEWS" | grep -e "^>\s" | sed 's/^>\s//'
		return 0
	else
		[ $opt_verbose ] && echo "INFO: No new NEWS."
		return 0
	fi
}

fetch_news () {
	TMPNEWS=$(mktemp)
	OLDNEWS=$(mktemp)
	if [ -w "$TMPNEWS" ]; then
		[ $opt_verbose ] && echo "INFO: Attempting to download NEWS file..."
		if "$TAHOE" get "$NEWSFURL/NEWS" "$TMPNEWS" 2> /dev/null ; then
			print_news
			return 0
		else
			echo "ERROR: couldn't fetch the news file." >&2
			exit 1
		fi

	else
		echo "ERROR: couldn't create temporary news file." >&2
		exit 1
	fi
}

check_for_valid_furls () {
	# FURLs will start with URI:. Yes, this is very rudimentary checking,
	# but it's better than nothing...isn't it?

	if [ ! $(echo $NEWSFURL |grep '^URI:') ]; then
		echo "ERROR: $NEWSFURL is not a valid news-furl." >&2
		exit 1
	fi

	if [ ! $(echo $LISTFURL |grep '^URI:') ]; then
		echo "ERROR: $LISTFURL is not a valid list-furl." >&2
		exit 1
	fi

	if [ ! $(echo SCRIPTFURL |grep '^URI:') ]; then
		echo "ERROR: $SCRIPTFURL is not a valid list-furl." >&2
		exit 1
	fi
}

check_update () {
	[ $opt_verbose ] && echo "INFO: Attempting to check for new version."
	LATEST_VERSION_FILENAME=$(tahoe ls $SCRIPTFURL | grep 'grid-updates-v[[:digit:]]\.[[:digit:]].*\.tgz' | sort -rV | head -n 1)
	LATEST_VERSION_NUMBER=$(echo $LATEST_VERSION_FILENAME | sed 's/^grid-updates-v\(.*\)\.tgz$/\1/')
	if [ $VERSION != $LATEST_VERSION_NUMBER ]; then
		[ $opt_verbose ] && echo "INFO: new version available: $LATEST_VERSION_NUMBER."
		return 0
	else
		[ $opt_verbose ] && echo "INFO: no new version available."
		return 1
	fi
}

download_update () {
	if [ ! -w $UPDATE_DOWNLOAD_DIR ]; then
		echo "ERROR: cannot write to download directory $UPDATE_DOWNLOAD_DIR"
		exit 1
	fi

	if [ ! -d $UPDATE_DOWNLOAD_DIR ]; then
		echo "ERROR: $UPDATE_DOWNLOAD_DIR is not a directory."
		exit 1
	fi

	if check_update; then
		[ $opt_verbose ] && echo "INFO: Attempting to download new version..."
		if tahoe get $SCRIPTFURL/$LATEST_VERSION_FILENAME "$UPDATE_DOWNLOAD_DIR/$LATEST_VERSION_FILENAME" 2> /dev/null ; then
			echo "Update found (version $LATEST_VERSION_NUMBER) and downloaded to $UPDATE_DOWNLOAD_DIR/$LATEST_VERSION_FILENAME."
		fi
	fi
}

# some of those variables will not be initialized--and that's OK
# We'll do our own checking from this point forward.
set +u

while [ $# -gt 0 ] ; do
	case $1 in
		--node-directory|-d)
			if [ -z "$2" ]; then
				echo "ERROR: tahoe node directory not specified." >&2
				print_help
				exit 1
			fi
			TAHOE_NODE_DIR=$2
			shift 2
			check_if_tahoe_node
		;;
		--list-furl)
			if [ -z "$2" ]; then
				echo "ERROR: list-furl not specified." >&2
				print_help
				exit 1
			fi
			LISTFURL=$2
			shift 2
			check_for_valid_furls
		;;
		--news-furl)
			if [ -z "$2" ]; then
				echo "ERROR: news-furl not specified." >&2
				print_help
				exit 1
			fi
			NEWSFURL=$2
			shift 2
			check_for_valid_furls
		;;
		--script-furl)
			if [ -z "$2" ]; then
				echo "ERROR: script-furl not specified." >&2
				print_help
				exit 1
			fi
			SCRIPTFURL=$2
			shift 2
			check_for_valid_furls
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
		--version|-V)
			echo "$(basename $0) version: $VERSION"
			exit 0
		;;
		--check-update)
			opt_check_update=1
			shift
		;;
		--download-update)
			if [ -z "$2" ]; then
				echo "ERROR: download directory not specified." >&2
				print_help
				exit 1
			fi
			UPDATE_DOWNLOAD_DIR="$2"
			opt_download_update=1
			shift 2
		;;
		--verbose|-v)
			opt_verbose=1
			shift
		;;
		--help|-h)
			print_help
			exit
		;;
		*)
			echo "ERROR: Unknown command." >&2
			print_help
			exit 1
		;;
	esac
done

if [ ! $opt_merge_list ] && [ ! $opt_replace_list ] && \
[ ! $opt_check_subscriptions ] && [ ! $opt_fetch_news ] && \
[ ! $opt_check_update ] && [ ! $opt_download_update ]; then
	echo "ERROR: An action must be selected." >&2
	print_help
	exit 1
fi

if [ $opt_merge_list ] && [ ! $opt_replace_list ]; then
	merge_list
elif [ ! $opt_merge_list ] && [ $opt_replace_list ]; then
	replace_list
elif [ $opt_merge_list ] && [ $opt_replace_list ]; then
	echo "ERROR: --merge-introducers and --replace-introducers are mutually exclusive." >&2
	print_help
	exit 1
fi
[ $opt_check_subscriptions ] && check_subscriptions
[ $opt_fetch_news ] && fetch_news

if [ $opt_check_subscriptions ] && [ $opt_download_update ]; then
	download_update
elif [ $opt_download_update ]; then
	download_update
elif [ $opt_check_update ]; then
	check_update
fi

exit 0

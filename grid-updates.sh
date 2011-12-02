#!/bin/sh

# grid-updates -- a helper script for a Tahoe-LAFS nodes
#
#
# Authors:
#     darrob <darrob@mail.i2p>
#     KillYourTV <kytv@mail.i2p>
#
# License: public domain
#
# Requirements:
#     Bourne-compatible shell, Tahoe-LAFS

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

# This script's version:
VERSION='0.1'

############################### Configuration #################################
# Default location of the Tahoe-LAFS node:
#TAHOE_NODE_DIR="$HOME/.tahoe"
# Default location (directory) of the subscription list:
LISTURI='URI:DIR2-RO:22s6zidugdxaeikq6lakbxbcci:mgrc3nfnygslyqrh7hds22usp6hbn3pulg5bu2puv6y3wpoaaqqq'
# Default location (directory) of the NEWS file:
NEWSURI='URI:DIR2-RO:vi2xzmrimvcyjdoypphdwxqbte:g7lpf2v6vyvl4w5udgpriiawg6ofmbazktvxmspesvkqtmujr2rq/Latest'
# Default location (directory) of script releases:
SCRIPTURI='URI:DIR2-RO:mjozenx3522pxtqyruekcx7mh4:eaqgy2gfsb73wb4f4z2csbjyoh7imwxn22g4qi332dgcvfyzg73a'
###############################################################################

only_verbose () {
	if [ $OPT_VERBOSE ]; then
		$@
	fi
}

# Stop multiple instances from running simultaneously
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
               only_verbose echo "INFO: Removing stale PID ${OTHERPID}" >&2
               rm -rf ${LOCKDIR} || echo "Cannot remove $LOCKDIR" >&2; exit 1
               only_verbose echo "INFO: [`basename $0`] restarting" >&2
               exec "$0" "$@"
       else
               #lock is valid and OTHERPID is active
               echo "ERROR: Another instance of `basename $0` is active with PID ${OTHERPID}" >&2
               exit ${ENO_LOCKFAIL}
       fi
fi

print_help () {
cat << EOF

Usage: $0 [OPTIONS] [ACTION]

Actions:
    -m, --merge-introducers     Merge your local introducers list with the
                                subscription's
    -r, --replace-introducers   Replace your local list of introducers with the
                                master list
    -c, --check-subscriptions   Maintain or repair the health of the subscription
                                service's URI
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
    --list-uri [URI]            Overwrite default location of introducers
                                list
    --news-uri [URI]            Overwrite default location of news file
    --script-uri [URI]          Overwrite default location of script updates
    -v, --verbose               Display more verbose output
    -V, --version               Display version information
    -h, --help                  Print this help text

Errors:
	If the script repeatedly fails to retrieve a file from the grid, the share
	may be damaged.  Try running --check-subscriptions which will try to repair
	it.  If that doesn't help, you will most likely have to find a new URI to
	subscribe to.  Ask in #tahoe-lafs on Irc2P, check the DeepWiki and/or
	http://killyourtv.i2p.

EOF
}

TAHOE=$(which tahoe)
[ -z "$TAHOE" ] && echo "ERROR: \`tahoe\` executable not found." >&2 && exit 1

check_tahoe_node () {
	if [ -d $TAHOE_NODE_DIR ]; then
		if [ ! -e $TAHOE_NODE_DIR/node.url ]; then
			echo "ERROR: Cannot find $TAHOE_NODE_DIR/node.url. Not a valid tahoe node." >&2
			exit 1
		fi
		return 0
	else
		echo "ERROR: $TAHOE_NODE_DIR is not a directory." >&2
		exit 1
	fi
}

# Abort if any variables aren't initialized to try to prevent any surprises
set -o nounset  # same as set -u
set -e          # abort if there are any uncaught errors along the way

check_permissions () {
	if [ ! -w $TAHOE_NODE_DIR ]; then
		echo "ERROR: Need write permissions to "$TAHOE_NODE_DIR" to be able to update "$1"" >&2
		exit 1
	fi
	if [ -e "$2" ] && [ ! -w "$2" ]; then
		echo "ERROR: Need write permissions to \"$2\" to be able to update "$1"" >&2
		exit 1
	fi
}

pretty_print () {
	while read line ; do echo "$line" | sed 's/^/INFO:\ \ \ \ /'; done
}

download_list () {
	only_verbose echo "INFO: Attempting to download introducers list."
	TMPLIST=$(mktemp $LOCKDIR/grid-update.XXXX)
	if ! "$TAHOE" get "$LISTURI"/introducers "$TMPLIST" 2> /dev/null ; then
		echo "ERROR: Could not retrieve the list. Try again or check the share's integrity. See \`$0 --help.\`" >&2
		exit 1
	fi
}

backup_list () {
	if [ -e "$INTRODUCER_LIST" ]; then
		LISTBAK="$INTRODUCER_LIST.bak"
		if [ ! -w "$LISTBAK" ] && ! touch "$LISTBAK" 2> /dev/null ; then
			echo "ERROR: Need write permissions to $LISTBAK to be able to update the file." >&2
			exit 1
		fi
		echo "# This is a backup of "$INTRODUCER_LIST". It was created by `basename $0` on $(date -u)." > "$LISTBAK"
		cat "$INTRODUCER_LIST" >> "$LISTBAK"
		return 0
	fi
}

merge_list () {
	TMPLIST2=$(mktemp $LOCKDIR/grid-update.XXXX)
	if [ ! -e "$INTRODUCER_LIST" ]; then
		only_verbose echo "INFO: Unable to find "$INTRODUCER_LIST". Retrieving a new list."
		replace_list
		return 0
	else
		# Add new URIs in the subscribed list to the local list.
		# This resembles I2P's address book's system.
		check_permissions "the subscription list" "$INTRODUCER_LIST"
		download_list
		backup_list
		cat "$INTRODUCER_LIST.bak" "$TMPLIST" \
			| grep '^pb://' | sort -u > "$TMPLIST2"
		if diff -N "$TMPLIST2" "$INTRODUCER_LIST" > /dev/null 2>&1 ; then
			only_verbose echo "INFO: No new introducers found."
			return 0
		else
			cat "$INTRODUCER_LIST.bak" "$TMPLIST" \
				| grep '^pb://' | sort -u > "$INTRODUCER_LIST"  # merge
			only_verbose echo "INFO: Success: the list has been retrieved and merged. (Changes will take effect upon restart of the node.)"
		fi

		return 0
		#rm $TMPLIST
	fi
}

replace_list () {
	# Make the local list identical to the subscribed one.
	check_permissions "the subscription list" "$INTRODUCER_LIST"
	download_list
	backup_list
	if diff -N "$LISTBAK" "$INTRODUCER_LIST" > /dev/null 2>&1; then
		mv -f "$TMPLIST" "$INTRODUCER_LIST"    # install list
		only_verbose echo "INFO: Success: the list has been retrieved. (Changes will take effect upon restart of the node.)"
	else
		only_verbose echo "INFO: No updates available."
	fi
	return 0
}

checking_failed ()
{
	echo "ERROR: failed to check $1 share."
	return 1
}

check_subscriptions () {
	check_tahoe_node
	if [ $OPT_VERBOSE ]; then
		echo "INFO: Beginning to check subscription shares."
		echo "INFO: Checking subscription share (1/3)."
		("$TAHOE" deep-check -v --repair --add-lease "$LISTURI" 2>/dev/null >&1 | pretty_print) \
			|| checking_failed "subscriptions"

		echo "INFO: Checking NEWS share (2/3)."
		("$TAHOE" deep-check -v --repair --add-lease "$NEWSURI" 2>/dev/null >&1 | pretty_print) \
			|| checking_failed "news"

		echo "INFO: Checking scripts share (3/3)."
		("$TAHOE" deep-check -v --repair --add-lease "$SCRIPTURI" 2>/dev/null >&1 | pretty_print) \
			|| checking_failed "scripts"
	else
		("$TAHOE" deep-check --repair --add-lease "$LISTURI" > /dev/null 2>&1) \
			|| checking_failed "subscriptions"
		("$TAHOE" deep-check --repair --add-lease "$NEWSURI" > /dev/null 2>&1) \
			|| checking_failed "news"
		("$TAHOE" deep-check --repair --add-lease "$SCRIPTURI" > /dev/null 2>&1) \
			|| checking_failed "scripts"
	fi
}

print_news () {
	# if new NEWS...
	if ! diff -N "$TAHOENEWS" "$TMPNEWS" > /dev/null ; then
		# move old news aside
		if [ -e "$TAHOENEWS" ]; then
			cp -f "$TAHOENEWS" "$OLDNEWS"
		fi
		# put new news into place
		cp -f "$TMPNEWS" "$TAHOENEWS" > /dev/null
		# print
		diff --ignore-all-space --ignore-blank-lines --new-file \
			"$OLDNEWS" "$TAHOENEWS" | grep -e "^>\s" | sed 's/^>\s//'
		return 0
	else
		only_verbose echo "INFO: There are no news."
		return 0
	fi
}

fetch_news () {
	check_permissions "news" "$TAHOENEWS"
	TMPNEWS=$(mktemp $LOCKDIR/grid-update.XXXX)
	OLDNEWS=$(mktemp $LOCKDIR/grid-update.XXXX)
	only_verbose echo "INFO: Attempting to download NEWS file."
	if "$TAHOE" get "$NEWSURI/NEWS" "$TMPNEWS" 2> /dev/null ; then
		print_news
		return 0
	else
		echo "ERROR: Couldn't fetch the NEWS file." >&2
		exit 1
	fi

}

check_for_valid_uris () {
	# URIs will start with URI:. Yes, this is very rudimentary checking,
	# but it's better than nothing...isn't it?

	if [ ! $(echo $NEWSURI |grep '^URI:') ]; then
		echo "ERROR: $NEWSURI is not a valid news-uri." >&2
		exit 1
	fi

	if [ ! $(echo $LISTURI |grep '^URI:') ]; then
		echo "ERROR: $LISTURI is not a valid list-uri." >&2
		exit 1
	fi

	if [ ! $(echo $SCRIPTURI |grep '^URI:') ]; then
		echo "ERROR: $SCRIPTURI is not a valid list-uri." >&2
		exit 1
	fi
}

check_update () {
	only_verbose echo "INFO: Attempting to check for new version."
	LATEST_VERSION_FILENAME=$(tahoe ls $SCRIPTURI | grep 'grid-updates-v[[:digit:]]\.[[:digit:]].*\.tgz' | sort -rV | head -n 1)
	if [ "$LATEST_VERSION_FILENAME" ]; then
		LATEST_VERSION_NUMBER=$(echo $LATEST_VERSION_FILENAME | sed 's/^grid-updates-v\(.*\)\.tgz$/\1/')
		if [ "$VERSION" != "$LATEST_VERSION_NUMBER" ]; then
			# Only print if not called via --download-update
			[ ! $OPT_DOWNLOAD_UPDATE ] && echo "New version available: $LATEST_VERSION_NUMBER."
			return 0
		else
			# Only print if not called via --download-update
			[ ! $OPT_DOWNLOAD_UPDATE ] && echo "No new version available."
			return 1
		fi
	else
		echo "Error: Nothing found. This doesn't seem to be a download location for grid-updates." >&2
	fi
}

download_update () {
	if [ ! -w $UPDATE_DOWNLOAD_DIR ]; then
		echo "ERROR: Cannot write to download directory $UPDATE_DOWNLOAD_DIR."
		exit 1
	fi

	if [ ! -d $UPDATE_DOWNLOAD_DIR ]; then
		echo "ERROR: $UPDATE_DOWNLOAD_DIR is not a directory."
		exit 1
	fi

	if check_update; then
		only_verbose echo "INFO: Attempting to download new version."
		if tahoe get $SCRIPTURI/$LATEST_VERSION_FILENAME "$UPDATE_DOWNLOAD_DIR/$LATEST_VERSION_FILENAME" 2> /dev/null ; then
			echo "Update found (version $LATEST_VERSION_NUMBER) and downloaded to $UPDATE_DOWNLOAD_DIR/$LATEST_VERSION_FILENAME."
		fi
	fi
}

# Useful constants
: ${TAHOE_NODE_DIR:="$HOME/.tahoe"}
INTRODUCER_LIST="$TAHOE_NODE_DIR/introducers"
TAHOENEWS="$TAHOE_NODE_DIR/NEWS"

# some of those variables will not be initialized--and that's OK.
# We'll do our own checking from this point forward.
set +u

while [ $# -gt 0 ] ; do
	case $1 in
		--node-directory|-d)
			if [ -z "$2" ]; then
				echo "ERROR: Tahoe node directory not specified." >&2
				print_help
				exit 1
			fi
			TAHOE_NODE_DIR=$2
			shift 2
			check_tahoe_node
		;;
		--list-uri)
			if [ -z "$2" ]; then
				echo "ERROR: list-uri not specified." >&2
				print_help
				exit 1
			fi
			LISTURI=$2
			shift 2
			check_for_valid_uris
		;;
		--news-uri)
			if [ -z "$2" ]; then
				echo "ERROR: news-uri not specified." >&2
				print_help
				exit 1
			fi
			NEWSURI=$2
			shift 2
			check_for_valid_uris
		;;
		--script-uri)
			if [ -z "$2" ]; then
				echo "ERROR: script-uri not specified." >&2
				print_help
				exit 1
			fi
			SCRIPTURI=$2
			shift 2
			check_for_valid_uris
		;;
		--merge-introducers|-m)
			OPT_MERGE_LIST=1
			shift
		;;
		--replace-introducers|-r)
			OPT_REPLACE_LIST=1
			shift
		;;
		--check-subscriptions|-c)
			OPT_CHECK_SUBSCRIPTIONS=1
			shift
		;;
		--fetch-news|-n)
			OPT_FETCH_NEWS=1
			shift
		;;
		--version|-V)
			echo "$(basename $0) version: $VERSION"
			exit 0
		;;
		--check-update)
			OPT_CHECK_UPDATE=1
			shift
		;;
		--download-update)
			if [ -z "$2" ]; then
				echo "ERROR: Download directory not specified." >&2
				print_help
				exit 1
			fi
			UPDATE_DOWNLOAD_DIR="$2"
			OPT_DOWNLOAD_UPDATE=1
			shift 2
		;;
		--verbose|-v)
			OPT_VERBOSE=1
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

if [ ! $OPT_MERGE_LIST ] && [ ! $OPT_REPLACE_LIST ] && \
[ ! $OPT_CHECK_SUBSCRIPTIONS ] && [ ! $OPT_FETCH_NEWS ] && \
[ ! $OPT_CHECK_UPDATE ] && [ ! $OPT_DOWNLOAD_UPDATE ]; then
	echo "ERROR: You need to specify an action." >&2
	print_help
	exit 1
fi

if [ $OPT_MERGE_LIST ] && [ ! $OPT_REPLACE_LIST ]; then
	merge_list
elif [ ! $OPT_MERGE_LIST ] && [ $OPT_REPLACE_LIST ]; then
	replace_list
elif [ $OPT_MERGE_LIST ] && [ $OPT_REPLACE_LIST ]; then
	echo "ERROR: --merge-introducers and --replace-introducers are mutually exclusive." >&2
	print_help
	exit 1
fi
[ $OPT_CHECK_SUBSCRIPTIONS ] && check_subscriptions
[ $OPT_FETCH_NEWS ] && fetch_news

if [ $OPT_CHECK_SUBSCRIPTIONS ] && [ $OPT_DOWNLOAD_UPDATE ]; then
	download_update
elif [ $OPT_DOWNLOAD_UPDATE ]; then
	download_update
elif [ $OPT_CHECK_UPDATE ]; then
	check_update
fi

exit 0

#!/bin/sh

# This script makes a backup of the original welcome.xhtml and tahoe.css files
# and installs versions that have been used for the use with grid-updates.
# Specifically, the change will display the grid-updates news on your Tahoe
# node's web interface.

TAHOE=$(which tahoe)

find_files () {
	if [ "$TAHOE" = "/usr/bin/tahoe" ]; then
		WELCOME="/usr/share/pyshared/allmydata/web/welcome.xhtml"
		CSS="/usr/share/pyshared/allmydata/web/tahoe.css"
	else
		# This tries to find versions installed by the installer script.
		WELCOME="$(dirname $(which tahoe))/../src/allmydata/web/welcome.xhtml"
		CSS="$(dirname $(which tahoe))/../src/allmydata/web/tahoe.css"
	fi
}

file_profile () {
	FILE="$1"
	if [ "$FILE" = "welcome.xhtml" ]; then
		export FILE_PATH="$WELCOME"
		export PATCH_FILE=welcome.xhtml.patch
		export BACKUP_FILE=${FILE_PATH}.grid-updates.original
		export ORIG_CHECKSUM=c5ffbc368f8142a7f25747d0cc69fee1dede919709f0f27fe9777f67bab74e3e
	elif [ "$FILE" = "tahoe.css" ]; then
		export FILE_PATH="$CSS"
		export PATCH_FILE=tahoe.css.patch
		export BACKUP_FILE=${FILE_PATH}.grid-updates.original
		export ORIG_CHECKSUM=76c58b765a9c1ee589783a56bc238af70bd7ca101b1db7189454970941223996
	else
		echo "ERROR: unknown file name."
		return 1
	fi
		
}

check_file_permissions () {
	if [ -f "$FILE_PATH" ]; then
		if [ ! -w "$FILE_PATH" ]; then
			echo "ERROR: No permission to write to $FILE."
			echo "       You may want run this command as the user who owns the Tahoe-LAFS installation."
			return 1
		else
			echo "$FILE found and writable."
		fi
	else
		echo "Not found: $FILE_PATH."
		return 1
	fi

}

check_if_patchable () {
	# Compare files
	if [ "$(sha256sum $FILE_PATH | cut -d ' ' -f 1)" = "$ORIG_CHECKSUM" ]; then
		echo "$FILE still unpatched (known checksum)."
		# patch
		return 0
	else
		if grep -q "grid-updates" $FILE_PATH ; then
			# Check if patched by g-u.  (It could also differ because
			# of a new version of Tahoe. This shouldn't continue if we
			# don't understand why the file differs.)
			#echo "$FILE has been patched by grid-updates before."
			if [ -f "$BACKUP_FILE" ]; then
				# check if backup exists
				#echo "Backup exists (as expected)"
				if [ "$(sha256sum $BACKUP_FILE | cut -d ' ' -f 1)" = $ORIG_CHECKSUM ]; then
					#echo "Backup matches known checksum (as expected)."
					restore_backup
					return 0
				else
					echo "Unknown checksum. Don't know what to do."
					return 1
				fi
			fi
		else
			echo "ERROR: $FILE looks unexpected. Cannot apply patch."
			return 1
		fi
	fi
}

make_backup () {
	if [ ! -f "$BACKUP_FILE" ]; then
		cp "$FILE_PATH" "$BACKUP_FILE"
	fi
}

restore_backup () {
	if [ -f "$BACKUP_FILE" ]; then
		cp $BACKUP_FILE $FILE_PATH
	else
		echo "ERROR: Couldn't find original backup file $BACKUP_FILE."
		return 1
	fi
}

patch_file () {
	patch "$FILE_PATH" < "$PATCH_FILE"
}


if [ -z $TAHOE ]; then
	echo "ERROR: Tahoe not found"
	exit 1
fi

case $1 in
	"install" )
		find_files
		for FILE in "welcome.xhtml" "tahoe.css" ; do
			echo "--- Patching $FILE ---"
			file_profile $FILE
			check_file_permissions
			check_if_patchable
			make_backup
			patch_file
		done && echo -e "\nSuccess: Patches successfully applied."
		;;
	"restore" )
		find_files
		for FILE in "welcome.xhtml" "tahoe.css" ; do
			echo "--- Restoring $FILE ---"
			file_profile $FILE
			check_file_permissions
			restore_backup
		done && echo -e "\nSuccess: Original Tahoe WebUI files restored." || echo -e "\nERROR: Couldn't restore original WebUI files."
		;;
	* )
		echo "ERROR: Unknown command."
		exit 1
		;;
esac

#!/bin/sh

FILE=NEWS.atom.template
DATE=$(date +%FT%T%:z) # RFC 3339
ID="urn:uuid:$(uuid)"

sed -e "s/REPLACEDATE/$DATE/" -e "s/REPLACEID/$ID/" $FILE

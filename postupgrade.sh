#!/bin/sh

ARGV0=$0 # Zero argument is shell command
ARGV1=$1 # First argument is temp folder during install
ARGV2=$2 # Second argument is Plugin-Name for scipts etc.
ARGV3=$3 # Third argument is Plugin installation folder
ARGV4=$4 # Forth argument is Plugin version
ARGV5=$5 # Fifth argument is Base folder of LoxBerry

echo "<INFO> Copy back existing config files"
cp -v -r /var/tmp/$ARGV3/* $ARGV5/config/plugins/$ARGV3 

echo "<INFO> Remove temporary folders"
rm -rf /var/tmp/$ARGV3

exit 0

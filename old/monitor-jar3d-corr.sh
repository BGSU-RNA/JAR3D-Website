#!/bin/sh

# processCheck.sh
#
# This script is a generic framework for checking for a running process
# and taking some action based on its status.  It is intended to be run
# on a scheduled basis from the crontab of the user who owns/runs the
# process being monitored.  In production use, it is best practice to
# place a renamed and properly modified version of the script into some
# standard location (/usr/local/bin, or the home directory of the user
# under which the process will be running) for each instance where the
# script will be used to monitor a given process

QUEUE_DIR="/var/www/jar3d/bin"

# Definition of the process to be monitored (i.e. httpd, whatever.pl, etc.)
CHK_PROG="align.py"

LOGS="$QUEUE_DIR/align.log"

# Definition of the FQDN of the user to be notified of a process restart
ADM_ADDR="rnabgsu@gmail.com"

# Check for a running instance of the process being monitored
CHK_RESULT=$(/usr/bin/pgrep -f $CHK_PROG)

if [ "$CHK_RESULT" == "" ]; then
   if [[ -e "$LOGS" ]]; then
       date=$(date --rfc-3339='seconds' | tr " " '-')
       old="$QUEUE_DIR/align-$date.log"
       mv "$LOGS" "$old"
   fi

   PYTHONPATH='/var/www/jar3d' python "$QUEUE_DIR/$CHK_PROG" &> "$LOGS" &

   echo "$CHK_PROG restarted" | /bin/mail -s "[rnaprod] $CHK_PROG NOT RUNNING" $ADM_ADDR

fi

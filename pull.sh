#!/bin/sh
HOST='ftp.tammer.com'
USER='tammer'
echo "Password please: "
read PASSWD
echo "BK day please: (number from 1 to 31)"
read day
path="/private/django/django1/pool/backups/$day"
echo "$path"

ftp -i -n $HOST <<END_SCRIPT
quote USER $USER
quote PASS $PASSWD
cd $path
mget *
quit
END_SCRIPT

python3 manage.py mirror
rm User.json
rm Team.json
rm Game.json
rm Pick.json
rm Bank.json
rm Monday.json
#!/usr/bin/env bash

dir=/var/www/jar3d

cd "$dir"
branch="$(git rev-parse --abbrev-ref HEAD)"
git pull origin "$branch"
python JAR3Doutput/manage.py collectstatic --noinput

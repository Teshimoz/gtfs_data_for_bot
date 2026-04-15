#!/bin/bash

REPO=/home/lev/Documents/15minutes/gtfs_server/gtfs_data_for_bot
SRC=/home/lev/Documents/15minutes/gtfs_server/data.csv

cd "$REPO" || exit 1

# copy latest file into repo
cp "$SRC" ./data.csv

# exit if nothing changed
git diff --quiet && exit 0

git add data.csv
git commit -m "auto update $(date +%F)"
git push origin main

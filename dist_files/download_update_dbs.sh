#!/bin/bash

# Use this script to update existing DBs by downloading daily monitoring and activity files from Garmin Connect (https://connect.garmin.com)
echo "Updating existing DBs by downloading from Garmin Connect"

./garmin --all --download --import --analyze --latest


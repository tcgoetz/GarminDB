#!/bin/bash

# Use this script to create new DBs by downloading daily monitoring and activity files from Garmin Connect (https://connect.garmin.com)
echo "Creating new DBs by downloading from Garmin Connect"

./garmin --all --download --import --analyze


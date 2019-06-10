#!/bin/bash

# Use this script to create new DBs by copying daily monitoring and activity files from a USB connected Garmin device
echo "Creating new DBs by copying from a USB mounted Garmin device"

./garmin --all --copy --import --analyze


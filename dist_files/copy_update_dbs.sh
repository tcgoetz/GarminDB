#!/bin/bash

# Use this script to update existing DBs by copying daily monitoring and activity files from a USB connected Garmin device.
echo "Updating existing DBs by copying from a USB mounted Garmin device"

./garmin --all --copy --import --analyze --latest


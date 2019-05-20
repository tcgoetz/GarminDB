#!/usr/bin/env python

#
# copyright Tom Goetz
#

import sys, json, logging, platform, subprocess


class GarminConnectConfigManager(object):
    config_filename = 'GarminConnectConfig.json'

    def __init__(self):
        def parser(entry):
            for (entry_key, entry_value) in entry.iteritems():
                if str(entry_value).endswith('_date'):
                    entry[entry_key] = dateutil.parser.parse(entry_value)
            return entry
        try:
            self.config = json.load(open(self.config_filename), object_hook=parser)
        except Exception as e:
            print str(e)
            print "Missing config: copy GarminConnectConfig.json.example to GarminConnectConfig.json and edit GarminConnectConfig.json to " + \
             "add your Garmin Connect username and password."
            sys.exit(-1)

    def get_secure_password(self):
        system = platform.system()
        if system == 'Darwin':
            password = subprocess.check_output(["security", "find-internet-password", "-s", "sso.garmin.com", "-w"])
            if password:
                return password.rstrip()

    def get_user(self):
        return self.config['credentials']['user']

    def get_password(self):
        password = self.config['credentials']['password']
        if not password:
            password = self.get_secure_password()
        return password

    def latest_activity_count(self):
        return self.config['data']['download_latest_activities']

    def all_activity_count(self):
        return self.config['data']['download_all_activities']

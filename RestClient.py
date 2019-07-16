#
# copyright Tom Goetz
#

import os
import logging
import json


logger = logging.getLogger(__file__)


class RestClient(object):

    agents = {
        'Chrome_Linux'  : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/1337 Safari/537.36',
        'Firefox_MacOS' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0'
    }
    agent = agents['Firefox_MacOS']

    default_headers = {
        'User-Agent'    : agent,
        'Accept'        : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    def __init__(self, session, base_route):
        self.session = session
        self.base_route = base_route

    @classmethod
    def inherit(cls, rest_client, route):
        return RestClient(rest_client.session, '%s/%s' % (rest_client.base_route, route))

    def build_url(self, leaf_route):
        return '%s/%s' % (self.base_route, leaf_route)

    def get(self, leaf_route, aditional_headers={}, params={}):
        total_headers = self.default_headers.copy()
        total_headers.update(aditional_headers)
        response = self.session.get(self.build_url(leaf_route), headers=total_headers, params=params)
        logger.info("get: %s (%d)", response.url, response.status_code)
        return response

    def post(self, leaf_route, aditional_headers, params, data):
        total_headers = self.default_headers.copy()
        total_headers.update(aditional_headers)
        response = self.session.post(self.build_url(leaf_route), headers=total_headers, params=params, data=data)
        logger.info("post: %s (%d)", response.url, response.status_code)
        return response

    def convert_to_json(self, object):
        return object.__str__()

    def save_json_to_file(self, json_full_filename, json_data):
        with open(json_full_filename, 'w') as file:
            logger.info("save_json_to_file: %s", json_full_filename)
            file.write(json.dumps(json_data, default=self.convert_to_json))

    def download_json_file(self, url, params, json_filename, overwite):
        json_full_filname = json_filename + '.json'
        exists = os.path.isfile(json_full_filname)
        if not exists or overwite:
            logger.info("%s %s", 'Overwriting' if exists else 'Downloading', json_filename)
            response = self.get(url, params=params)
            if response.status_code != 200:
                logger.error("GET %s failed (%d): %s", response.url, response.status_code, response.text)
                return False
            self.save_json_to_file(json_full_filname, response.json())
        else:
            logger.info("Ignoring %s (exists)", json_filename)
        return True

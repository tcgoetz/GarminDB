#!/usr/bin/env python

#
# copyright Tom Goetz
#

import os, sys, getopt, re, logging, datetime, time, tempfile, zipfile

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.DEBUG)

class Scrape():

    garmin_connect_base_url = "https://connect.garmin.com"
    garmin_connect_login_url = garmin_connect_base_url + "/en-US/signin"
    garmin_connect_modern_url = garmin_connect_base_url + "/modern"
    garmin_connect_daily_url = garmin_connect_modern_url + "/dailySummary/timeline"
    garmin_connect_daily_user_base_url = garmin_connect_modern_url + "/daily-summary"

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        logger.info("Creating profile: temp_dir= " + self.temp_dir)
        fp = webdriver.FirefoxProfile()
        fp.set_preference("browser.download.folderList", 2)
        fp.set_preference("browser.helperApps.alwaysAsk.force", False)
        fp.set_preference("browser.download.manager.showWhenStarting", False)
        fp.set_preference("browser.download.dir", self.temp_dir)
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-zip-compressed")
        logger.info("Creating driver")
        self.browser = webdriver.Firefox(firefox_profile=fp)

    def load_page(self, url):
        logger.info("load_page: " + url)
        self.browser.switch_to.default_content()
        self.browser.get(url)

    def switch_frame_by_id(self, parent, id):
        logger.info("switch_frame_by_id: " + id)
        frame = parent.find_element_by_id(id)
        self.browser.switch_to.frame(frame)

    def fill_field_by_id(self, parent, id, value):
        logger.info("fill_field_by_id: %s = %s" % (id, value))
        field = parent.find_element_by_id(id)
        field.click()
        field.clear()
        field.send_keys(value)

    def click_by_id(self, parent, id):
        logger.info("click_by_id: " + id)
        submit_button = parent.find_element_by_id(id)
        submit_button.click()

    def dump_children_by_tag(self, element, tag):
        child_elements = element.find_elements_by_tag_name(tag)
        for child_element in child_elements:
            print repr(child_element.get_attribute("class"))

    def wait_for_id(self, driver, time_s, id):
        logger.info("Waiting for: " + id)
        return WebDriverWait(driver, time_s).until(EC.presence_of_element_located((By.ID, id)))

    def __del__(self):
        self.browser.close()

    def get_profile_name(self, url):
        try:
            return re.search('modern/daily-summary/(.+)/\d{4}-\d{2}-\d{2}/timeline', url).group(1)
        except AttributeError:
            raise AttributeError("profile name not found")

    def login(self, username, password):
        self.load_page(self.garmin_connect_login_url)
        self.switch_frame_by_id(self.browser, "gauth-widget-frame-gauth-widget")
        self.fill_field_by_id(self.browser, "username", username)
        self.fill_field_by_id(self.browser, "password", password)
        self.click_by_id(self.browser, "login-btn-signin")

    def save_monitoring(self, parent):
        logger.info("Finding dropdown")
        dropdown = parent.find_element_by_xpath("//*[@class='dropdown page-dropdown']")
        logger.info("clicking button")
        dropdown.click()

        logger.info("Finding button")
        button = dropdown.find_element_by_class_name("btn-export-original")
        logger.info("clicking button")
        button.click()
        time.sleep(10)

    def browse_daily_page(self, profile_name, date):
        logger.info("browse_daily_page: %s %s" % (profile_name, repr(date)))
        daily_url = self.garmin_connect_daily_user_base_url + ("/%s/%s/timeline" % (profile_name, date.strftime("%Y-%m-%d")))
        self.load_page(daily_url)
        page_container = self.wait_for_id(self.browser, 10, "pageContainer")
        self.save_monitoring(page_container)

    def get_monitoring(self, date, days):
        logger.info("get_monitoring: %s : %d" % (str(date), days))
        self.load_page(self.garmin_connect_daily_url)

        page_container = self.wait_for_id(self.browser, 10, "pageContainer")
        daily_user_url = self.browser.current_url
        logger.info("User daily: " + daily_user_url)
        profile_name = self.get_profile_name(daily_user_url)
        logger.info("Profile name: " + profile_name)
        for day in xrange(0, days):
            day_date = date + datetime.timedelta(day)
            self.browse_daily_page(profile_name, day_date)

    def unzip_monitoring(self, outdir):
        logger.info("unzip_monitoring: " + outdir)
        for filename in os.listdir(self.temp_dir):
            monitoring_files_zip = zipfile.ZipFile(self.temp_dir + "/" + filename, 'r')
            monitoring_files_zip.extractall(outdir)
            monitoring_files_zip.close()


def usage(program):
    print '%s -d <date> -n <days> -u <username> -p <password> [-m <outdir>]' % program
    sys.exit()

def main(argv):
    date = None
    days = None
    username = None
    password = None
    monitoring = None

    try:
        opts, args = getopt.getopt(argv,"d:n:m:u:p:", ["date=", "days=", "username=", "password=", "monitoring="])
    except getopt.GetoptError:
        usage(sys.argv[0])

    for opt, arg in opts:
        if opt == '-h':
            usage(sys.argv[0])
        elif opt in ("-d", "--date"):
            logger.debug("Date: " + arg)
            date = datetime.datetime.strptime(arg, "%m/%d/%Y").date()
        elif opt in ("-n", "--days"):
            logger.debug("Days: " + arg)
            days = int(arg)
        elif opt in ("-u", "--username"):
            logger.debug("USername: " + arg)
            username = arg
        elif opt in ("-p", "--password"):
            logger.debug("Password: " + arg)
            password = arg
        elif opt in ("-m", "--monitoring"):
            logger.debug("Monitoring: " + arg)
            monitoring = arg

    if not date or not days or not username or not password or not monitoring:
        print "Missing arguments:"
        usage(sys.argv[0])

    scrape = Scrape()
    scrape.login(username, password)
    if monitoring:
        scrape.get_monitoring(date, days)
        scrape.unzip_monitoring(monitoring)


if __name__ == "__main__":
    main(sys.argv[1:])



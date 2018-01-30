# GarminDB

Python script for parsing health monitoring files into and manipulating data in a Sqlite DB.

* Automatically download and import Garmin monitoring Fit files.
* Extract weight data from Garmin Connect and import it into the DB.
* Import Fitbit daily summary CSV files (files with one summary entry per day).
* Import MS Health daily summary CSV files.
* Import MS Health Vault weight export CSV files.
* Summarizing daily data into a common DB

Once you have your data in the DB, I recoomand using a SQLite browser like [SQLite Studio](http://sqlitestudio.pl) for browsing and working with it.

# Using It

The scripts are automated with Make. The directories where the data files are stored is setup for my use and not genralized. You may need to reconfigure the file and directory paths in the makefile variables.

* `make deps` to install Python dependancies
* Run `make GC_DATE=<date to start scraping monitoring data from> GC_DAYS={number of days of miopnitoring data to download} GC_USER={username} GC_PASSWORD={password} scrape_monitoring` followed by `make import_monitoring` to start exporting your daily monitoring data.
* Keep your Garmin daily monitoring data up to date by running `make GC_USER={username} GC_PASSWORD={password} import_monitoring` which will download monitoring fit files from the day after the last day in the DB and import them.
* Download and import weight data from Garmin Connect by running `make GC_DATE={date to start scraping monitoring data from} GC_DAYS={number of days of miopnitoring data to download} GC_USER={username} GC_PASSWORD={password} scrape_weight`
* Keep you local copy of your weight data up to date by running `make GC_USER={username} GC_PASSWORD={password} scrape_new_weight`.
* Import your FitBit daily CSV files by downloading them and running `make import_fitbit_file`.
* Import your Microsoft Health daily CSV files by downloading them and running `make import_mshealth_file`
* `make backup` to backup your DBs

# GarminDB

Python scripts for parsing health data into and manipulating data in a Sqlite DB.

* Automatically download Garmin daily monitoring files from the user's Garmin Connect "Daily Summary" page. (Currently requires a Firefox brwoser be installed)
* Import Garmin monitoring Fit files into a SQLite DB. 
* Extract weight data from Garmin Connect and import it into the DB. (Currently requires a Firefox brwoser be installed)
* Import Fitbit daily summary CSV files (files with one summary entry per day).
* Import MS Health daily summary CSV files.
* Import MS Health Vault weight export CSV files.
* Summarizing data into a common DB with tables containing daily summaries, weekly summaries, and monthly summaries.

Once you have your data in the DB, I recomend using a SQLite browser like [SQLite Studio](http://sqlitestudio.pl) for browsing and working with it.

# Using It

The scripts are automated with Make. The directories where the data files are stored is setup for my use and not genralized. You may need to reconfigure the file and directory paths in the makefile variables.

* `make deps` to install Python dependancies needed to run the scripts.
* Run `make GC_DATE=<date to start scraping monitoring data from> GC_DAYS={number of days of monitoring data to download} GC_USER={username} GC_PASSWORD={password} scrape_monitoring` followed by `make import_monitoring` to start exporting your daily monitoring data. You need to run this at least once to get some data into your DB. The import command in the next line can't calulate the dates to import until there s data in the DB.
* Keep your Garmin daily monitoring data up to date by running `make GC_USER={username} GC_PASSWORD={password} import_monitoring` which will download monitoring fit files from the day after the last day in the DB and import them.
* Download and import weight data from Garmin Connect by running `make GC_DATE={date to start scraping monitoring data from} GC_DAYS={number of days of monitoring data to download} GC_USER={username} GC_PASSWORD={password} scrape_weight`
* Keep you local copy of your weight data up to date by running `make GC_USER={username} GC_PASSWORD={password} scrape_new_weight`. This command logs into Garmin Connect and navigates tot he weight report, configures the graph for a year of data, and exports it.
* Import your FitBit daily CSV files by downloading them and running `make import_fitbit_file`. I wrote this to get my hsitorical FitBit data into the DB, I do not currently use FitBit and do not plan to do any more work in this area.
* Import your Microsoft Health daily CSV files by downloading them and running `make import_mshealth_file`
* `make backup` to backup your DBs. I wrote this to get my hsitorical MS Health data into the DB, I do not currently use MS Health or a MS Band and do not plan to do any more work in this area.

# Notes

* The scripts were developed on OSX. Information or patches that on using these scripts on other platforms are welcome.

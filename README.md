# GarminDB
Python script for parsing health monitoring files into and manipulating data in a Sqlite DB.

* Garmin monitoring Fit files
* Fitbit daily summary CSV files
* MS Halth daily summary CSV files
* Summarizing daily data into a common DB

Once you have your data in the DB, I recoomand using a SQLite browser like [SQLite Studio](http://sqlitestudio.pl) for browsing and working with it.

# Using It

The scripts are automated with Make. The directories where the data files are stored is setup for my use and not genralized. You may need to reconfigure the file and directory paths in the makefile variables.

* "make deps" to install Python dependancies
* Import your Garmin data by downloading your monitoring Fit files from Garmin Connect and running "make import_monitoring"
* Import your FitBit daily CSV files by downloading them and running "make import_fitbit_file".
* Import your Microsoft Health daily CSV files by downloading them and running "make import_mshealth_file".
* "make backup" to backup your DBs

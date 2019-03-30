[![Screen shot of browsing the DB](https://raw.githubusercontent.com/tcgoetz/GarminDB/master/Screenshots/ScreenShot_browsing_sm.jpg)](https://github.com/tcgoetz/GarminDB/wiki/Screenshots)

# GarminDB

[Python scripts](https://www.python.org/) for parsing health data into and manipulating data in a [SQLite](http://sqlite.org/) DB. SQLite is a light weight DB that requires no server.

What they can do:
* Automatically download and import Garmin daily monitoring files (all day heart rate, activity, climb/decend, stress, and intensity minutes) from the user's Garmin Connect "Daily Summary" page.
* Extract sleep, weight, and resting heart rate data from Garmin Connect and import it into the DB.
* Download and import activity files from Garmin Connect. A summary table for all activities and more detailed data for some activity types. Lap and record entries for activities.
* Import Fitbit daily summary CSV files (files with one summary entry per day).
* Import MS Health daily summary CSV files and MS Health Vault weight export CSV files.
* Summarizing data into a common DB with tables containing daily summaries, weekly summaries, and monthly summaries.
* Retain data as JSON files or FIT files so that the DB can be regenerated without connecting to Garmin.

Once you have your data in the DB, I recomend using a SQLite browser like [SQLite Studio](http://sqlitestudio.pl) for browsing and working with the data.

# Using It

The scripts are automated with [Make](https://www.gnu.org/software/make/manual/make.html). Run the Make commands in a terminal window. You may need to reconfigure the file and directory paths in the makefile variables.

* Git clone GarminDB repo. Get the command from the green button on the project home page.
* Run `make setup` get the scripts ready to process data.
* Run `make GC_DATE=<date to start downloading data from> GC_DAYS={number of days of data to download} GC_USER={username} GC_PASSWORD={password} create_dbs` for your first run.
* Keep all of your local data up to date by running only one command: `make GC_USER={username} GC_PASSWORD={password}`.
* Run `make backup` to backup your DBs.

More [usage](https://github.com/tcgoetz/GarminDB/wiki/Usage)

# Notes

* If you get a DB version exception, the DB schema was updated and you need to rebuild your DBs by running `make GC_USER={username} GC_PASSWORD={password} rebuild_dbs`.
* The scripts were developed on OSX. Information or patches that on using these scripts on other platforms are welcome.
* Running the scripts on Linux should require little or no changes.
* I'm not sure what it would take to run these scripts on Windows. Installing the [Ubuntu subsystem](https://www.howtogeek.com/249966/how-to-install-and-use-the-linux-bash-shell-on-windows-10/) on Windows 10 is one possibility. Using a Linux container is another possibility.
* If you have issues, file a bug here on the project. See the Issues tab at the top of the project page. Run `make bugreport`and include bugreport.txt in your bug report.
* When a run of make `GC_USER={username} GC_PASSWORD={password}` finishes, a summary of the data in the DB will bne printed. The date ranges included in daily monitoring files and activities. It includes the number of records for daily monitoring, activities, sleep, resting heart rate, weight, etc. Use the summary information to determine if all of your data has been downloaded from Garmin Connect. If not, usde the make targets download_monitoring, download_all_activities, download_sleep, download_weight, and download_rhr as needed to download any reamining data.

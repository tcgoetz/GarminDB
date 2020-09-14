[![Screen shot of browsing the DB](https://raw.githubusercontent.com/tcgoetz/GarminDB/master/Screenshots/ScreenShot_browsing_sm.jpg)](https://github.com/tcgoetz/GarminDB/wiki/Screenshots)

[![Screen shot of a daily graph](https://raw.githubusercontent.com/tcgoetz/GarminDB/master/Screenshots/Screen_Shot_daily_graph_sm.jpg)](https://github.com/tcgoetz/GarminDB/wiki/Screenshots)

[![Screen shot of a steps graph](https://raw.githubusercontent.com/tcgoetz/GarminDB/master/Screenshots/Screen_Shot_steps_graph_sm.jpg)](https://github.com/tcgoetz/GarminDB/wiki/Screenshots)

# GarminDB

[Python](https://www.python.org/) scripts for parsing health data into and manipulating data in a [SQLite](http://sqlite.org/) DB. SQLite is a light weight DB that requires no server.

What they can do:
* Automatically download and import Garmin daily monitoring files (all day heart rate, activity, climb/descend, stress, and intensity minutes) from the user's Garmin Connect "Daily Summary" page.
* Extract sleep, weight, and resting heart rate data from Garmin Connect, store it as JSON files, and import it into the DB.
* Download and import activity files from Garmin Connect. A summary table for all activities and more detailed data for some activity types. Lap and record entries for activities.
* Copy daily monitoring and/or activities Fit files from a USB connected Garmin device.
* Import Fitbit daily summary CSV files (files with one summary entry per day).
* Import MS Health daily summary CSV files and MS Health Vault weight export CSV files.
* Summarizing data into `stats.txt` and a common DB with tables containing daily summaries, weekly summaries, and monthly summaries.
* Graph your data.
* Retain data as JSON files or FIT files so that the DB can be regenerated without connecting to Garmin.
* Export activities as TCX files.

Once you have your data in the DB, I recommend using a SQLite browser like [SQLite Studio](http://sqlitestudio.pl) or [DB Browser for SQLite](https://sqlitebrowser.org/) for browsing and working with the data. The scripts create some default [views](http://www.tutorialspoint.com/sqlite/sqlite_views.htm) in the DBs that make browsing the data easier.

# Using It

## Binary Release

Binary releases are available for MacOS. Binary release for other platforms may be added. You can download releases from the [release page](https://github.com/tcgoetz/GarminDB/releases).
For the MacOS binary release:
* Download the zip file and unzip it into a directory where you want to keep it and run it from.
* Follow the directions in the `Readme_MacOS.txt` in the zip file.

## From Source

The scripts are automated with [Make](https://www.gnu.org/software/make/manual/make.html). Run the Make commands in a terminal window.

* Git clone GarminDB repo using the SSH clone method. The submodules require you to use SSH and not HTTPS. Get the command from the green button on the project home page.
* Run `make setup` get the scripts ready to process data.
* Copy `GarminConnectConfig.json.example` to `GarminConnectConfig.json`, edit it, and add your Garmin Connect username and password and adjust the start dates to when your data starts from. [More](https://github.com/tcgoetz/GarminDB/wiki/Config) infomation on the config file.
* Run `make create_dbs` for your first run.
* Keep all of your local data up to date by running only one command: `make`.
* Run `make backup` to backup your DBs.

More [usage](https://github.com/tcgoetz/GarminDB/wiki/Usage)

# Success Stories

Find out who's using GarminDb on what platforms, OSes, and python versions [here](https://github.com/tcgoetz/GarminDB/wiki/Success-Stories). If you're using GarminDB and your scenario isn't listed send me a message or file an issue with your success case.

# Notes

* You may get a DB version exception after updating the code, this means that the DB schema was updated and you need to rebuild your DBs by running `make rebuild_dbs`. Your DBs will be regenerated from the previously downloaded data files. All of your data will not be redownloaded from Garmin.
* The scripts were developed on MacOS. Information or patches on using these scripts on other platforms are welcome.
* Running the scripts on Linux should require little or no changes. You may need to [install](https://github.com/tcgoetz/GarminDB/wiki/Usage) `git` and `make`.
* There are two ways to use this project on Windows. Installing the [Ubuntu subsystem](https://www.howtogeek.com/249966/how-to-install-and-use-the-linux-bash-shell-on-windows-10/) on Windows 10 is one way. Using a Linux container or VM is also possible.
* When a database update finishes, a summary of the data in the DB will be saved to stats.txt. The output includes the date ranges included in the downloaded daily monitoring files and activities. It includes the number of records for daily monitoring, activities, sleep, resting heart rate, weight, etc. Use the summary information to determine if all of your data has been downloaded from Garmin Connect. If not, adjust the dates in GarminConnectConfig.json and runt he download again.
* In `GarminConnectConfig.json` the "steps" element of the "course_views" is list of course ids that per course database views will be generated for. The database view allows you to compare all activities from that course.

# Bugs and Debugging

* If you have issues, file a bug here on the project. See the Issues tab at the top of the project page. Run `make bugreport` or `bugreport.sh` and include bugreport.txt in your bug report.
* Besdies errors that appear on the screen, one of the first places to look for more information is the log files (garmin.log, graphs.log).
* If your having issues with a particular data files, please considering sharing so I can debug it.

# Contributing

Please submit a pull request targeting the develop branch and add your self to the contributors file. Run `make flake8` at the top level and fix all errors before submitting your pull request.

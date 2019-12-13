1. Unzip the GarminDb files and copy them to a directory where you would like to keep them.
2. Open a Terminal.app window and navigate to the directory where you put the GarminDb files.
3. Copy GarminConnectConfig.json.example to GarminConnectConfig.json, edit it, and add your Garmin Connect username and password.
2. Create your databases if you have not used the program previously by doing one of:
    a. Run download_create_dbs.sh to create databases by downloading from the Garmin Connect website.
    b. Run copy_create_dbs.sh to create databases from a USB connected Garmin device.
3.  Update you databases regularly by doing one of:
    a. Run download_update_dbs.sh to download from Garmin Connect
    b. Run copy_update_dbs.sh to copy files from a plugged in Garmin device.

Notes:
* If you are running MacOS 10.15 Catalina, then the GarminDb scripts will be blocked form running and you will have to give permission for them
  to run in System Preferences -> Security & Privacy -> General. After trying to run the script and being blocked, a button will appear in
  that location and you can give the scripts permission to run.

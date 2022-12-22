self: { config, lib, pkgs, ... }:

with lib;
let
  cfg = config.programs.garminDB;
  stats = [ "monitoring" "steps" "itime" "sleep" "rhr" "weight" "activities" ];
  garminDBPackage = self.packages."${pkgs.system}".default;
  credentialsOption = {
    options = {
      user = mkOption {
        type = types.str;
        description = "Username";
      };
      secure_password = mkOption {
        type = types.bool;
        description = "Secure password";
      };
      password = mkOption {
        type = types.str;
        description = "Password";
        default = "";
      };
      password_command = mkOption {
        type = types.str;
        description = "Command to retrieve the password";
      };
    };
  };
  dataOption = {
    options = {
      weight_start_date = mkOption {
        type = types.str;
        description = "The date to start downloading weight data from (mm/dd/YYYY)";
      };
      sleep_start_date = mkOption {
        type = types.str;
        description = "The date to start downloading sleep data from (mm/dd/YYYY)";
      };
      rhr_start_date = mkOption {
        type = types.str;
        description = "The date to start downloading resting heart rate data from (mm/dd/YYYY)";
      };
      monitoring_start_date = mkOption {
        type = types.str;
        description = "The date to start downloading daily monitoring data from (mm/dd/YYYY)";
      };
      download_latest_activities = mkOption {
        type = types.int;
        description = "The number of activities summaries to ask Garmin Connect for when looking for the latest activities. Activities that have no been previously downloaded will be downloaded";
      };
      download_all_activities = mkOption {
        type = types.int;
        description = "The number of activities to summaries to ask for when looking for all activities to download.  Activities that have no been previously downloaded will be downloaded";
      };
    };
  };
  copyOption = {
    options = {
      mount_dir = mkOption {
        type = types.str;
        description = "TODO";
        default = "/Volumes/GARMIN";
      };
    };
  };
  enabledStatsOption = {
    options = {
      monitoring = mkOption {
        type = types.bool;
        description = "Enabled monitoring stat";
        default = true;
      };
      steps = mkOption {
        type = types.bool;
        description = "Enabled steps stat";
        default = true;
      };
      itime = mkOption {
        type = types.bool;
        description = "Enabled itime stat";
        default = true;
      };
      sleep = mkOption {
        type = types.bool;
        description = "Enabled sleep stat";
        default = true;
      };
      rhr = mkOption {
        type = types.bool;
        description = "Enabled rhr stat";
        default = true;
      };
      weight = mkOption {
        type = types.bool;
        description = "Enabled weight stat";
        default = true;
      };
      activities = mkOption {
        type = types.bool;
        description = "Enabled activities stat";
        default = true;
      };
    };
  };
  courseViewsOption = {
    options = {
      steps = mkOption {
        type = types.listOf types.str;
        description = "TODO";
        default = [ ];
      };
    };
  };
  modesOption = {
    options = { };
  };
  activitiesOption = {
    options = {
      display = mkOption {
        type = types.listOf types.str;
        description = "TODO";
        default = [ ];
      };
    };
  };
in
{
  options.programs.garminDB = {
    enable = mkEnableOption "Garming Connect downloader and backuper";
    config.credentials = mkOption {
      type = with types; submodule credentialsOption;
    };
    config.data = mkOption {
      type = with types; submodule dataOption;
    };
    config.copy = mkOption {
      type = with types; submodule copyOption;
    };
    config.enabled_stats = mkOption {
      type = with types; submodule enabledStatsOption;
    };
    config.course_views = mkOption {
      type = with types; submodule courseViewsOption;
    };
    config.modes = mkOption {
      type = with types; submodule modesOption;
    };
    config.activities = mkOption {
      type = with types; submodule activitiesOption;
    };
  };
  config = mkIf cfg.enable {
    home.packages = [ garminDBPackage ];
    home.file.".GarminDb/GarminConnectConfig.json" = {
      text = "${builtins.toJSON cfg.config}";
    };
  };
}


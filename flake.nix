{
  description = "Download and parse data from Garmin Connect or a Garmin watch, FitBit CSV, and MS Health CSV files into and analyze data in Sqlite serverless databases with Jupyter notebooks.";
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    flake-parts.url = "github:hercules-ci/flake-parts";
    pypi-deps-db = {
      url = "github:DavHau/pypi-deps-db";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs@{ self, flake-parts, ... }:
    let
      requirements = (builtins.readFile ./requirements.txt);
      devRequirements = (builtins.readFile ./dev-requirements.txt);
      cleanedRequirements = (builtins.replaceStrings [
        ">=1.4.0"
        ">=1.1.3"
        ">=1.0.4"
        ">=1.0.6"
        "ipyleaflet"
      ] [ "" "" "" "" "" ]
        requirements);
      splitRequirements = (builtins.filter (el: builtins.isString el && el != "") (builtins.split "\n" cleanedRequirements));
    in
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      perSystem = { pkgs, lib, config, system, inputs', ... }:
        let
          fitfile = pkgs.python3Packages.buildPythonPackage rec {
            pname = "fitfile";
            version = "1.1.3";
            src = pkgs.python3Packages.fetchPypi {
              inherit pname version;
              sha256 = "sha256-KfupwZ8KsaxCLEB6e7Zve8HJA9ewmDAKSulNwPaSouE=";
            };
          };
          idbutils = pkgs.python3Packages.buildPythonPackage rec {
            pname = "idbutils";
            version = "1.0.6";
            buildInputs = with pkgs.python3Packages; [ python-dateutil requests sqlalchemy tqdm ];
            propagateBuildInputs = with pkgs.python3Packages; [ python-dateutil requests sqlalchemy tqdm ];
            src = pkgs.python3Packages.fetchPypi {
              inherit pname version;
              sha256 = "sha256-dU5YfJ7ae6v186e9uII/68AkLIsUnd7UvGCB2nKDp6E=";
            };
          };
          tcxfile = pkgs.python3Packages.buildPythonPackage rec {
            pname = "tcxfile";
            version = "1.0.4";
            buildInputs = with pkgs.python3Packages; [ python-dateutil ];
            propagateBuildInputs = with pkgs.python3Packages; [ python-dateutil ];
            src = pkgs.python3Packages.fetchPypi {
              inherit pname version;
              sha256 = "sha256-qJL25YZd32DosOm6RT9nzh0DaXBWpr9muGpJSws6p5M=";
            };
          };
          xyzservices = pkgs.python3Packages.buildPythonPackage rec {
            pname = "xyzservices";
            version = "2022.9.0";
            src = pkgs.python3Packages.fetchPypi {
              inherit pname version;
              sha256 = "sha256-VWUZYXCLmhSEmXizOd92AIyIbfeoMmMIpVSbrlUWJgw=";
            };
            doCheck = false;
          };
          ipyleaflet = pkgs.python3Packages.buildPythonPackage rec {
            pname = "ipyleaflet";
            version = "0.17.2";
            buildInputs = with pkgs.python3Packages; [
              jupyter-packaging
              traittypes
              ipywidgets
              branca
            ] ++ [ xyzservices ];
            propagateBuildInputs = with pkgs.python3Packages; [
              jupyter-packaging
              traittypes
              ipywidgets
              branca
            ] ++ [ xyzservices ];
            src = pkgs.python3Packages.fetchPypi {
              inherit pname version;
              sha256 = "sha256-gRzrShVYmqA0qAckz+W9yTaJVjuIn0ub7T1eO8t2Jrs=";
            };
            doCheck = false;
          };
          garminDB = pkgs.python3Packages.buildPythonPackage {
            name = "garmindb";
            propagatedBuildInputs = with pkgs.python3Packages; [
              python-dateutil
              cloudscraper
              tqdm
              matplotlib
              sqlalchemy
              ipykernel
              cached-property
              traittypes
              ipywidgets
              branca
            ] ++ [ fitfile idbutils tcxfile ipyleaflet xyzservices ];
            src = ./.;
            doCheck = false;
          };
          snakemd = pkgs.python3Packages.buildPythonPackage rec {
            pname = "SnakeMD";
            version = "0.11.0";
            buildInputs = with pkgs.python3Packages; [ ];
            propagateBuildInputs = with pkgs.python3Packages; [ ];
            src = pkgs.python3Packages.fetchPypi {
              inherit pname version;
              sha256 = "sha256-Iou7KtgX6PAdj1OW/eMdSh2+F/WPJtgmAmp9cPSZRZg=";
            };
            doCheck = false;
          };
          shell = pkgs.mkShell {
            name = "garmingDB-shell";
            nativeBuildInputs = [
              garminDB
              pkgs.python3Packages.pandas
              pkgs.python3Packages.jupyterlab
              pkgs.python3Packages.plotly
              pkgs.python3Packages.numpy
              pkgs.python3Packages.scipy
              pkgs.streamlit
              snakemd
            ];
          };
        in
        {
          packages.default = garminDB;
          devShells.default = shell;
        };
      flake = {
        homeManagerModule = import ./nix/hm-module.nix self;
      };
    };
}



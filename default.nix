let
  pkgs = import (fetchTarball
    "https://github.com/NixOS/nixpkgs-channels/archive/99dfb6dce37edcd1db7cb85c2db97089d9d5f442.tar.gz"
  ) {};
  pythonPackages = pkgs.python35Packages;
  python = pkgs.python35;
  jenkinsapi = pythonPackages.buildPythonPackage rec {
    pname = "jenkinsapi";
    version = "0.3.4";
    name = "${pname}-${version}";
    format = "wheel";

    src = pythonPackages.fetchPypi {
      inherit pname version format;
      sha256 = "0xyfalcbz9f92pvf9mi9mv614r87c53rnd4jsw8mkvxnwfr87737";
    };

    propagatedBuildInputs = with pythonPackages; [ pytz requests2 six ];

    meta = {
      description = "A Python API for accessing resources on a Jenkins continuous-integration server";
      homepage = https://github.com/pycontribs/jenkinsapi;
      license = pkgs.stdenv.lib.licenses.mit;
    };
  };
  in pythonPackages.buildPythonApplication {
    name = "myjenkins";
    src = ./.;
    propagatedBuildInputs = [jenkinsapi] ++ (with pythonPackages; [
      click
      pandas
    ]);
    buildInputs = [python] ++ (with pkgs; [
      stdenv
      less
      which
    ]) ++ (with pythonPackages; [
      pytest
      mock
    ]);
    checkPhase = "py.test";
    doCheck = false;
    postShellHook = ''
    '';
  }



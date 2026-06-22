{
  baseInputs,
  defaultSets,
  pkgs,
  pyWorkspace,
  ...
}:
let
  inherit (baseInputs) pyproject-nix;
  inherit (defaultSets.pyEnv) pySet;
  inherit (pkgs.callPackages pyproject-nix.build.util { }) mkApplication;

  # pkg without venv
  tbc-video-export = mkApplication {
    venv = pySet.mkVirtualEnv "tbc-video-export-env" pyWorkspace.deps.default;
    package = pySet.tbc-video-export;
  };
in
{
  packages = {
    inherit tbc-video-export;
    default = tbc-video-export;
  };

  apps = {
    default = {
      type = "app";
      program = tbc-video-export;
    };

    tbc-video-export = {
      type = "app";
      program = tbc-video-export;
    };
  };
}

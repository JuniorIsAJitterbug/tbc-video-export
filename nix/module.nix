{
  flake-parts-lib,
  inputs,
  lib,
  self,
  ...
}:
let
  inherit (inputs) pyproject-build-systems pyproject-nix uv2nix;

  gitShortRev = lib.head (
    lib.splitString "-" self.sourceInfo.shortRev or self.sourceInfo.dirtyShortRev or "unknown"
  );
in
{
  options.perSystem = flake-parts-lib.mkPerSystemOption (
    {
      inputs',
      pkgs,
      ...
    }:
    let
      pyWorkspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ../.; };
      pyOverlay = pyWorkspace.mkPyprojectOverlay { sourcePreference = "wheel"; };
      getDefault = set: lib.findFirst (s: (s ? default) && s.default) null set;

      mkPyEnv =
        {
          pkgSet,
        }:
        {
          inherit pkgSet;
          inherit (pkgSet) default;

          pySet = (pkgs.callPackage pyproject-nix.build.packages { inherit (pkgSet) python; }).overrideScope (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.wheel
              pyOverlay

              (_: prev: {
                tbc-video-export = prev.tbc-video-export.overrideAttrs (_: {
                  # bypass dynamic versioning on nix builds
                  UV_DYNAMIC_VERSIONING_BYPASS = "0.0.0+nix.${gitShortRev}";
                });
              })
            ]
          );
        };
    in
    {
      config =
        let
          defaultSets = {
            pyEnv = getDefault pyEnvs;
            pkgSet = getDefault pkgSets;
            toolSet = getDefault decodeToolSets;
          };

          pkgSets = [
            {
              name = "py314-ff8";
              default = true;
              python = inputs'.uv-python.packages."cpython-3.14";
              ffmpeg = pkgs.ffmpeg_8-headless;
            }
            {
              name = "py310-ff4";
              python = inputs'.uv-python.packages."cpython-3.10";
              ffmpeg = pkgs.ffmpeg_4-headless;
            }
          ];

          decodeToolSets = [
            {
              name = "legacy-tools";
              default = true;
              package = inputs'.jitterbug.packages.vhs-decode-legacy;
            }
            {
              name = "ld-decode-tools";
              package = inputs'.jitterbug.packages.ld-decode-tools;
            }
            {
              name = "tbc-tools";
              package = inputs'.jitterbug.packages.tbc-tools;
            }
          ];

          pyEnvs = map (pkgSet: { inherit (pkgSet) name; } // mkPyEnv { inherit pkgSet; }) pkgSets;

          toolSettings =
            let
              pyProjectSettings = (fromTOML (builtins.readFile ../pyproject.toml)).tool.nix;
            in
            {
              yamlfmt = toString ((pkgs.formats.yaml { }).generate "yamlfmt.toml" pyProjectSettings.yamlfmt);
              pinact = toString ((pkgs.formats.yaml { }).generate "pinact.toml" pyProjectSettings.pinact);
            };
        in
        {
          _module.args = {
            inherit
              defaultSets
              decodeToolSets
              pyEnvs
              pyWorkspace
              toolSettings
              ;

            baseInputs = inputs;
          };
        };
    }
  );
}

{
  decodeToolSets,
  lib,
  pkgs,
  pyEnvs,
  ...
}:
let
  # create pytest for a given pkgset
  mkPyTests =
    {
      pkgSet,
    }:
    pyEnvName:
    (final: prev: {
      tbc-video-export = prev.tbc-video-export.overrideAttrs (prevAttrs: {
        passthru = (prevAttrs.passthru or { }) // {
          # create test for every toolset
          tests =
            (prevAttrs.tests or { })
            // lib.listToAttrs (
              map (
                toolSet:
                let
                  testName = "pytest-${toolSet.name}-${pyEnvName}";
                in
                {
                  name = testName;
                  value = pkgs.stdenv.mkDerivation {
                    inherit (final.tbc-video-export) src;

                    name = "${final.tbc-video-export.name}-${testName}";
                    dontConfigure = true;

                    nativeBuildInputs = [
                      (final.mkVirtualEnv "tbc-video-export-${testName}-env" { tbc-video-export = [ "test" ]; })
                      pkgSet.ffmpeg
                      toolSet.package
                    ];

                    buildPhase = ''
                      runHook preBuild
                      pytest
                      mkdir -p $out/tests/${testName}
                      runHook postBuild
                    '';
                  };
                }
              ) decodeToolSets
            );
        };
      });
    });
in
{
  # create checks for all pytest variants
  checks = lib.mergeAttrsList (
    map (
      pyEnv:
      (pyEnv.pySet.overrideScope (
        lib.composeManyExtensions [
          (mkPyTests {
            inherit (pyEnv) pkgSet;
          } pyEnv.name)
        ]
      )).tbc-video-export.passthru.tests
    ) pyEnvs
  );
}

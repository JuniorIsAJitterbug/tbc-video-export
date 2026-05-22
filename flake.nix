{
  description = "tbc-video-export dev flake";

  outputs =
    {
      flake-parts,
      devenv,
      jitterbug,
      ...
    }@inputs:
    flake-parts.lib.mkFlake
      {
        inherit inputs;
      }
      {
        imports = [
          devenv.flakeModule
        ];

        systems = [
          "x86_64-linux"
          "aarch64-linux"
          "x86_64-darwin"
          "aarch64-darwin"
        ];

        perSystem =
          {
            pkgs,
            system,
            ...
          }:
          {
            devenv.shells = {
              default = {
                name = "tbc-video-export";
                packages = with pkgs; [
                  mediainfo
                  libmediainfo
                  openssl
                  ruff
                  ffmpeg_4
                  jitterbug.packages.${system}.vhs-decode-legacy
                ];

                languages.python = {
                  enable = true;
                  version = "3.10";

                  poetry = {
                    enable = true;
                    activate.enable = true;
                    package = pkgs.poetry.withPlugins (ps: [
                      pkgs.python3Packages.poetry-dynamic-versioning
                    ]);

                    install = {
                      enable = true;
                      allGroups = true;
                      allExtras = true;
                    };
                  };
                };

                git-hooks.hooks = {
                  ruff.enable = true;
                  pyright.enable = true;
                };
              };
            };
          };
      };

  nixConfig = {
    extra-trusted-public-keys = [
      "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw="
      "nixpkgs-python.cachix.org-1:hxjI7pFxTyuTHn2NkvWCrAUcNZLNS3ZAvfYNuYifcEU="
      "jitterbug.cachix.org-1:6GrV9s/TKZ07JuCWvHETRnt4yvuXayO8gYiM2o9mSVw="
    ];
    extra-substituters = [
      "https://devenv.cachix.org"
      "https://nixpkgs-python.cachix.org"
      "https://jitterbug.cachix.org"
    ];
  };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    devenv.url = "github:cachix/devenv";
    nixpkgs-python.url = "github:cachix/nixpkgs-python";
    jitterbug.url = "github:JuniorIsAJitterbug/nur-packages";
  };
}

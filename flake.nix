{
  description = "tbc-video-export dev flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv.url = "github:cachix/devenv";
    nixpkgs-python.url = "github:cachix/nixpkgs-python";
    jitterbug.url = "github:JuniorIsAJitterbug/nur-packages";
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

  outputs = inputs@{ flake-parts, nixpkgs, jitterbug, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.devenv.flakeModule
      ];

      systems = [ "x86_64-linux" ];

      perSystem = { config, self', inputs', pkgs, lib, system, ... }:
        let
          commonPackages = with pkgs; [
            mediainfo
            libmediainfo
            openssl
            ruff
            ffmpeg_4
            inputs.jitterbug.packages.${pkgs.system}.vhs-decode
          ];
        in
        {
          devenv.shells = {
            default = {
              name = "tbc-video-export";
              packages = commonPackages;

              languages.python = {
                enable = true;
                version = "3.10";

                poetry = {
                  enable = true;
                  activate.enable = true;
                  install = {
                    enable = true;
                    allExtras = true;
                  };
                };
              };

              pre-commit.hooks = {
                ruff.enable = true;
                pyright.enable = true;
              };
            };
          };
        };
    };
}

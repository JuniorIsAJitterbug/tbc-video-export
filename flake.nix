{
  description = "tbc-video-export dev flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
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

      perSystem = { config, self', inputs', pkgs, system, ... }: {
        devenv.shells = {
          default = {
            name = "tbc-video-export";

            packages = with pkgs; [
              ruff
              mediainfo
              inputs.jitterbug.packages.${pkgs.system}.vhs-decode
              inputs.jitterbug.packages.${pkgs.system}.ab-av1
            ];

            languages.python = {
              enable = true;
              version = "3.10";

              poetry = {
                enable = true;
                activate.enable = true;
                install.enable = true;
                install.allExtras = true;
              };
            };

            pre-commit.hooks = {
              ruff.enable = true;
              pyright.enable = true;

              yamllint = {
                enable = true;
                settings.preset = "relaxed";
              };
            };
          };

          ci = {
            name = "tbc-video-export (CI)";

            packages = with pkgs;[
              ruff
              mediainfo
            ];

            languages.python = {
              enable = true;
              version = "3.10";

              poetry = {
                enable = true;
                activate.enable = true;
                install.enable = true;
                install.allExtras = true;
              };
            };
          };
        };
      };
    };
}

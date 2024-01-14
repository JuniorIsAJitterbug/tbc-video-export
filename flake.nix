{
  description = "tbc-video-export dev flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
    devenv.url = "github:cachix/devenv";
    jitterbug.url = "github:JuniorIsAJitterbug/nur-packages";
  };

  nixConfig = {
    extra-trusted-public-keys = "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=";
    extra-substituters = "https://devenv.cachix.org";
  };

  outputs = inputs@{ flake-parts, nixpkgs, jitterbug, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.devenv.flakeModule
      ];
      systems = [ "x86_64-linux" ];

      perSystem = { config, self', inputs', pkgs, system, ... }:
        let
          python-packages = p:
            with p; [
              pip
            ];
        in
        {
          devenv.shells.default = {
            name = "tbc-video-export";

            imports = [ ];

            packages = with pkgs;
              [
                stdenv.cc.cc.lib
                ruff
                jitterbug.packages.${pkgs.system}.vhs-decode
                (python310.withPackages python-packages)
              ];

            languages.python = {
              enable = true;
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
            };

            pre-commit.settings = {
              yamllint.relaxed = true;
            };
          };

        };
      flake = { };
    };
}

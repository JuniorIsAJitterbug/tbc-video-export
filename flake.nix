{
  description = "tbc-video-export dev flake";

  outputs =
    {
      flake-parts,
      git-hooks,
      ...
    }@inputs:
    flake-parts.lib.mkFlake
      {
        inherit inputs;
      }
      {
        imports = [
          git-hooks.flakeModule
          ./nix/module.nix
        ];

        systems = [
          "x86_64-linux"
          "aarch64-linux"
          "x86_64-darwin"
          "aarch64-darwin"
        ];

        perSystem = _: {
          imports = [
            ./nix/checks.nix
            ./nix/dev-shells.nix
            ./nix/git-hooks.nix
            ./nix/packages.nix
          ];
        };
      };

  nixConfig = {
    extra-trusted-public-keys = [
      "jitterbug.cachix.org-1:6GrV9s/TKZ07JuCWvHETRnt4yvuXayO8gYiM2o9mSVw="
    ];

    extra-substituters = [
      "https://jitterbug.cachix.org"
    ];
  };

  inputs = {
    nixpkgs = {
      url = "github:NixOS/nixpkgs/nixos-unstable";
    };

    jitterbug = {
      url = "github:JuniorIsAJitterbug/nur-packages";
    };

    flake-parts = {
      url = "github:hercules-ci/flake-parts";
      inputs = {
        nixpkgs-lib.follows = "nixpkgs";
      };
    };

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
      };
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        pyproject-nix.follows = "pyproject-nix";
      };
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        pyproject-nix.follows = "pyproject-nix";
        uv2nix.follows = "uv2nix";
      };
    };

    uv-python = {
      url = "github:pyproject-nix/uv-python.nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
      };
    };

    git-hooks = {
      url = "github:cachix/git-hooks.nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
      };
    };
  };
}

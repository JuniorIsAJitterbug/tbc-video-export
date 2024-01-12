{
  description = "tbc-video-export dev flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    jitterbug.url = "github:JuniorIsAJitterbug/nur-packages";
  };

  outputs =
    { self
    , nixpkgs
    , flake-utils
    , jitterbug
    }:

    flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs { inherit system; };
      pythonPackages = ps: with ps; [
        coverage
      ];
    in
    {
      devShells.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          pre-commit
          stdenv.cc.cc.libgcc
        ];
        nativeBuildInputs = [ pkgs.autoPatchelfHook ];

        enterShell = ''
          pre-commit install

          # oddly the python pre-commit hook doesn't actually install things during install
          # here's a hack to force ruff into the pre-commit cache (works but is not great)
          pre-commit run

          # pre-commits output is a bit verbose when it succeeds, choose your own output wrangling
          patch=$(autoPatchelf ~/.cache/pre-commit/)
          if [[ $? -ne 0 ]]; then
            echo "$patch"
            exit 1
          else
            echo "patched ~/.cache/pre-commit"
          fi
        '';

        packages = with pkgs;
          [
            (python310.withPackages pythonPackages)
            poetry
            pre-commit
            ruff

            jitterbug.packages.${pkgs.system}.vhs-decode
          ];
      };
    });
}

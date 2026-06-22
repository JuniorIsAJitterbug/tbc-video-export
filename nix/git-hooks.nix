{
  config,
  defaultSets,
  lib,
  pkgs,
  toolSettings,
  ...
}:
let
  inherit (defaultSets.pyEnv) pySet;

  venv = pySet.mkVirtualEnv "tbc-video-export-lint-env" { tbc-video-export = [ "test" ]; };

  mkHookFilter =
    idPrefix:
    builtins.concatStringsSep " " (
      builtins.attrNames (
        lib.filterAttrs (n: _v: (lib.hasPrefix "custom-${idPrefix}-" n)) config.pre-commit.settings.hooks
      )
    );
in
{
  pre-commit = {
    check.enable = false; # would fail due to offline/sandbox

    settings = {
      package = pkgs.prek;

      excludes = [
        "tests/files"
      ];

      default_stages = [ "manual" ]; # use .#format & .#lint

      hooks =
        let
          mkHook =
            name: package: extraAttrs:
            {
              inherit name package;
              enable = true;
              entry = lib.getExe package;
            }
            // extraAttrs;

          mkFormatterHook = name: extraAttrs: mkHook "format-${name}" pkgs.${name} extraAttrs;
          mkLinterHook = name: extraAttrs: mkHook "linter-${name}" pkgs.${name} extraAttrs;
        in
        {
          # formatters
          ## nix
          custom-formatter-deadnix = mkFormatterHook "deadnix" {
            priority = 0;
            types = [ "nix" ];
            args = [
              "--edit"
            ];
          };

          custom-formatter-statix = mkFormatterHook "statix" {
            priority = 1;
            pass_filenames = false;
            types = [ "nix" ];
            args = [ "fix" ];
          };

          custom-formatter-nixfmt-rs = mkFormatterHook "nixfmt" {
            priority = 2;
            types = [ "nix" ];
          };

          ## python
          custom-formatter-ruff = mkFormatterHook "ruff" {
            types = [ "python" ];
            args = [ "format" ];
          };

          ## toml
          custom-formatter-tombi = mkFormatterHook "tombi" {
            types = [ "toml" ];
            args = [ "format" ];
          };

          ## markdown
          custom-formatter-rumdl = mkFormatterHook "rumdl" {
            types = [ "markdown" ];
            args = [ "fmt" ];
          };

          ## yaml
          custom-formatter-yamlfmt = mkFormatterHook "yamlfmt" {
            types = [ "yaml" ];
            args = [
              "-conf"
              toolSettings.yamlfmt
            ];
          };

          # linters
          ## nix
          custom-linter-deadnix = mkLinterHook "deadnix" {
            types = [ "nix" ];
            args = [
              "--fail"
            ];
          };

          custom-linter-statix = mkLinterHook "statix" {
            types = [ "nix" ];
            pass_filenames = false;
            args = [ "check" ];
          };

          custom-linter-nixfmt-rs = mkLinterHook "nixfmt" {
            types = [ "nix" ];
            args = [ "--check" ];
          };

          ## python
          custom-linter-pyrefly = mkLinterHook "pyrefly" {
            types = [ "python" ];
            args = [
              "check"
              "--python-interpreter-path"
              "${venv}/bin/python"
            ];
          };

          custom-linter-ruff = mkLinterHook "ruff" {
            types = [ "python" ];
            args = [ "check" ];
          };

          ## toml
          custom-linter-tombi = mkLinterHook "tombi" {
            types = [ "toml" ];
            args = [
              "lint"
            ];
          };

          ## markdown
          custom-linter-rumdl = mkLinterHook "rumdl" {
            types = [ "markdown" ];
            args = [
              "fmt"
              "--check"
            ];
          };

          ## yaml
          custom-linter-yamlfmt = mkLinterHook "yamlfmt" {
            types = [ "yaml" ];
            args = [
              "-lint"
              "-conf"
              toolSettings.yamlfmt
            ];
          };

          ## github actions
          custom-linter-pinact = mkLinterHook "pinact" {
            types = [ "yaml" ];
            files = "^.github/workflows/";
            args = [
              "run"
              "--check"
              "--verify"
              "--verify-min-age"
              "--verify-comment"
              "--config"
              toolSettings.pinact
            ];
          };

          custom-linter-zizmor = mkLinterHook "zizmor" {
            types = [ "yaml" ];
            files = "^.github/workflows/";
          };

          ## misc
          custom-linter-typos = mkLinterHook "typos" {
            types = [ "text" ];
          };
        };
    };
  };

  # all hooks are set to manual and should be run via
  # nix run .#format and nix run .#lint
  apps = {
    format = {
      type = "app";
      program = "${pkgs.writeShellScript "tbc-video-export-apps-format" ''
        set -euo pipefail
        ${config.pre-commit.shellHook}
        ${lib.getExe pkgs.prek} run --all-files --stage manual ${mkHookFilter "formatter"}
      ''}";
    };

    lint = {
      type = "app";
      program = "${pkgs.writeShellScript "tbc-video-export-apps-lint" ''
        set -euo pipefail
        ${config.pre-commit.shellHook}
        ${lib.getExe pkgs.prek} run --all-files --stage manual ${mkHookFilter "linter"}
      ''}";
    };
  };
}
